# -*- coding: utf-8 -*-
"""ER 渲染器:er.json → 两种版式(+ 实体多时的模块图),同一份数据

  <id>.svg/.png             详细版:实体盒子含全部字段、LR 展开,供作者自查做了什么
  <id>_compact.svg/.png     紧凑版:只画实体名与关系、TB 紧凑排版,供插入论文
  <id>_mod_<模块>.svg/.png  模块图(仅当数据里写了 modules):本模块实体 + 其他模块的
                            虚线引用框,紧凑版塞不进 A4 时用它

版式参数经实测选定(work/ 下实验):14 实体 / 21 关系下,
详细版 2001×1704pt,紧凑版 746×541pt(缩到 A4 版心约 63%)。
不用 dot 的 concentrate:它可能合并平行边,而 用户→好友关系 这类
同一对实体的多条语义不同关系(发起/被加)一旦被合并就是静默丢数据。

模块图不是「第二份数据」而是同一份数据的第三种版式:整体图与模块图都由这一个
JSON 渲染,所以结构上不可能出现「改了整体图忘了改模块图」的漂移。
"""
import json
import pathlib

from engine import _common as C

# 引用框:别的模块的实体,只示意、不列字段。
# 用 box 而不是 plaintext —— plaintext 不画边界,style="dashed" 无处可施。
# 刻意不加 rounded:圆角在本仓库是 GB/T 1526 端点符的专用形状(render_flow),
# 借用会造成记号冲突。
_REF = dict(shape="box", style="dashed", color=C.REF_EDGE,
            fontcolor=C.REF_TEXT, penwidth="1", fontsize="12")

_REF_LEGEND = "虚线框 = 其他模块的实体(只示意,不列字段)"


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


def _slice(data: dict, module: str):
    """按模块切出:本模块实体名 / 要画的实体名 / 要画的关系下标。

    **关系归 `to` 端(外键所在端、"多"侧)所属的模块。** 不能按「任一端在本模块」
    过滤 —— `User` 常自成模块又是全图枢纽,按「任一端」会把每一条 User 发出的
    关系都判给它,整张图被拖进来(实测 14 实体时 accounts 模块被撑到 983pt),
    与拆图的目的正好相反。按 to 端切则每条关系**恰好归一个模块**(实测 21 条
    无重复无遗漏),且这条规则可对着源码核:Django 的外键字段就长在 to 端那张表上。

    `shown` 只收「参与本模块关系」的外部实体 —— 与本模块无关的外部实体不留漂浮空框。
    """
    internal = {e["name"] for e in data["entities"] if e.get("module") == module}
    idx = [i for i, r in enumerate(data["relations"]) if r["to"] in internal]
    shown = internal | {data["relations"][i]["from"] for i in idx}
    return internal, shown, idx


def _graph_label(data: dict, module=None) -> str:
    """图题。模块图用 modules[].title(由抽取者写明,渲染器不拼中文),
    并在图题下印一行图例 —— 不印的话论文读者看不懂虚线框是什么意思。"""
    if module is None:
        return data.get("title", "")
    m = next(x for x in data["modules"] if x["name"] == module)
    return (f'<{C.esc(m["title"])}<br/>'
            f'<font point-size="10" color="{C.REF_TEXT}">{_REF_LEGEND}</font>>')


def _build(data: dict, compact: bool, module=None):
    node_attr = {"shape": "plaintext", "fontname": C.FONT,
                 "fontsize": "12" if compact else "14"}
    edge_attr = {"fontname": C.FONT, "fontsize": "10" if compact else "11",
                 "color": C.EDGE, "fontcolor": C.EDGE, "arrowhead": "none",
                 "arrowtail": "none", "labelfontcolor": "#999999"}
    g = C.base_graph(_graph_label(data, module),
                     rankdir="TB" if compact else "LR",
                     node_attr=node_attr, edge_attr=edge_attr)
    if compact:
        g.graph_attr.update(nodesep="0.25", ranksep="0.55")

    if module is None:
        rels = data["relations"]
        for ent in data["entities"]:
            g.node(ent["name"],
                   label=(_compact_label(ent) if compact else _full_label(ent)))
    else:
        internal, shown, idx = _slice(data, module)
        rels = [data["relations"][i] for i in idx]
        for ent in data["entities"]:
            if ent["name"] not in shown:
                continue
            if ent["name"] in internal:
                g.node(ent["name"],
                       label=(_compact_label(ent) if compact else _full_label(ent)))
            else:
                # 边不跟着画虚:读者要读的是基数,虚边会把 1/N 读成不确定。
                # 虚线的语义只给「这个盒子在别的模块」。
                g.node(ent["name"], label=C.esc(ent.get("label", ent["name"])),
                       **_REF)

    for rel in rels:
        one, many = (x.strip() for x in rel["cardinality"].split(":"))
        g.edge(rel["from"], rel["to"], taillabel=one, headlabel=many,
               label=rel.get("label", ""))
    return g


def render(data_path, fig_id, out_dir) -> dict:
    data = json.loads(pathlib.Path(data_path).read_text(encoding="utf-8"))
    graphs = [("", _build(data, compact=False)),
              ("_compact", _build(data, compact=True))]
    for m in data.get("modules", []):
        name = m["name"]
        internal, shown, idx = _slice(data, name)
        graphs.append((f"_mod_{name}", _build(data, compact=True, module=name),
                       {"module": name,
                        "label": m.get("label", name),
                        "internal": sorted(internal),
                        "external": sorted(shown - internal),
                        # 必须是原始下标:User→Friendship 有两条语义不同的平行边,
                        # 按 (from,to) 去重就是静默丢数据
                        "relation_ids": idx}))
    return C.emit_many(graphs, fig_id, "er", data_path, data, out_dir)
