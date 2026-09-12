- 表名按 Django 默认命名推断(`library_category` 等),`models.py` 里**没有** `Meta.db_table`。
  实际项目请对着建表语句核。
- `Reader.phone` 源码是 `CharField`,但注释写明"**概念上是多值属性**:一个读者可登记多个号码,
  以逗号分隔(实现时宜拆表)"。本图仍把它当一个普通字段 —— 若你的实现真拆了表,
  这里就该多出一个实体。
- 本图只到"实体 + 联系"一层:`fields` 里只放非外键列,外键都在 `relations.fk_field`。
