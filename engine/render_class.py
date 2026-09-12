# -*- coding: utf-8 -*-
"""类图渲染器:class.json → out/<id>.svg + <id>.png

UML 记号约定(与 prompts/extract_class.md 对齐):
  继承 = 空心三角箭头指向父类;组合 = 实心菱形在“整体”端;聚合 = 空心菱形在“整体”端;
  关联 = 开放箭头;依赖 = 虚线开放箭头;
  可见性 = 成员名前缀 + 公开 / - 私有 / # 保护 / ~ 包内,排成左列对齐。

可见性由**数据**决定,渲染器不猜语言:成员串带记号就画记号列,整类都不带
就原样竖排(Python 源码没有强制可见性,标出来是假精度 —— 见 extract_class.md)。
"""
import json
import pathlib

from engine import _common as C

STEREO = {"class": "", "abstract": "«abstract»",
          "interface": "«interface»", "enum": "«enum»"}

VIS = ("+", "-", "#", "~")   # UML 2.5 可见性记号


def _split_member(s: str):
    """拆出可见性记号:'+ name' → ('+', 'name');无记号 → ('', 原串)。

    记号后必须跟一个空格 —— 与 contract/class.schema.json 的 pattern 一致,两边不能松。
    Python 的 `__init__` / `_cache` 首字符不在记号集里,不会被误拆。
    """
    if len(s) > 1 and s[0] in VIS and s[1].isspace():
        return s[0], s[2:].strip()
    return "", s


def _members(items) -> str:
    """成员区块。整类只要有一个带记号,就统一排成「记号列 + 名称列」——
    必须整类一致,否则同一格里有的缩进有的不缩进,记号对不齐;
    一个都不带则原样竖排,不塞空列。

    两处坑(都实测过):
      - 用 `<br/>` 拼多行,Graphviz 会**居中**,`align="left"` 压不住 ——
        同一个类里属性左对齐、方法居中。必须包一层单列嵌套表才会左对齐。
      - **不要**给记号单独开一列。HTML 表格会把外层单元格的富余宽度分给窄列:
        表头比成员宽多少,记号列就胖多少。实测同一张图里间距从 14pt 到 55pt 不等
        (属性和方法是两张表,各自被撑开的程度不同),`fixedsize` 也压不住。
        故记号直接拼进成员串,整行一个文本对象 —— 代价是 `-` 比 `+` 窄约 3pt,
        记号会有几 pt 抖动,换取列宽稳定、不随表头变形。
    """
    marked = any(_split_member(i)[0] for i in items)
    out = ['<table border="0" cellborder="0" cellspacing="0" cellpadding="0">']
    for i in items:
        mark, text = _split_member(i)
        cell = f"{mark}&#160;{C.esc(text)}" if (marked and mark) else C.esc(i)
        out.append(f'<tr><td align="left">{cell}</td></tr>')
    out.append("</table>")
    return "".join(out)

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
            rows.append('<tr><td align="left">' + _members(items) + "</td></tr>")
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
