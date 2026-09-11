# -*- coding: utf-8 -*-
"""属性图渲染器(陈氏 Chen 记法):一个实体一张图 —— 中央矩形实体 + 周围椭圆属性。

记法依据(《数据库系统概论》王珊;Chen 1976):
    实体 = 矩形;属性 = 椭圆,无向边相连;
    主键 = 属性名下加下划线;多值属性 = 双椭圆;派生属性 = 虚线椭圆。

这是本仓库唯一「自带布局」的渲染器:dot/twopi 都做不出「按椭圆宽度分配角度」的星形
(等角摆放时,中文属性名一宽就互相压住)。故用 neato -n(只画不排)、坐标自己算。两遍法:
    pass1  让 Graphviz 实算每个椭圆的宽高 —— 免去自己猜中文字宽;
    pass2  按宽度做角度跨度分配,并在 0~180° 里挑一个让画布最窄的起始角,再渲染。

注意 base_graph(fixed_pos=True) 不能设 overlap —— 实测 neato 在 -n 下会因为
overlap=false 去缩放整个布局,把这里算好的半径和角度全部打乱。

实测(毕设 14 个实体,fontsize 12 / R=150):最宽 381×335pt,14/14 都 100% 适配
A4 版心(470×700pt)。只有 2 个属性的实体不再被拉成竖条 —— 起始角是自动挑的,
不需要像手写脚本那样逐个 angle_override。
"""
import json
import math
import pathlib

from engine import _common as C

BASE_R = 150.0    # 椭圆中心到实体中心的半径(点);属性又多又宽时自动放大
GAP = 14.0        # 相邻椭圆之间的最小弧长(点)
ATTR_FS = 12
ENTITY_FS = 14
ROT_STEP = 3      # 挑起始角时的试探步长(度)


def _attr_label(attr):
    """属性椭圆的 label 与额外 node 属性。主键下划线要用 raw HTML(双层尖括号)。"""
    text = C.esc(attr["label"])
    kind = attr.get("kind", "normal")
    if kind == "pk":
        return f"<<u>{text}</u>>", {}
    if kind == "multi":
        return text, {"peripheries": "2"}
    if kind == "derived":
        return text, {"style": "dashed"}
    return text, {}


def _build(data, positions):
    ent = data["entity"]
    g = C.base_graph(data.get("title", ""), engine="neato", fixed_pos=True)
    g.attr("node", fontname=C.FONT, fontsize=str(ATTR_FS), shape="ellipse")
    g.attr("edge", arrowhead="none", color=C.EDGE)
    g.node("__ent__", C.esc(ent["label"]), shape="box", fontsize=str(ENTITY_FS),
           penwidth="2", pos="0,0!")
    for i, attr in enumerate(data["attributes"]):
        label, extra = _attr_label(attr)
        x, y = positions[i]
        g.node(f"a{i}", label, pos=f"{x:.1f},{y:.1f}!", **extra)
        g.edge("__ent__", f"a{i}")
    return g


def _sizes(g):
    """pass1:让 Graphviz 报出每个节点的真实宽高(点)。尺寸与坐标无关,故位置随便给。"""
    plain = g.pipe(format="plain", neato_no_op=1, encoding="utf-8")
    out = {}
    for line in plain.splitlines():
        if line.startswith("node"):
            p = line.split()
            out[p[1]] = (float(p[4]) * 72.0, float(p[5]) * 72.0)
    return out


def _angles(widths, radius):
    """角度跨度分配:每个椭圆按「弧长≈自身宽度」占角,余量平均分成间隙。"""
    n = len(widths)
    sizes = [w / radius for w in widths]
    free = max(2 * math.pi - sum(sizes), 0.0)
    gap = free / n if n > 1 else 0.0
    angs, cur = [], -math.pi / 2.0
    for s in sizes:
        angs.append(cur + s / 2.0)
        cur += s + gap
    return angs


def _bbox(angs, radius, halfs, ent_half, delta):
    xs = [-ent_half[0], ent_half[0]]
    ys = [-ent_half[1], ent_half[1]]
    for a, (hw, hh) in zip(angs, halfs):
        x, y = radius * math.cos(a + delta), radius * math.sin(a + delta)
        xs += [x - hw, x + hw]
        ys += [y - hh, y + hh]
    return max(xs) - min(xs), max(ys) - min(ys)


def _layout(data, sizes):
    """算出各属性椭圆中心坐标:半径 → 角度跨度分配 → 挑最窄的起始角。"""
    n = len(data["attributes"])
    ids = [f"a{i}" for i in range(n)]
    ws = [sizes[k][0] for k in ids]
    halfs = [(sizes[k][0] / 2.0, sizes[k][1] / 2.0) for k in ids]
    ent_half = (sizes["__ent__"][0] / 2.0, sizes["__ent__"][1] / 2.0)
    # 半径下限:所有椭圆宽度 + 间隙加起来能绕满一圈;再留 12% 余量
    radius = max(BASE_R, (sum(ws) + GAP * n) / (2 * math.pi) * 1.12)
    angs = _angles(ws, radius)

    best = None
    for deg in range(0, 180, ROT_STEP):        # 转 180° 结果一样,扫半个圆就够
        d = math.radians(deg)
        w, h = _bbox(angs, radius, halfs, ent_half, d)
        if best is None or (w, h) < best[0]:   # 先压宽度,再压高度
            best = ((w, h), d)
    delta = best[1]
    return [(radius * math.cos(a + delta), radius * math.sin(a + delta))
            for a in angs]


def render(data_path, fig_id, out_dir) -> dict:
    data = json.loads(pathlib.Path(data_path).read_text(encoding="utf-8"))
    n = len(data["attributes"])
    far = [(3000.0 * math.cos(2 * math.pi * i / n),
            3000.0 * math.sin(2 * math.pi * i / n)) for i in range(n)]
    sizes = _sizes(_build(data, far))                 # pass1:量尺寸
    if not all(f"a{i}" in sizes for i in range(n)) or "__ent__" not in sizes:
        raise RuntimeError("属性图:Graphviz 未回报节点尺寸,无法布局")
    g = _build(data, _layout(data, sizes))            # pass2:按算好的坐标出图
    return C.emit(g, fig_id, "attr", data_path, data, out_dir,
                  render_kw={"neato_no_op": 1})
