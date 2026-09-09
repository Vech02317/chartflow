# -*- coding: utf-8 -*-
"""自动验收:核对渲染产物齐全、非空、与契约计数一致(仿毕设 check_figs 思路)。

验收规则都写在这里,是流水线的“门禁”——契约里加实体却不重跑,这里就会拦住。
"""
import json
import pathlib


def check(er_path, out_dir, report_name="check_report.txt") -> bool:
    out = pathlib.Path(out_dir)
    er = pathlib.Path(er_path)
    data = json.loads(er.read_text(encoding="utf-8"))
    meta = json.loads((out / "er.meta.json").read_text(encoding="utf-8"))

    lines, all_ok = [], True

    def ok(cond, msg):
        nonlocal all_ok
        all_ok &= bool(cond)
        lines.append(("[PASS] " if cond else "[FAIL] ") + msg)
        return cond

    for name in ("er.svg", "er.png"):
        f = out / name
        ok(f.exists(), f"{name} 存在")
        if f.exists():
            size = f.stat().st_size
            ok(size > 500, f"{name} 非空 ({size} B)")

    ok(meta["entities"] == len(data["entities"]),
       f"实体数一致 (契约 {len(data['entities'])} = 产物 {meta['entities']})")
    ok(meta["relations"] == len(data["relations"]),
       f"关系数一致 (契约 {len(data['relations'])} = 产物 {meta['relations']})")

    result = "PASS" if all_ok else "FAIL"
    lines.append(f"\nRESULT: {result}")
    (out / report_name).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return all_ok


if __name__ == "__main__":
    import sys
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.exit(0 if check(root / "samples/library/er.json", root / "out") else 1)
