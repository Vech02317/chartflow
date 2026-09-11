# -*- coding: utf-8 -*-
"""渲染器共用件:字体、HTML 转义、图属性、产物落盘与 meta 记账。

一份数据可出多种版式(见 emit_many):例如 ER 的「详细版 / 紧凑版」。
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
    "attr": ["attributes"],
}

# 版式说明:渲染器可产出多个 suffix,人类据此挑选(如 ER 紧凑版插论文)
VARIANT_DOC = {
    "full": "详细版 —— 含全部字段,供作者自查",
    "compact": "紧凑版 —— 只画实体名与关系,供插入论文",
}


def esc(s) -> str:
    """Graphviz HTML-like 标签转义"""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def base_graph(title, rankdir="TB", node_attr=None, edge_attr=None,
               engine="dot", fixed_pos=False):
    """建图:统一字体/间距/配色,各渲染器只填内容。

    fixed_pos=True 供「自带布局」的图型用(属性图:坐标由渲染器算好,neato -n 只画不排)。
    此时**不能**设 rankdir/splines/overlap —— 实测 neato 在 -n 下会因为 overlap=false
    去缩放整个布局,把渲染器算好的半径和角度全部打乱。
    """
    default_node = {"shape": "plaintext", "fontname": FONT, "fontsize": "14"}
    default_edge = {"fontname": FONT, "fontsize": "11", "color": EDGE,
                    "fontcolor": EDGE, "arrowhead": "none", "arrowtail": "none",
                    "labelfontcolor": "#999999"}
    ga = {"bgcolor": "white", "fontname": FONT, "fontsize": "20",
          "labelloc": "t", "labeljust": "c", "label": title}
    if not fixed_pos:
        ga.update({"rankdir": rankdir, "nodesep": "0.5", "ranksep": "1.1",
                   "splines": "true", "overlap": "false"})
    return graphviz.Digraph(
        "fig", engine=engine, graph_attr=ga,
        node_attr=node_attr or default_node,
        edge_attr=edge_attr or default_edge,
    )


def emit_many(graphs, fig_id, type_, data_path, data, out_dir,
              render_kw=None) -> dict:
    """渲染多种版式并写一份 meta。

    graphs: [(suffix, graphviz_graph), ...];suffix 为空表示主版式。
    例:ER 传 [("", 详细图), ("_compact", 紧凑图)] → fig1.png + fig1_compact.png

    render_kw 透传给 graphviz 的 render();自带布局的图型(attr)要传
    {"neato_no_op": 1} 才是「只画不排」。
    """
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    outputs = []
    for suffix, g in graphs:
        stem = f"{fig_id}{suffix}"
        for fmt in ("svg", "png"):
            g.format = fmt
            g.render(filename=stem, directory=str(out), cleanup=False,
                     **(render_kw or {}))
        outputs.append({"variant": (suffix or "full").lstrip("_"),
                        "svg": f"{stem}.svg", "png": f"{stem}.png"})

    meta = {
        "fig_id": fig_id,
        "type": type_,
        "title": data.get("title", ""),
        "source": data.get("source", ""),
        "counts": {k: len(data.get(k, [])) for k in COUNT_FIELDS[type_]},
        "data_sha256": hashlib.sha256(
            pathlib.Path(data_path).read_bytes()).hexdigest(),
        "outputs": outputs,
    }
    (out / f"{fig_id}.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def emit(g, fig_id, type_, data_path, data, out_dir, render_kw=None) -> dict:
    """单一版式渲染(类图 / 流程图 / 属性图用)。"""
    return emit_many([("", g)], fig_id, type_, data_path, data, out_dir,
                     render_kw=render_kw)
