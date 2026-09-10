# -*- coding: utf-8 -*-
"""自动验收(门禁):产物齐全 / 非空 / 计数与契约一致 / 数据改了没重跑。

验收规则都写在这里;契约加内容却不重跑,这里就会拦住。
注意:PASS 只证“图与契约一致”,不证“契约与事实一致”——后者必须人审。
"""
import hashlib
import json
import pathlib

from engine._common import COUNT_FIELDS


def check(fig_id, type_, data_path, out_dir, quiet=False) -> bool:
    out = pathlib.Path(out_dir)
    dp = pathlib.Path(data_path)
    data = json.loads(dp.read_text(encoding="utf-8"))
    lines, all_ok = [], True

    def ok(cond, msg):
        nonlocal all_ok
        all_ok &= bool(cond)
        lines.append(("[PASS] " if cond else "[FAIL] ") + msg)
        return cond

    meta_path = out / f"{fig_id}.meta.json"
    if not ok(meta_path.exists(), f"{fig_id}.meta.json 存在"):
        return _finish(out, fig_id, lines, all_ok, quiet)

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    ok(meta.get("type") == type_, f"图型一致 ({type_})")
    for name in (meta["outputs"]["svg"], meta["outputs"]["png"]):
        f = out / name
        ok(f.exists(), f"{name} 存在")
        if f.exists():
            size = f.stat().st_size
            ok(size > 500, f"{name} 非空 ({size} B)")
    for key in COUNT_FIELDS[type_]:
        exp, got = len(data.get(key, [])), meta["counts"].get(key)
        ok(exp == got, f"{key} 数与契约一致 (契约 {exp} = 产物 {got})")
    sha = hashlib.sha256(dp.read_bytes()).hexdigest()
    ok(sha == meta.get("data_sha256"), "数据未在渲染后被改动(非陈旧产物)")
    return _finish(out, fig_id, lines, all_ok, quiet)


def _finish(out, fig_id, lines, all_ok, quiet) -> bool:
    lines.append(f"\nRESULT: {'PASS' if all_ok else 'FAIL'}")
    (out / f"{fig_id}.check.txt").write_text("\n".join(lines) + "\n",
                                             encoding="utf-8")
    if not quiet:
        print("\n".join(lines))
    return all_ok


if __name__ == "__main__":
    import sys
    root = pathlib.Path(__file__).resolve().parent.parent
    fid, ftype = (sys.argv[1:3] + ["fig1", "er"])[:2]
    sys.exit(0 if check(fid, ftype, root / "samples/library/figs" / f"{fid}.json",
                        root / "samples/library/out") else 1)
