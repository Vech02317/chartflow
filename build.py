# -*- coding: utf-8 -*-
"""逐图执行流水线:校验 fig json → 渲染 → 自动验收。

用法: python3 build.py [plan.json]    默认 samples/library/plan.json
退出码 0 = 全部通过。产物落在 plan 同级的 out/,抽取产物在 plan 同级的 figs/。
"""
import importlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from engine import check_figs  # noqa: E402

RENDERERS = {"er": "render_er", "class": "render_class", "flow": "render_flow"}


def main(plan_path) -> bool:
    from jsonschema import validate
    plan_path = pathlib.Path(plan_path).resolve()
    base = plan_path.parent
    figs_dir, out_dir = base / "figs", base / "out"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))

    results = []
    for fig in plan["figures"]:
        fid, ftype = fig["id"], fig["type"]
        if fig.get("status") == "skip":
            print(f"[{fid}] skip —— {fig.get('note', '(未注明原因)')}")
            continue

        fig_json = figs_dir / f"{fid}.json"
        if not fig_json.exists():
            print(f"[{fid}] FAIL —— 缺 {fig_json.relative_to(base)};"
                  f"agent 应先按 prompts/extract_{ftype}.md 产出它")
            results.append(False)
            continue

        contract = ROOT / "contract" / f"{ftype}.schema.json"
        data = json.loads(fig_json.read_text(encoding="utf-8"))
        validate(instance=data,
                 schema=json.loads(contract.read_text(encoding="utf-8")))

        module = importlib.import_module(f"engine.{RENDERERS[ftype]}")
        module.render(fig_json, fid, out_dir)
        ok = check_figs.check(fid, ftype, fig_json, out_dir, quiet=True)
        print(f"[{fid}] {ftype} —— {'PASS' if ok else 'FAIL'}"
              f"{'' if ok else f' (详见 out/{fid}.check.txt)'}")
        results.append(ok)

    passed = all(results) if results else False
    print(f"\n{sum(results)}/{len(results)} 通过 —— RESULT: "
          f"{'PASS' if passed else 'FAIL'}")
    return passed


if __name__ == "__main__":
    default = ROOT / "samples" / "library" / "plan.json"
    target = sys.argv[1] if len(sys.argv) > 1 else default
    sys.exit(0 if main(target) else 1)
