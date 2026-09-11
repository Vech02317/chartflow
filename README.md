# chartflow —— 工科论文产图流水线(给 AI 的操作手册)

把论文与项目源码交给 agent,产出**可重跑、风格统一、自动验收**的 ER 图 / 实体属性图 / 类图 / 流程图。

本文件是**程序的一部分**:任何 agent(codex / deepseek harness / Claude Code)按本文操作即可。

---

## 1. 它是什么

三角色分工,越界即错:

| 角色 | 做什么 | 不做什么 |
|---|---|---|
| **Agent(你)** | 读论文与源码、产出清单与 JSON、跑脚本、改产物 | 不决定论文该有哪些图(由人拍板);不手写绘图代码 |
| **确定性引擎**(本仓库脚本) | 校验 / 渲染 / 验收 | 不含任何 LLM;同输入必同输出 |
| **人类** | 交材料、确认《出图清单》、审数据、挑图的毛病 | 不写代码、不装环境(环境由你代装) |

**一句话**:你负责"读懂",脚本负责"画对",人负责"拍板"。

## 2. 目录

```
contract/   5 份 JSON Schema —— 全部数据的唯一标准
prompts/    5 份抽取提示词 —— 你的工作说明书
engine/     渲染器(er/attr/class/flow)+ 共用件 + 验收器
doctor.py   环境自检        plan.py   校验《出图清单》
build.py    逐图执行流水线    samples/  合成样例(可照抄格式)
使用说明.md  给人类的说明书(不用读)
```

## 3. 三条铁律

1. **第一产出是清单,不是图**。先产出《出图清单》交人类确认,确认后才逐图执行。跳过这一步 = 图会整整齐齐地错。
2. **验收 PASS ≠ 正确**。`build.py` 的 PASS 只证明"图与契约一致",不证明"契约与事实一致"。数据对不对,由人(对着源码/建表语句)审。
3. **不编造**。源码里没有的字段、正文里没写的步骤,一律不写进 JSON;拿不准的**单列"待确认"**回报给人类。

## 4. 快速开始(三步)

```bash
python3 doctor.py            # 1. 环境自检;缺什么按打印的命令装(可能需 sudo,先问人类)
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # 首次用项目内 venv
python3 plan.py  <plan.json> # 2. 校验清单
python3 build.py <plan.json> # 3. 逐图:校验 → 渲染 → 验收
```

自测(用仓库自带样例,先确认环境真的能用):

```bash
.venv/bin/python doctor.py
.venv/bin/python plan.py  samples/library/plan.json
.venv/bin/python build.py samples/library/plan.json    # 期望:4/4 通过 —— RESULT: PASS
```

## 5. 完整流程(对一份真实论文)

1. **读材料** —— 接收论文全文 + 部分项目源码。论文很长时**不要通读**:先看目录,按章节定位。
2. **出清单** —— 按 `prompts/make_plan.md` 产出 `plan.json`(章节 → 图型 → 源材料 → 图题),保存到论文工作目录。**停下来请人确认**。
3. **逐图抽取** —— 对每条 `status: todo` 的图,按 `prompts/extract_<type>.md` 产出 `figs/<id>.json`。
   - `er` / `attr` / `class`(都以源码为准)优先;`flow`(正文描述,模糊度最高)放最后。
   - **只喂相关片段**:ER 只喂 models/建表语句,flow 只喂那一两段业务描述,**不要喂全文**。
4. **渲染+验收** —— 跑 `build.py`。失败就按提示修 JSON 重跑(渲染永远可重跑,不必手工调图)。
5. **交付** —— 产物在 `out/`:每图 `.svg`(矢量,可放大)/ `.png` / `.meta.json`(记账)/ `.check.txt`(验收详情)。把图与"待确认"清单一起交人类。

### ER 图出两版(同一份数据)

| 文件 | 版式 | 用途 |
|---|---|---|
| `<id>.png` / `.svg` | **详细版**:实体盒子含全部字段,LR 展开 | 给作者自查"我到底建了什么" |
| `<id>_compact.png` / `.svg` | **紧凑版**:只画实体名与关系,TB 紧凑 | **插入论文**(A4 友好) |

两版都由同一份 `figs/<id>.json` 渲染,数据只改一处。**插论文优先用紧凑版**;
紧凑版仍放不下时(见下),按模块拆图,而不是硬缩。

### 实体属性图(Chen 记法)

整体 ER 图说"有哪些实体、怎么联系",属性图说"单个实体内部有哪些属性"。两者互补,
论文里常都要 —— 出不出按 `prompts/make_plan.md` 的规则定,不要硬加。

**一张图只画一个实体**:几个实体就出几条 `attr` 记录、几张图,不要把多个实体塞一张。
记法按 Chen(陈氏)规范:

| 属性类型 | `kind` | 画法 |
|---|---|---|
| 主键 | `pk` | 椭圆内属性名**加下划线**(有且只有一个) |
| 多值属性 | `multi` | **双椭圆**(如"联系电话""所属分类") |
| 派生属性 | `derived` | **虚线椭圆**(由别的属性算出、不单独存) |
| 普通属性 | `normal` | 普通椭圆(默认,不写 `kind` 就是它) |

**外键会画成属性**(label 取源码 `verbose_name`,如"所属书")—— 这是跟随毕设惯例。
它严格说属于"联系"而非"属性",所以 `extract_attr.md` 要求 agent **必须**把画了哪些外键
列进"待确认",由人决定删不删。

实测(毕设 14 个实体,最多的 10 个属性):出图 302~376pt 见方,**14/14 都 100% 适配
A4 版心**,不必缩放,可以两张并排插。

### 版面尺寸门禁

验收会量 SVG 画布尺寸。按 A4 版心(约 470×700pt)需缩到 **70% 以下**时给出
`[WARN]`,提示改用紧凑版或拆图 —— **只警告不否决**(图画出来了就算通过,
但插不进论文得让作者知道)。实测参考:14 实体 / 21 关系的 ER,
详细版 2001×1704pt(需缩 23%),紧凑版 746×541pt(需缩 63%)。

## 6. 契约(数据结构,必须严格符合)

| 文件 | 用于 | 关键约束 |
|---|---|---|
| `contract/plan.schema.json` | 出图清单 | `source` 必须具体到文件/章节,禁止"全文" |
| `contract/er.schema.json` | ER 图 | `fields` 只放非外键列;外键进 `relation.fk_field`;`from` 是"一"侧 |
| `contract/attr.schema.json` | 实体属性图 | **一张图一个实体**;`attributes` 里有且只有一个 `kind: "pk"` |
| `contract/class.schema.json` | 类图 | 成员只写名称/签名;省略 getter/setter 样板;类数 ≤ 15 |
| `contract/flow.schema.json` | 流程图 | 单 `start` 单 `end`;`decision` 每条出边必须带 `label` |

## 7. 命令手册

| 命令 | 作用 | 退出码 |
|---|---|---|
| `python3 doctor.py` | 自检 python/graphviz/中文字体,缺啥打印安装命令 | 0=READY |
| `python3 plan.py <plan.json>` | 校验清单结构 + 语义(id 唯一、source 具体、skip 有原因) | 0=PASS |
| `python3 build.py <plan.json>` | 逐图校验→渲染→验收,产物落 `out/` | 0=全通过 |
| `python3 engine/check_figs.py <id> <type>` | 单独复验某张图 | 0=PASS |

## 8. 失败排查

| 现象 | 原因 / 处理 |
|---|---|
| 中文显示成方框 | 缺 CJK 字体。Linux:`sudo apt-get install -y fonts-noto-cjk`(需 sudo,先问人) |
| `dot: command not found` | 缺 graphviz。Linux `apt-get install graphviz` / Windows `winget install Graphviz.Graphviz` |
| `json 不符合契约` | 按报错字段名改 JSON;契约即标准,不要绕过 |
| 验收 FAIL「数据未在渲染后被改动」 | 改了 `figs/<id>.json` 但没重跑 → 重跑 `build.py` |
| `[WARN] 版面 … 需缩到 xx%` | 图太宽/太高插不进 A4。ER 优先用紧凑版;仍超就按模块拆图 |
| 流程图/ER 形状与标准不符 | 形状定义在 `engine/render_*.py` 顶部字典;改前先查规范(Chen vs Crow's Foot / GB/T 1526) |
| 图太挤/太长 | 调 `engine/render_*.py` 顶部的布局常量(`rankdir`、间距),**不要动数据** |
| 实体/类/步骤太多(dot 布局崩) | 精简:只画核心对象,把省略项写进给人类的"待确认" |

## 9. 扩展新图型(如用例图)

1. 加 `contract/<type>.schema.json`
2. 加 `prompts/extract_<type>.md`
3. 加 `engine/render_<type>.py`(照抄 `render_class.py` 骨架,用 `_common.base_graph` / `emit`)。
   若新图型要**自己算坐标**(像 `attr` 那样):用 `base_graph(..., engine="neato", fixed_pos=True)`
   + `emit(..., render_kw={"neato_no_op": 1})`,并且**千万别设 `overlap`** ——
   实测 neato 在 `-n` 下会因为 `overlap=false` 去缩放整个布局,把你算好的坐标全部打乱。
4. `engine/_common.py` 的 `COUNT_FIELDS` 注册计数键
5. `build.py` 的 `RENDERERS` 注册模块名

主干代码不需要任何改动。
