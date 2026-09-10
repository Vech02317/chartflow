# -*- coding: utf-8 -*-
"""流程图渲染器:flow.json → out/<id>.svg + <id>.png

节点形状按 GB/T 流程图惯例:起止=圆角框、处理=矩形、判断=菱形、
输入输出=平行四边形、子流程=双边框。
"""
import json
import pathlib

from engine import _common as C

NODE_STYLE = {
    "start": dict(shape="box", style="rounded,filled",
                  fillcolor=C.ACCENT, fontcolor="white"),
    "end": dict(shape="box", style="rounded,filled",
                fillcolor="#3b4a45", fontcolor="white"),
    "process": dict(shape="box", style="rounded,filled", fillcolor="white"),
    "decision": dict(shape="diamond", style="filled", fillcolor="#fdf1dc"),
    "io": dict(shape="parallelogram", style="filled", fillcolor="#eef6f2"),
    "subprocess": dict(shape="box", style="filled", peripheries="2",
                       fillcolor="white"),
}


def render(data_path, fig_id, out_dir) -> dict:
    data = json.loads(pathlib.Path(data_path).read_text(encoding="utf-8"))
    g = C.base_graph(
        data.get("title", ""),
        rankdir=data.get("direction", "TB"),
        node_attr={"shape": "box", "fontname": C.FONT, "fontsize": "14"},
        edge_attr={"fontname": C.FONT, "fontsize": "12", "color": "#4a4a4a",
                   "fontcolor": "#333333", "arrowhead": "vee",
                   "arrowsize": "0.8"},
    )
    for n in data["nodes"]:
        g.node(n["id"], label=n["label"],
               **NODE_STYLE.get(n.get("type", "process"), NODE_STYLE["process"]))
    for e in data["edges"]:
        g.edge(e["from"], e["to"], label=e.get("label", ""))
    return C.emit(g, fig_id, "flow", data_path, data, out_dir)
