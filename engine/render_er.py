# -*- coding: utf-8 -*-
"""ER 渲染器:把 er.json(数据契约实例)确定性渲染成 out/er.svg + out/er.png。

分工:数据与语义由 er.json 决定(LLM 抽取、人审数据);本文件只负责“画”。
排版交给 dot;密集图不满意时优先调本文件 LAYOUT / _entity_label,不要改数据。
"""
import json
import pathlib

import graphviz

FONT = "Noto Sans CJK SC"
ACCENT = "#2ea27f"      # 主色:青绿(与登录门面同源)
EDGE = "#7a7a7a"
GRAPH_ATTR = {
    "rankdir": "LR", "nodesep": "0.5", "ranksep": "1.1",
    "bgcolor": "white", "splines": "true", "overlap": "false",
    "fontname": FONT, "fontsize": "20",
    "labelloc": "t", "labeljust": "c",
}
NODE_ATTR = {"shape": "plaintext", "fontname": FONT, "fontsize": "14"}
EDGE_ATTR = {"fontname": FONT, "fontsize": "11",
             "color": EDGE, "fontcolor": EDGE,
             "arrowhead": "none", "arrowtail": "none",
             "labelfontcolor": "#999999"}


def _esc(s) -> str:
    """Graphviz HTML-like 标签转义"""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _entity_label(ent: dict) -> str:
    """实体盒子:表头(中文名 + 代码名)+ 每字段一行;主键下划线加粗"""
    name = _esc(ent["name"])
    label = _esc(ent.get("label", ent["name"]))
    rows = [f'<tr><td bgcolor="{ACCENT}"><font color="white"><b>{label}</b>'
            f' <font color="#d8f0e8">{name}</font></font></td></tr>']
    for f in ent["fields"]:
        fname = _esc(f["name"])
        if f.get("pk"):
            fname = f"<u><b>{fname}</b></u>"
        rows.append(f'<tr><td align="left">{fname}　{_esc(f["label"])}</td></tr>')
    return ('<<table border="1" cellborder="1" cellspacing="0" cellpadding="6">'
            + "".join(rows) + "</table>>")


def render(er_path, out_dir) -> dict:
    """渲染 er.json → out/er.{svg,png},并写 out/er.meta.json 供验收比对。"""
    er_path = pathlib.Path(er_path)
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data = json.loads(er_path.read_text(encoding="utf-8"))

    g = graphviz.Digraph("er",
                         graph_attr={**GRAPH_ATTR, "label": data.get("title", "")},
                         node_attr=NODE_ATTR, edge_attr=EDGE_ATTR)
    for ent in data["entities"]:
        g.node(ent["name"], label=_entity_label(ent))
    for rel in data["relations"]:
        one, many = (x.strip() for x in rel["cardinality"].split(":"))
        # from 是“一”侧 → 基数标注靠尾;to 是“多”侧 → 基数标注靠头
        g.edge(rel["from"], rel["to"], taillabel=one, headlabel=many,
               label=rel.get("label", ""))

    for fmt in ("svg", "png"):
        g.format = fmt
        g.render(filename="er", directory=str(out_dir), cleanup=False)

    meta = {
        "title": data.get("title", ""),
        "source": data.get("source", ""),
        "entities": len(data["entities"]),
        "relations": len(data["relations"]),
        "outputs": {"svg": "er.svg", "png": "er.png"},
    }
    (out_dir / "er.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


if __name__ == "__main__":
    # 单独调试: python3 engine/render_er.py
    import sys
    root = pathlib.Path(__file__).resolve().parent.parent
    render(root / "samples/library/er.json", root / "out")
    print("rendered ->", root / "out")
