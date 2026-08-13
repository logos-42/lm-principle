# -*- coding: utf-8 -*-
"""TeX 结构完整性检查: begin/end 配对 + label/ref 一致性"""
import re
import sys
from collections import Counter

p = sys.argv[1] if len(sys.argv) > 1 else "paper/main_jrnl.tex"
s = open(p, encoding="utf-8").read()

begins = re.findall(r"\\begin\{(\w+)\}", s)
ends = re.findall(r"\\end\{(\w+)\}", s)
b, e = Counter(begins), Counter(ends)
ok = True
for k in set(b) | set(e):
    if b[k] != e[k]:
        print(f"MISMATCH: {k} begin={b[k]} end={e[k]}")
        ok = False
print("begin/end 配对:", "OK" if ok else "FAIL")

labels = set(re.findall(r"\\label\{([^}]+)\}", s))
refs = set(re.findall(r"\\ref\{([^}]+)\}", s))
missing = refs - labels
print(f"labels={len(labels)} refs={len(refs)} 缺失引用: {sorted(missing) if missing else '无'}")

m = re.search(r"\\title\{(.*?)\}", s, re.S)
print("标题:", m.group(1).replace("\n", " ")[:100] if m else "未找到")

# 未闭合花括号粗检
opens, closes = s.count("{"), s.count("}")
print(f"花括号: {{ = {opens}, }} = {closes}, {'OK' if opens == closes else 'FAIL'}")
sys.exit(0 if ok and not missing and opens == closes else 1)
