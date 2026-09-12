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

RENDERERS = {"er": "render_er", "class": "render_class", "flow": "render_flow",
             "attr": "render_attr"}

PENDING_HEADER = """# 待确认清单

**这是给人看的** —— 抽取时 agent 拿不准、需要你对着源码 / 建表语句拍板的地方。

`build.py` 的 PASS 只证明「图与契约一致」,**不证明「契约与事实一致」** —— 数据抽得对不对,
只能由你看着这份清单核对。本文件由 `build.py` 从各图的 `figs/<id>.待确认.md` 机械汇总,
**不要手改**;要改就改源头那几份,然后重跑 `build.py`。
"""


def _write_pending(plan, figs_dir, out_dir):
    """把各图的 `figs/<id>.待确认.md` 汇总成 `out/待确认.md`。

    「待确认」是这工具唯一的人机接口 —— 它要是只活在 agent 的对话里,会话一结束就没了,
    「人拍板」这一步就断了。所以要求 agent 落到文件;这里只做机械汇总,不做判断。

    返回 (汇总文件路径, 未提交记录的图 id 列表)。已 skip 的图不算。
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    missing, parts = [], []
    for fig in plan["figures"]:
        if fig.get("status") == "skip":
            continue
        fid = fig["id"]
        src = figs_dir / f"{fid}.待确认.md"
        body = src.read_text(encoding="utf-8").strip() if src.exists() else ""
        if not body:
            missing.append(fid)
            body = "（该图未提交待确认记录 —— 请确认它是不是真的没有要人拍板的地方）"
        parts.append(f"## {fid} {fig.get('title', '')}\n\n{body}\n")
    dst = out_dir / "待确认.md"
    dst.write_text(PENDING_HEADER + "\n" + "\n".join(parts), encoding="utf-8")
    return dst, missing


def main(plan_path) -> bool:
    from jsonschema import ValidationError, validate
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
        try:
            validate(instance=data,
                     schema=json.loads(contract.read_text(encoding="utf-8")))
        except ValidationError as e:
            # 契约错误要给人话,不是 traceback —— 报错路径直接落到出问题的那个键
            where = "/".join(str(p) for p in e.absolute_path) or "(根)"
            print(f"[{fid}] FAIL —— 不符契约 {where}:{e.message}")
            results.append(False)
            continue

        module = importlib.import_module(f"engine.{RENDERERS[ftype]}")
        module.render(fig_json, fid, out_dir)
        ok, warns = check_figs.check(fid, ftype, fig_json, out_dir, quiet=True)
        print(f"[{fid}] {ftype} —— {'PASS' if ok else 'FAIL'}"
              f"{'' if ok else f' (详见 out/{fid}.check.txt)'}")
        for w in warns:
            print(f"        {w}")
        results.append(ok)

    dst, missing = _write_pending(plan, figs_dir, out_dir)
    tail = (f"({len(missing)} 张未提交记录:{'、'.join(missing)})" if missing
            else "(全部图都已记录)")
    print(f"[待确认] {dst.relative_to(base)} {tail}")

    passed = all(results) if results else False
    print(f"\n{sum(results)}/{len(results)} 通过 —— RESULT: "
          f"{'PASS' if passed else 'FAIL'}")
    return passed


if __name__ == "__main__":
    default = ROOT / "samples" / "library" / "plan.json"
    target = sys.argv[1] if len(sys.argv) > 1 else default
    sys.exit(0 if main(target) else 1)
