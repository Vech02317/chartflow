# -*- coding: utf-8 -*-
"""校验《出图清单》plan.json:结构(schema)+ 语义(id 唯一 / source 具体 / skip 写明原因)。

用法: python3 plan.py [plan.json]   默认 samples/library/plan.json
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SCHEMA = ROOT / "contract" / "plan.schema.json"
VAGUE = ("全文", "整篇", "相关章节", "略", "见上文")


def validate_plan(plan_path) -> bool:
    import jsonschema
    plan_path = pathlib.Path(plan_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=plan,
                        schema=json.loads(SCHEMA.read_text(encoding="utf-8")))

    problems = []
    ids = [f["id"] for f in plan["figures"]]
    if len(ids) != len(set(ids)):
        problems.append("id 有重复")
    for f in plan["figures"]:
        if any(v in f["source"] for v in VAGUE):
            problems.append(f"{f['id']} 的 source 太含糊:{f['source']}")
        if f.get("status") == "skip" and not f.get("note"):
            problems.append(f"{f['id']} 标了 skip 却没写 note")

    print(f"图清单:{len(plan['figures'])} 张 —— "
          + ", ".join(f"{f['id']}({f['type']}):{f['title']}" for f in plan["figures"]))
    for p in problems:
        print("[FAIL]", p)
    print("RESULT:", "PASS" if not problems else "FAIL")
    return not problems


if __name__ == "__main__":
    default = ROOT / "samples" / "library" / "plan.json"
    target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else default
    sys.exit(0 if validate_plan(target) else 1)
