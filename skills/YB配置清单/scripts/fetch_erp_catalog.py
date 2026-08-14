#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置清单 skill · ERP §6 按需切片拉取器（查询型 fetcher）

在 Stage E 由 agent 调用：给定业务线（--line，生涯/科创）、目标空间（--space）
或显式查询参数（--category-id / --classification-id / --name），
向 ERP §6 发起定向切片查询，自带分页循环，做脏数据过滤，用薄映射层
product-mapping.json 的 tag_routing 把 ERP `tags` 派生为 skill 需要的
source_spaces / function_tags / product_role，并生成本次运行的快照
（含 SHA-256 指纹）——快照即本次"固定资源"。

--keywords 提供客户端多信号收窄：按 产品名 + function_tags + source_spaces
+ 小类名 + 分组名 任一命中保留（ERP 服务端 name 参数只搜 name+tags，
小类/分组锚点由客户端补足）。

依赖：仅 Python 标准库。
产物：
  <out-dir>/<run-id>/snapshot.json          归一化产品集（skill 消费的字段契约）
  <out-dir>/<run-id>/snapshot.sha256        snapshot.json 的 SHA-256
  <out-dir>/<run-id>/manifest.json          查询清单 + 关键词过滤 + 各快照指纹 + 映射层指纹

agent 后续把 snapshot.json 当作"标准产品库"使用：设备行通过 product_key(=product_no)
100% 可追溯至该快照与 ERP 原记录。
"""
import argparse
import hashlib
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

# token 解析优先级：--token-file > 环境变量 ERP_API_TOKEN > 同级/ assets/erp_apikey.txt
PROD_BASE = os.environ.get("ERP_API_BASE", "https://erpapi.yishengya.cn/api")
PRICE_MAP = {"market_price": "default_unit_price",
             "channel_price": "default_agent_price",
             "cost_price": "default_cost_price"}
MODEL_RE = re.compile(r"(?:[A-Za-z].*\d|\d.*[A-Za-z])|V\d|FH\d|LLXLYPT|[-_][A-Z0-9]{2,}")
GARBAGE_NAMES = {"dfadfdaf", "and/", "test", "测试", "asdf", "xxx", "/"}
GARBAGE_BRANDS = {"/", "一批", "无", "-", ""}
CJK_RE = re.compile(r"[一-鿿]")


def load_token(path=None):
    """解析 ERP API token，按优先级：
    1) 显式 --token-file 文件；2) 环境变量 ERP_API_TOKEN；
    3) 脚本同级或 assets/erp_apikey.txt；4) 仍无则报错退出。"""
    if path:
        raw = open(path, encoding="utf-8").read().strip()
    elif os.environ.get("ERP_API_TOKEN"):
        raw = os.environ["ERP_API_TOKEN"].strip()
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        for cand in (os.path.join(here, "erp_apikey.txt"),
                     os.path.join(here, "..", "assets", "erp_apikey.txt")):
            if os.path.exists(cand):
                raw = open(cand, encoding="utf-8").read().strip()
                break
        else:
            raise SystemExit(
                "✗ 未找到 ERP token：请传 --token-file <文件>，或设置环境变量 "
                "ERP_API_TOKEN，或在 assets/ 放置 erp_apikey.txt")
    return raw[7:] if raw.startswith("Bearer ") else raw


def api_get(path, params, token):
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(
        f"{PROD_BASE}/{path}?{qs}",
        headers={"accept": "application/json", "authorization": "Bearer " + token},
    )
    return json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8"))


def split_tag(tag):
    return [t.strip() for t in re.split(r"[,，、;；]", tag) if t.strip()]


def is_modelish(t):
    return bool(MODEL_RE.search(t)) or (bool(re.search(r"[A-Za-z]", t)) and bool(re.search(r"\d", t)))


def is_garbage_name(name):
    if not name:
        return True
    n = name.strip()
    if n.lower() in GARBAGE_NAMES:
        return True
    if n in ("/",):
        return True
    # 纯拉丁小写且无汉字、长度过短 → 多为测试数据
    if not CJK_RE.search(n) and len(n) < 4:
        return True
    return False


def classify_tags(tags, mapping):
    space_suffixes = mapping["tag_routing"]["space_suffixes"]
    brands = set(mapping["tag_routing"]["brand_dictionary"])
    spaces, funcs = [], []
    for raw in tags:
        for t in split_tag(raw):
            if not t:
                continue
            if any(t.endswith(s) for s in space_suffixes):
                if t not in spaces:
                    spaces.append(t)
            elif t in brands or is_modelish(t):
                continue  # 品牌/型号噪声，排除
            else:
                if t not in funcs:
                    funcs.append(t)
    return spaces, funcs


def derive_semantics(product, mapping):
    tags = product.get("tags") or []
    spaces, funcs = classify_tags(tags, mapping)
    if not spaces and not funcs:
        # 回退：按 category_id 推论语义
        fb = mapping.get("category_fallback", {}).get(str(product.get("category_id")))
        if fb:
            spaces = fb.get("source_spaces", []) or []
            funcs = fb.get("function_tags", []) or []
    # product_role 推断
    role = None
    pid = (product.get("category") or {}).get("parent_id")
    role_map = mapping.get("role_map", {})
    if pid is not None and str(pid) in role_map:
        role = role_map[str(pid)]
    # product_intro：ERP 无专用字段，取非空者
    intro = product.get("specifications") or product.get("remark") or product.get("product_advantages") or ""
    intro = intro.strip()
    return spaces, funcs, role, intro


def normalize(product, mapping, matched_by):
    spaces, funcs, role, intro = derive_semantics(product, mapping)
    price = {}
    for sk, ek in PRICE_MAP.items():
        v = product.get(ek)
        price[sk] = v if isinstance(v, (int, float)) else None
    # 图片：引用 ERP image_url（远程，不下载）
    image_refs = []
    raw_imgs = product.get("image_url") or []
    if isinstance(raw_imgs, str):
        try:
            raw_imgs = json.loads(raw_imgs)
        except Exception:
            raw_imgs = []
    for im in (raw_imgs or []):
        url = im.get("url") if isinstance(im, dict) else im
        if url:
            image_refs.append({
                "role": "primary",
                "url": url,
                "locally_verified": False,
                "confidence": "remote",
                "match_rule": "erp-image-url-v1",
            })
    category = product.get("category") or {}
    classification = product.get("classification") or {}
    raw_brand = product.get("brand")
    brand = raw_brand if raw_brand and raw_brand not in GARBAGE_BRANDS else None
    raw_model = product.get("model")
    model = raw_model if raw_model and raw_model != "/" else None
    return {
        "product_key": product.get("product_no"),
        "product_identity_key": "{}|{}|{}".format(
            product.get("name", ""), brand or "", model or "",
        ),
        "product_name": product.get("name"),
        "brand": brand,
        "model": model,
        "unit": product.get("unit_name"),
        **price,
        "category": category.get("name"),
        "product_group": classification.get("name"),
        "source_product_type": product.get("type_str"),
        "standardization": product.get("standardization_level_str"),
        "status": product.get("state_str"),
        "source_spaces": spaces,
        "function_tags": funcs,
        "product_role": role,
        "product_intro": intro,
        "image_refs": image_refs,
        "erp_id": product.get("id"),
        "erp_product_no": product.get("product_no"),
        "matched_by": matched_by,
    }


def filter_by_keywords(products, keywords):
    """客户端关键词收窄（多信号匹配）：

    匹配范围 = 产品名 + function_tags + source_spaces + 小类名 + 分组名。
    ERP 服务端 name 参数只模糊匹配 name+tags，不搜小类/分组名，因此
    小类/分组锚点必须在客户端实现。任一关键词命中即保留（宽召回），
    并在产品上记录 matched_keywords 供审计。
    """
    kws = [k.strip() for k in keywords if k and k.strip()]
    if not kws:
        return products
    out = []
    for p in products:
        haystack = "|".join(str(x) for x in [
            p.get("product_name") or "",
            p.get("category") or "",
            p.get("product_group") or "",
            *(p.get("function_tags") or []),
            *(p.get("source_spaces") or []),
        ])
        hits = [k for k in kws if k in haystack]
        if hits:
            p["matched_keywords"] = hits
            out.append(p)
    return out


def pull_slice(params, token, page_size, max_pages):
    out, page = [], 1
    while page <= max_pages:
        p = dict(params)
        p.update({"page": page, "page_size": page_size})
        d = api_get("product", p, token)
        lst = d["data"]["list"]
        out.extend(lst)
        if not lst or len(out) >= d["data"].get("cnt", 0):
            break
        page += 1
    return out


def route_queries(route, label_prefix):
    """把一条路由条目（space/business_line 同构：category_ids /
    classification_ids / name_keywords）展开为查询列表。"""
    queries = []
    for cid in route.get("category_ids", []):
        queries.append({"label": f"{label_prefix}|cat={cid}",
                        "params": {"category_id": cid, "state[]": 1}})
    for cl in route.get("classification_ids", []):
        queries.append({"label": f"{label_prefix}|cls={cl}",
                        "params": {"classification_id": cl, "state[]": 1}})
    for kw in route.get("name_keywords", []):
        queries.append({"label": f"{label_prefix}|name={kw}",
                        "params": {"name": kw, "state[]": 1}})
    return queries


def resolve_queries(args, mapping):
    queries = []
    if args.line:
        route = (mapping.get("query_routing", {}).get("business_lines", {})
                 or {}).get(args.line)
        if route:
            queries.extend(route_queries(route, f"line={args.line}"))
        else:
            known = sorted((mapping.get("query_routing", {})
                            .get("business_lines", {}) or {}).keys())
            raise SystemExit(
                f"✗ 未知业务线：{args.line}；product-mapping.json "
                f"query_routing.business_lines 中已定义：{known}")
    if args.space:
        stq = mapping.get("space_to_query", {}).get(args.space)
        if stq:
            queries.extend(route_queries(stq, f"space={args.space}"))
        else:
            # 未知空间：退化为按名称关键词查询（name 过滤可用）
            queries.append({"label": f"space={args.space}|name={args.space}",
                            "params": {"name": args.space, "state[]": 1}})
    for cid in args.category_id or []:
        queries.append({"label": f"cat={cid}", "params": {"category_id": cid, "state[]": 1}})
    for cl in args.classification_id or []:
        queries.append({"label": f"cls={cl}", "params": {"classification_id": cl, "state[]": 1}})
    for nm in args.name or []:
        queries.append({"label": f"name={nm}", "params": {"name": nm, "state[]": 1}})
    if not queries:
        # 默认：全量在售（仅在显式要求时）
        queries.append({"label": "all-state1", "params": {"state[]": 1}})
    return queries


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(65536), b""):
            h.update(blk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--line", help="业务线（在 product-mapping.json 的 query_routing.business_lines 中解析，如 生涯/科创）")
    ap.add_argument("--space", help="目标空间语义名（在 product-mapping.json 的 space_to_query 中解析）")
    ap.add_argument("--category-id", action="append", type=int, help="显式 ERP 父分类 id（可重复）")
    ap.add_argument("--classification-id", action="append", type=int, help="显式 ERP 叶子分组 id（可重复）")
    ap.add_argument("--name", action="append", help="按名称关键词查询（可重复）")
    ap.add_argument("--keywords", action="append",
                    help="客户端关键词收窄（可重复，或用逗号分隔）：在切片结果上按 产品名/tags/小类名/分组名 任一命中保留")
    ap.add_argument("--state", type=int, default=1, help="上下架状态，默认 1（在售）")
    ap.add_argument("--run-id", help="运行标识，默认时间戳")
    ap.add_argument("--out-dir", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "erp-runs"))
    ap.add_argument("--mapping", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "product-mapping.json"))
    ap.add_argument("--token-file", default=None, help="ERP token 文件路径（默认读环境变量 ERP_API_TOKEN 或 assets/erp_apikey.txt）")
    ap.add_argument("--page-size", type=int, default=100)
    ap.add_argument("--max-pages", type=int, default=30)
    args = ap.parse_args()

    token = load_token(args.token_file)
    mapping = json.load(open(args.mapping, encoding="utf-8"))
    mapping_sha = sha256_file(args.mapping)

    # 映射层新鲜度提醒：派生缓存层会随 ERP 标签/类目演变漂移
    gen = mapping.get("generated_at")
    if gen:
        try:
            gen_dt = datetime.fromisoformat(gen)
            age_days = (datetime.now() - gen_dt).days
            if age_days > 30:
                print(f"⚠ 映射层生成于 {gen}（{age_days} 天前）；如 ERP 类目/标签体系近期有调整，"
                      f"建议重跑 build_product_mapping.py 刷新派生缓存")
        except ValueError:
            pass

    queries = resolve_queries(args, mapping)
    seen = {}
    per_query = []
    for q in queries:
        raw = pull_slice(q["params"], token, args.page_size, args.max_pages)
        kept = []
        skipped = 0
        for p in raw:
            if is_garbage_name(p.get("name")):
                skipped += 1
                continue
            no = p.get("product_no")
            if no in seen:
                if q["label"] not in seen[no]["matched_by"]:
                    seen[no]["matched_by"].append(q["label"])
                continue
            norm = normalize(p, mapping, [q["label"]])
            seen[no] = norm
            kept.append(norm)
        per_query.append({"label": q["label"], "params": q["params"],
                          "raw_count": len(raw), "kept": len(kept), "skipped_garbage": skipped})

    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = os.path.join(args.out_dir, run_id)
    os.makedirs(run_dir, exist_ok=True)

    # --keywords 客户端收窄（name+tags 的服务端搜索之外的第二道过滤，
    # 额外覆盖小类名/分组名锚点）；兼容逗号分隔写法
    keywords = []
    for item in args.keywords or []:
        keywords.extend(k for k in re.split(r"[,，]", item) if k.strip())
    products = list(seen.values())
    pre_filter_count = len(products)
    if keywords:
        products = filter_by_keywords(products, keywords)

    snapshot = {
        "schema_version": "1.0",
        "run_id": run_id,
        "source": "ERP §6 product (yishengya)",
        "pulled_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mapping_ref": {"path": os.path.relpath(args.mapping, run_dir), "sha256": mapping_sha},
        "price_policy": mapping["price_policy"],
        "image_policy": mapping["image_policy"],
        "keyword_filter": keywords or None,
        "products": products,
    }
    snap_path = os.path.join(run_dir, "snapshot.json")
    with open(snap_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    snap_sha = sha256_file(snap_path)
    with open(os.path.join(run_dir, "snapshot.sha256"), "w", encoding="utf-8") as f:
        f.write(f"{snap_sha}  snapshot.json\n")

    manifest = {
        "run_id": run_id,
        "snapshot": {"path": "snapshot.json", "sha256": snap_sha, "product_count": len(snapshot["products"])},
        "mapping": {"path": os.path.relpath(args.mapping, run_dir), "sha256": mapping_sha,
                    "generated_at": mapping.get("generated_at")},
        "keyword_filter": {"keywords": keywords, "pre_filter_count": pre_filter_count,
                           "post_filter_count": len(products)} if keywords else None,
        "queries": per_query,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    with open(os.path.join(run_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"✓ 运行 {run_id} 完成")
    print(f"  命中产品（去重）: {len(snapshot['products'])}")
    print(f"  快照: {snap_path}")
    print(f"  快照 SHA-256: {snap_sha}")
    print(f"  映射层 SHA-256: {mapping_sha}")
    for q in per_query:
        print(f"   - {q['label']}: 原始 {q['raw_count']} / 保留 {q['kept']} / 脏数据跳过 {q['skipped_garbage']}")
    if keywords:
        print(f"  关键词收窄 {keywords}: {pre_filter_count} → {len(products)}")
    print(f"  带图片引用: {sum(1 for p in snapshot['products'] if p['image_refs'])}")
    print(f"  带 source_spaces: {sum(1 for p in snapshot['products'] if p['source_spaces'])}")
    print(f"  带 function_tags: {sum(1 for p in snapshot['products'] if p['function_tags'])}")


if __name__ == "__main__":
    main()
