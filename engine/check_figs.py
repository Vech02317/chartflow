# -*- coding: utf-8 -*-
"""自动验收(门禁):产物齐全 / 非空 / 计数一致 / 数据未陈旧 + 版面尺寸预警。

验收规则都写在这里;契约加内容却不重跑,这里就会拦住。
注意:PASS 只证“图与契约一致”,不证“契约与事实一致” —— 后者必须人审。
尺寸只 WARN 不 FAIL:图能画出来就算通过,但插不进论文得让作者知道。
"""
import hashlib
import json
import pathlib
import re

from engine._common import COUNT_FIELDS

# A4 版心约 470pt × 700pt;缩到 70% 以下文字就难读了
PAGE_W, PAGE_H, MIN_SCALE = 470.0, 700.0, 0.70


def _svg_size(p: pathlib.Path):
    head = p.read_text(encoding="utf-8", errors="ignore")[:800]
    m = re.search(r'width="([\d.]+)pt"\s+height="([\d.]+)pt"', head)
    return (float(m.group(1)), float(m.group(2))) if m else None


def check(fig_id, type_, data_path, out_dir, quiet=False):
    """返回 (是否通过, 预警列表)。预警不否决通过,但必须让调用方看得见。"""
    out = pathlib.Path(out_dir)
    dp = pathlib.Path(data_path)
    data = json.loads(dp.read_text(encoding="utf-8"))
    lines, warnings, all_ok = [], [], True

    def ok(cond, msg):
        nonlocal all_ok
        all_ok &= bool(cond)
        lines.append(("[PASS] " if cond else "[FAIL] ") + msg)
        return cond

    meta_path = out / f"{fig_id}.meta.json"
    if not ok(meta_path.exists(), f"{fig_id}.meta.json 存在"):
        _finish(out, fig_id, lines, warnings, all_ok, quiet)
        return all_ok, warnings

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    ok(meta.get("type") == type_, f"图型一致 ({type_})")
    has_compact = any(o.get("variant") == "compact" for o in meta["outputs"])

    for item in meta["outputs"]:
        variant = item.get("variant", "full")
        for name in (item["svg"], item["png"]):
            f = out / name
            ok(f.exists(), f"{name} 存在")
            if f.exists():
                size = f.stat().st_size
                ok(size > 500, f"{name} 非空 ({size} B)")
        svg = out / item["svg"]
        if svg.exists():
            dim = _svg_size(svg)
            if dim:
                w, h = dim
                scale = min(PAGE_W / w, PAGE_H / h, 1.0)
                if scale < MIN_SCALE:
                    if has_compact and variant != "compact":
                        hint = "改用紧凑版式(同目录 <id>_compact.*)"
                    elif variant == "compact":
                        hint = "已是最紧凑版式,建议按模块拆图"
                    else:
                        hint = "建议拆图或精简元素"
                    warnings.append(
                        f"[WARN] {item['svg']} 版面 {w:.0f}×{h:.0f}pt,"
                        f"按 A4 版心需缩到 {scale*100:.0f}%,文字恐难辨 —— {hint}")

    for key in COUNT_FIELDS[type_]:
        exp, got = len(data.get(key, [])), meta["counts"].get(key)
        ok(exp == got, f"{key} 数与契约一致 (契约 {exp} = 产物 {got})")
    sha = hashlib.sha256(dp.read_bytes()).hexdigest()
    ok(sha == meta.get("data_sha256"), "数据未在渲染后被改动(非陈旧产物)")
    _finish(out, fig_id, lines, warnings, all_ok, quiet)
    return all_ok, warnings


def _finish(out, fig_id, lines, warnings, all_ok, quiet):
    lines.extend(warnings)
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
    passed, _ = check(fid, ftype,
                      root / "samples/library/figs" / f"{fid}.json",
                      root / "samples/library/out")
    sys.exit(0 if passed else 1)
