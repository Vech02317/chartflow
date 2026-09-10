# -*- coding: utf-8 -*-
"""ER 渲染器:er.json(数据契约实例)→ out/<id>.svg + <id>.png

分工:数据与语义由 json 决定(agent 抽取、人审数据);本文件只负责“画”。
排版交给 dot;密集图不满意时调本文件常量,不要改数据。
"""
import json
import pathlib

from engine import _common as C


def _entity_label(ent: dict) -> str:
    """实体盒子:表头(中文名 + 代码名)+ 每字段一行;主键下划线加粗"""
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


def render(data_path, fig_id, out_dir) -> dict:
    data = json.loads(pathlib.Path(data_path).read_text(encoding="utf-8"))
    g = C.base_graph(data.get("title", ""), rankdir="LR",
                     edge_attr={**_default_edge()})
    for ent in data["entities"]:
        g.node(ent["name"], label=_entity_label(ent))
    for rel in data["relations"]:
        one, many = (x.strip() for x in rel["cardinality"].split(":"))
        g.edge(rel["from"], rel["to"], taillabel=one, headlabel=many,
               label=rel.get("label", ""))
    return C.emit(g, fig_id, "er", data_path, data, out_dir)


def _default_edge() -> dict:
    return {"fontname": C.FONT, "fontsize": "11", "color": C.EDGE,
            "fontcolor": C.EDGE, "arrowhead": "none", "arrowtail": "none",
            "labelfontcolor": "#999999"}
