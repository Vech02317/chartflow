# -*- coding: utf-8 -*-
"""类图渲染器:class.json → out/<id>.svg + <id>.png

UML 记号约定(与 prompts/extract_class.md 对齐):
  继承 = 空心三角箭头指向父类;组合 = 实心菱形在“整体”端;聚合 = 空心菱形在“整体”端;
  关联 = 开放箭头;依赖 = 虚线开放箭头。
"""
import json
import pathlib

from engine import _common as C

STEREO = {"class": "", "abstract": "«abstract»",
          "interface": "«interface»", "enum": "«enum»"}

REL_STYLE = {
    "继承": dict(style="solid", arrowhead="onormal", arrowtail="none"),
    "组合": dict(style="solid", arrowhead="vee", arrowtail="diamond"),
    "聚合": dict(style="solid", arrowhead="vee", arrowtail="odiamond"),
    "关联": dict(style="solid", arrowhead="vee", arrowtail="none"),
    "依赖": dict(style="dashed", arrowhead="vee", arrowtail="none"),
}


def _class_label(cls: dict) -> str:
    name = C.esc(cls["name"])
    label = C.esc(cls.get("label", ""))
    head = f"<b>{label or name}</b>" + (f" · {name}" if label else "")
    stereo = STEREO.get(cls.get("stereotype", "class"), "")
    if stereo:
        head = f'<font point-size="11">{stereo}</font><br/>{head}'
    rows = [f'<tr><td bgcolor="{C.ACCENT}"><font color="white">{head}</font></td></tr>']
    for key in ("attributes", "methods"):
        items = cls.get(key) or []
        if items:
            rows.append('<tr><td align="left">'
                        + "<br/>".join(C.esc(i) for i in items) + "</td></tr>")
    return ('<<table border="1" cellborder="1" cellspacing="0" cellpadding="6">'
            + "".join(rows) + "</table>>")


def render(data_path, fig_id, out_dir) -> dict:
    data = json.loads(pathlib.Path(data_path).read_text(encoding="utf-8"))
    g = C.base_graph(data.get("title", ""), rankdir="TB")
    for cls in data["classes"]:
        g.node(cls["name"], label=_class_label(cls))
    for rel in data["relations"]:
        kw = dict(REL_STYLE[rel["kind"]])
        car = rel.get("cardinality")
        if car:
            one, many = (x.strip() for x in car.split(":"))
            kw["taillabel"], kw["headlabel"] = one, many
        g.edge(rel["from"], rel["to"], label=rel.get("label", ""), **kw)
    return C.emit(g, fig_id, "class", data_path, data, out_dir)
