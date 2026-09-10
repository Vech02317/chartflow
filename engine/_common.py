# -*- coding: utf-8 -*-
"""渲染器共用件:字体、HTML 转义、图属性、产物落盘与 meta 记账。

meta 里记了数据文件的 sha256 —— 数据改了却没重跑,check_figs 会据此拦住。
"""
import hashlib
import json
import pathlib

import graphviz

FONT = "Noto Sans CJK SC"
ACCENT = "#2ea27f"
EDGE = "#7a7a7a"

# 每类图“数什么”:验收据此比对契约与产物
COUNT_FIELDS = {
    "er": ["entities", "relations"],
    "class": ["classes", "relations"],
    "flow": ["nodes", "edges"],
}


def esc(s) -> str:
    """Graphviz HTML-like 标签转义"""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def base_graph(title, rankdir="TB", node_attr=None, edge_attr=None):
    """建图:统一字体/间距/配色,各渲染器只填内容。"""
    default_node = {"shape": "plaintext", "fontname": FONT, "fontsize": "14"}
    default_edge = {"fontname": FONT, "fontsize": "11", "color": EDGE,
                    "fontcolor": EDGE, "arrowhead": "none", "arrowtail": "none",
                    "labelfontcolor": "#999999"}
    return graphviz.Digraph(
        "fig",
        graph_attr={"rankdir": rankdir, "nodesep": "0.5", "ranksep": "1.1",
                    "bgcolor": "white", "splines": "true", "overlap": "false",
                    "fontname": FONT, "fontsize": "20",
                    "labelloc": "t", "labeljust": "c", "label": title},
        node_attr=node_attr or default_node,
        edge_attr=edge_attr or default_edge,
    )


def emit(g, fig_id, type_, data_path, data, out_dir) -> dict:
    """渲染 SVG+PNG,并写 <id>.meta.json 供验收比对。"""
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for fmt in ("svg", "png"):
        g.format = fmt
        g.render(filename=fig_id, directory=str(out), cleanup=False)

    meta = {
        "fig_id": fig_id,
        "type": type_,
        "title": data.get("title", ""),
        "source": data.get("source", ""),
        "counts": {k: len(data.get(k, [])) for k in COUNT_FIELDS[type_]},
        "data_sha256": hashlib.sha256(
            pathlib.Path(data_path).read_bytes()).hexdigest(),
        "outputs": {"svg": f"{fig_id}.svg", "png": f"{fig_id}.png"},
    }
    (out / f"{fig_id}.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta
