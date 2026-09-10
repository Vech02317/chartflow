# 任务:从源码抽取实体关系 → `figs/<id>.json`(ER 图)

## 输入(按优先级取其一)
1. 实体类源码(Django / SQLAlchemy / JPA 等)
2. 建表 SQL(DDL)
3. 数据字典文档

## 输出
一个 JSON 文件,保存为 **`figs/<图清单里的 id>.json`**,严格符合 `contract/er.schema.json`。
**只输出 JSON 内容**,不要解释。

## 抽取规则
1. **源码为准,正文只补充**:字段名、类型、外键只从代码或 SQL 取;论文正文与代码冲突时**以代码为准**。
2. `entity.fields` **只放非外键列**(含主键);外键写进 `relation.fk_field`,不要重复成字段。
3. 关系方向:`from` 是**"一"侧**,`to` 是**"多"侧**,`cardinality` 写 `1:N`。
4. `name` 用代码里的原名(如 `BorrowRecord`);`label` 用中文(取 `verbose_name` / SQL comment;没有就意译)。
5. **不编造字段**。有拿不准的字段或关系,**不要写进 JSON**,而是在给人类的回复里单列一条"待确认"。
6. 纯连接表(只有两个外键、无业务字段)——省略成一条 `N:M` 关系,不单列实体。
7. 主键字段带 `"pk": true`(Django 的 `id` 即使没显式声明也算)。

## 自检
- [ ] 每个 `entity.name` 都是源码里真实存在的类名/表名
- [ ] 每条 `relation.from` / `relation.to` 都能在 `entities` 里找到
- [ ] 每个实体有且仅有一个主键
- [ ] 没有把外键列写进 `fields`

## 完成后
把"待确认"清单回报给人类(这一步不能省:验收脚本只能证明图和契约一致,证明不了契约和事实一致)。
