#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成薄映射层 assets/product-mapping.json（数据驱动，基于 ERP §6 实测）。

从 ERP 拉取：
  1) 分类树（category-list）
  2) 全部在售（state=1）产品（自带分页循环）
然后自动推导：
  - tag_routing：把 ERP `tags` 分流为 source_spaces / function_tags / 品牌型号噪声 的规则
  - category_fallback：按 category_id 推论语义（用于空 tags 产品回退）
  - space_to_query：空间名 → 应查的 ERP 分类/关键词（按需切片拉取用）
  - role_map：父分类 → product_role
薄映射层是配置清单 skill 唯一由人维护的"固定资源"，产品内容运行期从 ERP §6 按需切片拉取。

依赖：仅 Python 标准库。
"""
import json
import os
import re
import urllib.parse
import urllib.request
from collections import Counter, defaultdict

# token 解析优先级：--token-file > 环境变量 ERP_API_TOKEN > 同级/ assets/erp_apikey.txt
PROD_BASE = os.environ.get("ERP_API_BASE", "https://erpapi.yishengya.cn/api")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "product-mapping.json")

SPACE_SUFFIXES = ["室", "教室", "空间", "中心", "区", "馆", "厅"]
# 已知品牌（ERP `brand` 字段 + 观察到的品牌 tags），可继续扩充
SEED_BRANDS = [
    "翼生涯", "weeemake", "朗心", "南京优冠", "阳光心健", "世纪萌芽", "新启蒙模型",
    "绿萝心数", "希沃", "心理测评与预警", "远播", "生涯翼站", "科大讯飞", "强脑",
]

MODEL_RE = re.compile(r"(?:[A-Za-z].*\d|\d.*[A-Za-z])|V\d|FH\d|LLXLYPT|[-_][A-Z0-9]{2,}")


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


def get(path, params, token):
    qs = urllib.parse.urlencode(params)
    url = f"{PROD_BASE}/{path}?{qs}"
    req = urllib.request.Request(url, headers={
        "accept": "application/json",
        "authorization": "Bearer " + token,
    })
    return json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8"))


def pull_all_products(token):
    out, page = [], 1
    while True:
        d = get("product", {"state[]": 1, "page": page, "page_size": 100}, token)
        lst = d["data"]["list"]
        out.extend(lst)
        if not lst or len(out) >= d["data"]["cnt"]:
            break
        page += 1
    return out


def split_tag(tag):
    # tags 可能是逗号（中/英）拼接的字符串
    return [t.strip() for t in re.split(r"[,，、;；]", tag) if t.strip()]


def is_modelish(t):
    if MODEL_RE.search(t):
        return True
    # 纯型号/编号（含拉丁字母且较短、或含连字符+大写）
    if re.search(r"[A-Za-z]", t) and re.search(r"\d", t):
        return True
    return False


def sha256_file(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(65536), b""):
            h.update(blk)
    return h.hexdigest()


def deep_merge(base, overlay):
    """人工覆盖层深合并：dict 递归合并，其余类型 overlay 整体覆盖。"""
    for k, v in overlay.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            base[k] = deep_merge(base[k], v)
        else:
            base[k] = v
    return base


def main(token_file=None):
    token = load_token(token_file)
    print("[1/5] 拉取分类树 ...")
    cat_tree = get("category/list", {}, token)["data"]
    # 建立 id -> {name, parent_id, parent_name}，大类与小类都入表
    # （旧版只遍历顶层大类，导致小类名查不到、父级默认查询分支静默失效）
    cat_meta = {}
    for node in cat_tree:
        cat_meta[node["id"]] = {
            "name": node["name"], "parent_id": node.get("parent_id"),
            "parent_name": (node.get("parent") or {}).get("name"),
        }
        for child in (node.get("children") or []):
            cat_meta[child["id"]] = {
                "name": child["name"], "parent_id": node["id"],
                "parent_name": node["name"],
            }

    print("[2/5] 拉取在售产品 ...")
    prods = pull_all_products(token)
    print(f"      在售产品 {len(prods)} 条")

    brands = set(SEED_BRANDS)
    for p in prods:
        b = (p.get("brand") or "").strip()
        if b and b not in ("/", "一批", "无", "-", ""):
            brands.add(b)

    space_tags = Counter()
    func_tags = Counter()
    brand_tags = Counter()
    # category_id -> {space: Counter, func: Counter}
    cat_space = defaultdict(Counter)
    cat_func = defaultdict(Counter)
    # space_tag -> 父级 category_id Counter（用于 space_to_query；category_id 参数只认父级）
    space_to_cat = defaultdict(Counter)
    # space_tag -> 叶子 classification_id 集合
    space_to_cls = defaultdict(set)
    # parent category -> product_role 计数（简单推断）
    parent_role = defaultdict(Counter)

    for p in prods:
        cat_id = p.get("category_id")
        cls_id = p.get("classification_id")
        parent_id = (p.get("category") or {}).get("parent_id")
        parent_name = (p.get("category") or {}).get("parent")
        if isinstance(parent_name, dict):
            parent_name = parent_name.get("name")
        tags = []
        for raw in (p.get("tags") or []):
            tags.extend(split_tag(raw))
        seen_space, seen_func = set(), set()
        for t in tags:
            if any(t.endswith(s) for s in SPACE_SUFFIXES):
                space_tags[t] += 1
                seen_space.add(t)
                if parent_id:
                    space_to_cat[t][parent_id] += 1
                if cls_id:
                    space_to_cls[t].add(cls_id)
                cat_space[cat_id][t] += 1
            elif t in brands or is_modelish(t):
                brand_tags[t] += 1
            else:
                func_tags[t] += 1
                seen_func.add(t)
                cat_func[cat_id][t] += 1
        # role 推断（仅在有明确关键词时记录，避免噪声"其他"）
        if parent_name:
            if "软件" in parent_name or "系统" in parent_name:
                parent_role[parent_id or parent_name]["软件平台"] += 1
            elif "硬件" in parent_name or "设备" in parent_name:
                parent_role[parent_id or parent_name]["硬件设备"] += 1
            elif "文创" in parent_name or "长廊" in parent_name or "文化" in parent_name:
                parent_role[parent_id or parent_name]["环境创设"] += 1
        if cls_id:
            pass  # classification ids collected inside the space branch above

    print("[3/5] 构建 category_fallback ...")
    category_fallback = {}
    all_cat_ids = set(cat_space) | set(cat_func)
    for cid in all_cat_ids:
        top_space = [t for t, _ in cat_space[cid].most_common(6)]
        top_func = [t for t, _ in cat_func[cid].most_common(10)]
        category_fallback[str(cid)] = {
            "category_name": cat_meta.get(cid, {}).get("name"),
            # 按类目内 tags 词频派生，对混合类目（如科创设备及耗材）可能失真，
            # 仅供空 tags 产品的低置信补充语义；匹配主锚点是小类名/分组名/tags。
            "confidence": "low",
            "source_spaces": top_space,
            "function_tags": top_func,
        }

    print("[4/5] 构建 space_to_query ...")
    space_to_query = {}
    for sp, cc in space_to_cat.items():
        # 注意：category_id 参数只认父级且返回整个大类（过宽），不适合按空间切片；
        # 精确切片靠 name_keywords（ERP 的 name 参数实际跨 name+tags 关键词搜索）与叶子 classification_id。
        space_to_query[sp] = {
            "category_ids": [],
            "classification_ids": [int(c) for c in list(space_to_cls.get(sp, []))[:3]],
            "name_keywords": [sp],
        }
    # 父级大类默认查询（按 parent 聚合）
    parent_default = defaultdict(set)
    for cid, meta in cat_meta.items():
        pid = meta.get("parent_id")
        if pid:
            parent_default[pid].add(cid)
    for pid, cids in parent_default.items():
        key = cat_meta.get(pid, {}).get("name") or f"cat_{pid}"
        space_to_query.setdefault(key, {
            "category_ids": [int(pid)],
            "classification_ids": [],
            "name_keywords": [],
        })

    print("[5/5] 写出 product-mapping.json ...")
    mapping = {
        "schema_version": "1.0",
        "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "source": f"ERP §6 运行时实测（{len(prods)} 条 state=1 产品 + category/list 分类树），seed 2026-08-12",
        "note": "薄映射层：仅含语义映射/主键映射/价格图片策略。产品内容运行期从 ERP §6 按需切片拉取（见 scripts/fetch_erp_catalog.py）。",
        "price_policy": {
            "market_price": "default_unit_price",
            "channel_price": "default_agent_price",
            "cost_price": "default_cost_price",
        },
        "image_policy": {
            "source": "erp_image_url",
            "locally_verified": False,
            "confidence": "remote",
            "match_rule": "erp-image-url-v1",
            "download": False,
            "note": "引用 ERP image_url 远程链接，不下载、不本地 SHA-256；非本地核验须在追溯审计标注",
        },
        "key_map": {
            "catalog_product_key": "product_no",
            "product_identity_key": "name|brand|model（brand/model 为 '/' 时仅用 name）",
            "legacy_key_compat": "旧 standard-products.json 的 product_key 不再使用；如需回溯可按 product_no 关联",
        },
        "tag_routing": {
            "space_suffixes": SPACE_SUFFIXES,
            "space_allowlist": sorted(space_tags),
            "brand_dictionary": sorted(brands),
            "model_code_regex_hint": "含拉丁字母且含数字 / 形如 V1.0、FH75EA、LLXLYPT-V1.0 的 tag 视为型号噪声",
            "rule": "tag 命中 space 规则→source_spaces；命中 brand_dictionary 或型号形态→忽略；其余→function_tags",
        },
        "category_fallback": category_fallback,
        "space_to_query": space_to_query,
        "role_map": {str(k): v.most_common(1)[0][0] for k, v in parent_role.items() if v},
    }

    # 人工覆盖层（overlay）：keyword_aliases / query_routing.business_lines /
    # 空间条目修正等人工知识在此合并，重跑本脚本不会丢失
    overlay_path = os.path.join(os.path.dirname(OUT), "product-mapping.overlay.json")
    if os.path.exists(overlay_path):
        overlay = json.load(open(overlay_path, encoding="utf-8"))
        mapping = deep_merge(mapping, overlay)
        mapping["overlay_ref"] = {
            "path": os.path.basename(overlay_path),
            "sha256": sha256_file(overlay_path),
            "note": "人工覆盖层已合并；本字段记录其指纹以便审计区分自动层/人工层变化",
        }
        print(f"      已合并人工覆盖层: {overlay_path}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"已写出 -> {OUT}")
    print(f"  space tags: {len(space_tags)} | func tags: {len(func_tags)} | brands: {len(brands)}")
    print(f"  category_fallback: {len(category_fallback)} | space_to_query: {len(space_to_query)} | role_map: {len(mapping['role_map'])}")


if __name__ == "__main__":
    import argparse
    _ap = argparse.ArgumentParser(description="生成薄映射层 assets/product-mapping.json")
    _ap.add_argument("--token-file", default=None, help="ERP token 文件路径（默认读 ERP_API_TOKEN 环境变量或 assets/erp_apikey.txt）")
    _args = _ap.parse_args()
    main(_args.token_file)
