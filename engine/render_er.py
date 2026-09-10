# -*- coding: utf-8 -*-
"""ER 渲染器:er.json → 两种版式(同一份数据)

  <id>.svg/.png          详细版:实体盒子含全部字段、LR 展开,供作者自查做了什么
  <id>_compact.svg/.png  紧凑版:只画实体名与关系、TB 紧凑排版,供插入论文

版式参数经实测选定(work/ 下实验):14 实体 / 21 关系下,
详细版 2001×1704pt,紧凑版 746×541pt(缩到 A4 版心约 63%)。
不用 dot 的 concentrate:它可能合并平行边,而 用户→好友关系 这类
同一对实体的多条语义不同关系(发起/被加)一旦被合并就是静默丢数据。
"""
import json
import pathlib

from engine import _common as C


def _full_label(ent: dict) -> str:
    """详细版实体盒子:表头(中文名 + 代码名)+ 每字段一行;主键下划线加粗"""
    name = C.esc(ent["name"])
    label = C.esc(ent.get("label", ent["name"]))
    rows = [f'<tr><td bgcolor="{C.ACCENT}"><font color="white"><b>{label}</b>'
            f' <font color="#d8f0e8">{name}</font></font></td></tr>']
    for f in ent["fields"]:
        fname = C.esc(f["name"])
        if f.get("pk"):
            fname = f"<u><b>{fname}</b></u>"
        rows.append(f'<tr><td align="left">{fname}　{C.esc(f["label"])}</td></tr>')
    return ('<<table border="1" cellborder="1" cellspacing="0" cellpadding="6">'
            + "".join(rows) + "</table>>")


def _compact_label(ent: dict) -> str:
    """紧凑版实体盒子:只留中文实体名(英文名会显著增宽,论文图不需要)"""
    label = C.esc(ent.get("label", ent["name"]))
    return ('<<table border="0" cellborder="0" cellspacing="0" cellpadding="8">'
            f'<tr><td bgcolor="{C.ACCENT}"><font color="white"><b>{label}</b>'
            "</font></td></tr></table>>")


def _build(data: dict, compact: bool):
    node_attr = {"shape": "plaintext", "fontname": C.FONT,
                 "fontsize": "12" if compact else "14"}
    edge_attr = {"fontname": C.FONT, "fontsize": "10" if compact else "11",
                 "color": C.EDGE, "fontcolor": C.EDGE, "arrowhead": "none",
                 "arrowtail": "none", "labelfontcolor": "#999999"}
    g = C.base_graph(data.get("title", ""),
                     rankdir="TB" if compact else "LR",
                     node_attr=node_attr, edge_attr=edge_attr)
    if compact:
        g.graph_attr.update(nodesep="0.25", ranksep="0.55")
    for ent in data["entities"]:
        g.node(ent["name"],
               label=(_compact_label(ent) if compact else _full_label(ent)))
    for rel in data["relations"]:
        one, many = (x.strip() for x in rel["cardinality"].split(":"))
        g.edge(rel["from"], rel["to"], taillabel=one, headlabel=many,
               label=rel.get("label", ""))
    return g


def render(data_path, fig_id, out_dir) -> dict:
    data = json.loads(pathlib.Path(data_path).read_text(encoding="utf-8"))
    return C.emit_many([("", _build(data, compact=False)),
                        ("_compact", _build(data, compact=True))],
                       fig_id, "er", data_path, data, out_dir)
