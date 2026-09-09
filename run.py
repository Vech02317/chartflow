# -*- coding: utf-8 -*-
"""一键跑通 ER 流水线:校验契约 → 渲染 → 自动验收。

用法: python3 run.py   (退出码 0=通过, 1=失败)
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
SCHEMA = ROOT / "contract" / "er.schema.json"
ER = ROOT / "samples" / "library" / "er.json"
OUT = ROOT / "out"


def step1_validate():
    import jsonschema
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    data = json.loads(ER.read_text(encoding="utf-8"))
    jsonschema.validate(instance=data, schema=schema)
    print(f"[1/3] 契约校验 OK —— {len(data['entities'])} 实体 / "
          f"{len(data['relations'])} 关系")


def step2_render():
    from engine.render_er import render
    render(ER, OUT)
    print("[2/3] 渲染 OK —— out/er.svg, out/er.png")


def step3_check() -> bool:
    from engine.check_figs import check
    ok = check(ER, OUT)
    print(f"[3/3] 验收 {'PASS' if ok else 'FAIL'} (详情 out/check_report.txt)")
    return ok


if __name__ == "__main__":
    step1_validate()
    step2_render()
    ok = step3_check()
    sys.exit(0 if ok else 1)
