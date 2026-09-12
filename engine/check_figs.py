# -*- coding: utf-8 -*-
"""自动验收(门禁):产物齐全 / 非空 / 计数一致 / 数据未陈旧 + 版面尺寸预警。

验收规则都写在这里;契约加内容却不重跑,这里就会拦住。
注意:PASS 只证“图与契约一致”,不证“契约与事实一致” —— 后者必须人审。
尺寸只 WARN 不 FAIL:图能画出来就算通过,但插不进论文得让作者知道。

ER 拆模块时,这里额外做两件**只 FAIL**的机器证明(见 _check_modules):
实体没漏没重(分区完整)、关系一条没丢(全覆盖)—— 后者是「绝不静默丢数据」
在拆图场景下的落点。
"""
import hashlib
import json
import pathlib
import re
import sys

# 让 `python3 engine/check_figs.py <id> <type>`(README §7 的用法)也能跑:
# 直接执行脚本时 sys.path[0] 是 engine/,`engine.xxx` 反而导不到。build.py 同此写法。
_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engine._common import COUNT_FIELDS  # noqa: E402

# A4 版心约 470pt × 700pt;缩到 70% 以下文字就难读了
PAGE_W, PAGE_H, MIN_SCALE = 470.0, 700.0, 0.70


def _svg_size(p: pathlib.Path):
    head = p.read_text(encoding="utf-8", errors="ignore")[:800]
    m = re.search(r'width="([\d.]+)pt"\s+height="([\d.]+)pt"', head)
    return (float(m.group(1)), float(m.group(2))) if m else None


def _size_hint(variant, has_compact, has_modules) -> str:
    """超版面时给一句**可执行**的下一步,而不是笼统的“建议拆图”。"""
    if variant.startswith("mod_"):
        return "该模块仍超出 A4 版心 —— 可再细拆(给实体标更细的 module)或精简该模块的实体"
    if variant == "compact" and has_modules:
        return "整体紧凑版本就比模块图宽 —— 插论文请用同目录 <id>_mod_*.svg,本行可忽略"
    if variant == "compact":
        return ("需要按模块拆图:给实体加 module、顶层加 modules 后重跑"
                "(见 README「ER 模块图」/ prompts/extract_er.md)")
    if has_compact:
        return "改用紧凑版式(同目录 <id>_compact.*)"
    return "建议拆图或精简元素"


def _check_modules(data, meta, ok, warnings):
    """ER 拆模块的机器证明 + 两条 schema 表达不了的 WARN。"""
    mods = [o for o in meta["outputs"] if "module" in o]
    if not mods:
        return
    names = "、".join(o["svg"] for o in mods)
    warnings.append(f"[INFO] 模块图 {len(mods)} 张:{names} —— 插论文用它们,不用 _compact")

    # FAIL ① 分区完整:每个实体恰好属一个模块(少了会漏画,重了说明有两份数据)
    owner = {}
    for o in mods:
        for n in o.get("internal", []):
            owner.setdefault(n, []).append(o["module"])
    dup = {n: v for n, v in owner.items() if len(v) > 1}
    gone = [e["name"] for e in data.get("entities", []) if e["name"] not in owner]
    ok(not dup and not gone,
       f"模块分区完整(每实体恰好属一个模块;重复 {dup or '无'},遗漏 {gone or '无'})")

    # FAIL ② 关系全覆盖:所有模块图的 relation_ids 并集 == 全部关系
    # 用原始下标而非 (from,to) —— 平行边(User→Friendship 的「发起」「被加」)
    # 按元组去重就是静默丢数据
    covered = set()
    for o in mods:
        covered |= set(o.get("relation_ids", []))
    want = set(range(len(data.get("relations", []))))
    ok(covered == want,
       f"模块图关系全覆盖(合计 {len(covered)}/{len(want)};漏 {sorted(want - covered) or '无'})")

    # WARN(契约管不了跨数组的取值约束)
    declared = {m["name"] for m in data.get("modules", [])}
    for name in sorted(declared - {o["module"] for o in mods}):
        warnings.append(f"[WARN] 模块 {name} 声明了却没有任何实体 —— "
                        f"检查是不是有实体的 module 写错了")
    for e in data.get("entities", []):
        m = e.get("module")
        if m and m not in declared:
            warnings.append(f"[WARN] 实体 {e['name']} 的 module={m} 不在顶层 modules 里")


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
    has_modules = any("module" in o for o in meta["outputs"])

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
                    warnings.append(
                        f"[WARN] {item['svg']} 版面 {w:.0f}×{h:.0f}pt,"
                        f"按 A4 版心需缩到 {scale*100:.0f}%,文字恐难辨 —— "
                        + _size_hint(variant, has_compact, has_modules))

    _check_modules(data, meta, ok, warnings)

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
    args = sys.argv[1:]
    fid, ftype = (args + ["fig1", "er"])[:2]
    # 第三个参数是工作目录(含 figs/ 与 out/);默认样例
    base = pathlib.Path(args[2]) if len(args) > 2 else _ROOT / "samples/library"
    passed, _ = check(fid, ftype, base / "figs" / f"{fid}.json", base / "out")
    sys.exit(0 if passed else 1)
