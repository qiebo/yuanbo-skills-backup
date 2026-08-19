#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单文档「内容前后一致 / 矛盾」机检 (V1.0) —— crossref_check.py.

背景：响应文件的内容矛盾并非孤立一例，而是一类**跨位置信息不一致**问题，常见形态包括：
  ① 分项报价/采购清单表内字段错位：品牌填成另一行制造商的字号、产地与制造商地名不符、
     型号前缀实属其他制造商体系（贴牌/套牌/录入错列）；
  ② 同一敏感字段在多处出现且冲突：项目编号、投标主体公司名、法定代表人、金额大小写等；
  ③ 报价/参数声明与正文不一致（见铁律3，偏离声明 vs 正文参数）。
本脚本把③交由子代理 + 人工核对，把①②这两种**可用规则机械判定**的矛盾统一核查，
输出「疑似矛盾清单」供人工确认。**只做机械提示、绝不自动判违规**：品牌可为独立商标、
产地可异地代工，命中仅代表"该字段关系异常，需人工复核"。

Usage:
    python crossref_check.py output/响应文件_03.md
    python crossref_check.py --dir output
Output: 机检_内容一致性.md
"""
import sys
import os
import re
import json
import argparse
from collections import Counter

# ---------- 领域词典（可外置，见 config/consistency_dicts.json） ----------
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONFIG_PATH = os.environ.get("CROSSREF_DICT", os.path.join(_BASE, "config", "consistency_dicts.json"))
_DEFAULTS = {
    "common_cities": [
        "北京", "上海", "广州", "深圳", "南京", "苏州", "无锡", "常州", "徐州",
        "杭州", "宁波", "温州", "嘉兴", "湖州", "金华", "永康", "台州", "温岭",
        "青岛", "济南", "烟台", "合肥", "扬州", "镇江", "南通", "临沂", "东莞",
        "中山", "佛山", "珠海", "厦门", "福州", "泉州", "长沙", "武汉", "成都",
        "重庆", "天津", "大连", "郑州", "西安", "沈阳", "哈尔滨", "石家庄", "太原",
    ],
    "suffix_words": [
        "教育", "科技", "技术", "智能", "有限", "责任", "公司", "集团", "厂",
        "绘图", "仪器", "五金", "工具", "电机", "电子", "机械", "塑料",
        "美术", "制造", "实业", "工贸", "研发", "股份", "合伙",
        "市", "县", "区", "省", "镇", "街道",
    ],
    "noise_words": [
        "原厂", "出厂", "生产厂", "备用厂", "合作厂", "工厂", "各厂", "驻厂",
        "选厂", "家具出厂", "货物出厂", "设备出厂", "每台设备出厂", "每日工厂",
        "支付工厂", "对接厂", "联系原厂", "内从原厂", "内联系原厂", "直接退回原厂",
    ],
    "model_prefix_min_len": 2,
    "model_prefix_max_len": 6,
}
def _load_dicts():
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return {k: cfg.get(k, v) for k, v in _DEFAULTS.items()}
    except OSError:
        return dict(_DEFAULTS)
_CFG = _load_dicts()
COMMON_CITIES = _CFG["common_cities"]
SUFFIX_WORDS = _CFG["suffix_words"]
_NOISE_WORDS = tuple(_CFG["noise_words"])
PREFIX_MIN, PREFIX_MAX = _CFG["model_prefix_min_len"], _CFG["model_prefix_max_len"]

_MODEL_PREFIX_RE = re.compile(rf"([A-Za-z]{{{PREFIX_MIN},{PREFIX_MAX}}})[-\s]?")

# ---------- 表字段错位 / 串行（规则 ①） ----------
CITY_HINTS = re.compile(r"([\u4e00-\u9fa5]{2,4}?(?:市|县|州))")

def extract_city(s):
    if not s:
        return None
    s2 = re.sub(r"[一-鿿]*?(?:省|自治区)", "", s)
    for c in COMMON_CITIES:
        if c in s2:
            return c
    for m in CITY_HINTS.finditer(s):
        return m.group(1)
    return None

def manufacturer_zihao(manu):
    s = re.sub(r"（[^）]*）", "", manu)
    for w in SUFFIX_WORDS:
        s = s.replace(w, "")
    return re.sub(r"\s", "", s) or manu

def extract_column_map(header):
    cols = [c.strip() for c in header]
    def find(*keys):
        for k in keys:
            for c in cols:
                if k in c:
                    return cols.index(c)
        return None
    return {
        "no": find("序号") or 0,
        "name": find("名称", "品名", "产品"),
        "manu": find("制造商", "厂家"),
        "brand": find("品牌"),
        "origin": find("产地"),
        "model": find("规格", "型号"),
    }

def is_data_row(cells):
    return bool(re.fullmatch(r"\d{1,4}", cells[0].strip()))

def parse_tables(text):
    tables, cur, start = [], None, None
    for i, ln in enumerate(text.splitlines()):
        if ln.lstrip().startswith("|"):
            if cur is None:
                cur, start = [], i
            cur.append(ln)
        else:
            if cur is not None:
                tables.append((start, i, cur)); cur = None
    if cur is not None:
        tables.append((start, len(text.splitlines()), cur))
    return tables

def detect_table_misalign(text):
    findings, rows_in_file = [], []
    for _srow, _erow, lines in parse_tables(text):
        header, rows = None, []
        for ln in lines:
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if not cells or all(not c for c in cells):
                continue
            if header is None:
                if "制造商" in "".join(cells) and ("品牌" in "".join(cells) or "产地" in "".join(cells)):
                    header = extract_column_map(cells)
                continue
            if not is_data_row(cells):
                continue
            rows.append({k: (cells[i] if i is not None and i < len(cells) else "") for k, i in header.items()})
        if len(rows) < 2:
            continue
        rows_in_file = rows
        manu_zihao, zihao_manus = {}, {}
        for r in rows:
            m = r.get("manu", "")
            if m:
                z = manufacturer_zihao(m); manu_zihao[m] = z; zihao_manus.setdefault(z, m)
        prefix_brand, prefix_manuz = {}, {}
        for r in rows:
            pm = _MODEL_PREFIX_RE.match(r.get("model", "").strip())
            if pm:
                p = pm.group(1).upper()
                prefix_brand.setdefault(p, Counter()).update([r.get("brand", "")])
                if r.get("manu"):
                    prefix_manuz.setdefault(p, Counter()).update([manu_zihao.get(r["manu"], r["manu"])])
        mb_mode = {p: c.most_common(1)[0][0] for p, c in prefix_brand.items() if c}
        mm_mode = {p: c.most_common(1)[0][0] for p, c in prefix_manuz.items() if c}
        for r in rows:
            manu = r.get("manu", ""); brand = r.get("brand", ""); origin = r.get("origin", "")
            model = r.get("model", "").strip(); z = manu_zihao.get(manu, manu)
            issues = []
            if brand and z:
                if brand in z or z in brand:
                    pass
                else:
                    mis = [m2 for z2, m2 in zihao_manus.items() if z2 and brand in z2 and m2 != manu]
                    if mis:
                        issues.append(f"品牌「{brand}」实为另一行「{mis[0]}」字号所含，疑似「品牌列」取错(错位链)")
                    else:
                        issues.append(f"品牌「{brand}」与制造商「{manu}」无字号关联(独立品牌则忽略)")
            pm = _MODEL_PREFIX_RE.match(model)
            if pm:
                P = pm.group(1).upper(); mb = mb_mode.get(P); mm = mm_mode.get(P)
                if brand and mb and brand != mb and not (brand in z or z in brand):
                    issues.append(f"型号前缀「{P}」表内多数对应品牌「{mb}」，本行「{brand}」，疑似「型号/品牌」错位")
                if z and mm and z != mm and brand != mb:
                    issues.append(f"型号前缀「{P}」表内多数对应制造商「{mm}」，本行「{z}」，疑似「型号/制造商」错位")
            mcity = extract_city(manu); ocity = extract_city(origin) if origin else None
            if mcity and ocity and mcity != ocity:
                note = "（温岭→台州等地级关系属正常）" if (mcity, ocity) in (("温岭", "台州"), ("台州", "温岭")) else ""
                issues.append(f"制造商在「{mcity}」产地写「{ocity}」，疑「产地列」串行{note}")
            if issues:
                findings.append({"no": r.get("no", "?"), "name": r.get("name", ""), "manu": manu,
                                 "brand": brand, "origin": origin, "model": model, "issues": issues})
        # 型号重复
        model_rows = {}
        for r in rows:
            if r.get("model"):
                model_rows.setdefault(r["model"], []).append(r)
        for m, rs in model_rows.items():
            if len(rs) > 1 and len({r.get("name", "") for r in rs}) > 1:
                findings.append({"no": "+".join(r.get("no", "?") for r in rs),
                                 "name": "/".join(sorted({r.get("name", "") for r in rs})), "manu": "",
                                 "brand": "", "origin": "", "model": m,
                                 "issues": [f"同一型号「{m}」被多个不同产品重复使用，疑「规格型号」错位"]})
    return findings

# ---------- 跨位置敏感字段冲突（规则 ②） ----------
NUM_CN = {"零":0,"壹":1,"贰":2,"叁":3,"肆":4,"伍":5,"陆":6,"柒":7,"捌":8,"玖":9,
          "一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9}
UNIT_CN = {"拾":10,"十":10,"佰":100,"百":100,"仟":1000,"千":1000,"万":10000,"億":10**8,"亿":10**8}
def cnum(s):
    s = re.sub(r"[元整￥¥\s,，]+", "", s)
    if not s:
        return None
    total, sec, cur = 0, 0, 0
    for ch in s:
        if ch in NUM_CN:
            cur = NUM_CN[ch]
        elif ch in UNIT_CN:
            u = UNIT_CN[ch]
            if u >= 10 ** 4:
                total = (total + sec + cur) * u; sec = 0; cur = 0
            else:
                sec += (cur or 1) * u; cur = 0
        else:
            return None
    return total + sec + cur

def detect_scattered_conflicts(text):
    findings = []
    # 项目编号：仅取带「采购/项目/招标」等标签在内的编号（如 JXYL2026-B0626），
    # 避免把报告编号/标准编号/纯数字型号（T2761-2024、KT89021）误当项目编号
    nums = [n for n in re.findall(
        r"(?:项目|采购|比选|磋商|询价|招标)[编\s]{1,3}[号：:\s]*([A-Z][A-Z0-9\-\—]{2,18})", text) if n]
    keyforms = {}
    for v in nums:
        keyforms.setdefault(v.upper(), set()).add(v)
    dif_nums = set()
    for k, vs in keyforms.items():
        dif_nums.add(k)
        if len(vs) > 1:
            findings.append({"kind": "项目编号", "val": "/".join(sorted(vs)),
                             "issues": [f"同一编号存在不同写法：{' / '.join(sorted(vs))}"]})
    if len(dif_nums) > 1:
        findings.append({"kind": "项目编号", "val": "/".join(sorted(dif_nums)),
                         "issues": [f"文中出现多个不同项目编号：{' / '.join(sorted(dif_nums))}（请核对是否混入他文件）"]})
    # 投标主体：仅在「供应商名称（盖章）」等声明处提取，全文主体应唯一
    bodies = set()
    bodies |= set(re.findall(r"(?:供应商名称|投标人名称|供应商|投标人)[（(]?[盖章][）)]?[：:\s　]*([\u4e00-\u9fa5]{2,18}?(?:有限公司|公司|厂))", text))
    bodies |= set(re.findall(r"([\u4e00-\u9fa5]{2,18}?(?:有限公司|公司|厂))\s*[（(][盖章][）)]", text))
    # 过滤噪声词（原厂/出厂/生产厂等动词性、非主体）—— 词典外置于 config/consistency_dicts.json
    bodies = {b for b in bodies if b and not any(w in b for w in _NOISE_WORDS)}
    if len(bodies) > 1:
        findings.append({"kind": "投标主体声明", "val": "/".join(sorted(bodies)),
                         "issues": [f"不同位置声明的投标主体不一致：{' / '.join(sorted(bodies))}"]})
    # 法定代表人：只取声明处紧随其后的人名，过滤「或其授权/盖章」等噪声
    faren = set()
    for m in re.finditer(r"法定代表人[：:\s　]*([\u4e00-\u9fa5]{2,4})", text):
        nm = m.group(1)
        if nm and nm[0] not in "或或被其授盖章签" and not nm.endswith(("授权", "委托", "身份证")):
            faren.add(nm)
    if len(faren) > 1:
        findings.append({"kind": "法定代表人", "val": "/".join(sorted(faren)),
                         "issues": [f"多处法定代表人姓名不一致：{' / '.join(sorted(faren))}"]})
    # 金额：小写 vs 中文大写（当前仅在大写数无法对应到任何小写数时提示，避免误报）
    upper_total = []
    for m in re.finditer(r"([零壹贰叁肆伍陆柒捌玖拾佰仟万亿圆元]{2,}整?)", text):
        v = cnum(m.group(1))
        if v is not None:
            upper_total.append(v)
    arab = [int(x) for x in re.findall(r"[￥¥]\s*(\d[\d,]{0,9})", text.replace(",", ""))]
    if upper_total and arab:
        for ut in set(upper_total):
            if ut not in arab and not any(a and (ut % a == 0 or a % ut == 0) for a in arab):
                findings.append({"kind": "金额大小写", "val": f"大写={ut}",
                                 "issues": [f"中文大写金额 {ut} 未对应到相同小写金额（小写：{'、'.join(map(str, arab))}）"]})
    return findings

def detect(doc_path):
    text = open(doc_path, "r", encoding="utf-8").read()
    out = []
    for f in detect_table_misalign(text):
        f["section"] = "分项报价/清单表字段"
        out.append(f)
    for g in detect_scattered_conflicts(text):
        out.append({"no": "", "name": g["kind"], "manu": "", "brand": "", "origin": "", "model": g["val"],
                    "issues": g["issues"], "section": "跨位置字段"})
    return out

def render(findings, label):
    lines = [f"## {label}（疑似 {len(findings)} 处）", ""]
    lines.append("> 仅机械提示，命中不代表违规：品牌可为独立商标、产地可异地代工。命中项须结合正文与原件人工复核。")
    lines.append("")
    lines.append("| 位置/序号 | 产品/字段 | 制造商 | 品牌 | 产地 | 型号 | 疑似矛盾 |")
    lines.append("|---|---|---|---|---|---|---|")
    if not findings:
        lines.append("| — | 未发现疑似前后矛盾 | — | — | — | — | — |")
    for f in findings:
        lines.append(f"| {f['section']} / {f['no']} | {f['name'][:16]} | {f['manu'][:16]} | {f['brand']} | {f['origin']} | {f['model'][:14]} | {('；'.join(f['issues']))} |")
    lines.append("")
    lines.append("> 使用提示：①表字段—请对照《采购清单》原文与质保单，确认是「录入错列」还是「贴牌/套牌」；"
                 "②跨位置字段—请核查是否为多投标人串文件或版本混用。前者改表即可，后者可能触及实质响应/废标条款。")
    lines.append("")
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser(description="单文档内容一致性/矛盾机检 (V1.0).")
    ap.add_argument("files", nargs="*")
    ap.add_argument("--dir", help="扫描目录下所有 响应文件_*.md")
    args = ap.parse_args()
    paths = list(args.files)
    if args.dir:
        for fn in sorted(os.listdir(args.dir)):
            if fn.startswith("响应文件_") and fn.endswith(".md"):
                paths.append(os.path.join(args.dir, fn))
    if not paths:
        print("Usage: crossref_check.py <md...> | --dir output")
        sys.exit(1)
    parts = ["# 机检_内容一致性 / 矛盾（单文档跨位置核查）", ""]
    for p in paths:
        finds = detect(p)
        parts.append(render(finds, os.path.basename(p)))
    report = "\n".join(parts)
    print(report)
    out_path = os.path.join(os.path.dirname(os.path.abspath(paths[0])), "机检_内容一致性.md")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"\n[written] {out_path}")
    except OSError:
        pass

if __name__ == "__main__":
    main()