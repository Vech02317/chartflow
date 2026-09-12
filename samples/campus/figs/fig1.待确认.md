- **模块划分依据是三个源文件各自的 app 名**(accounts / activity / venue)。源码里没有
  `Meta.db_table`、也没有带 app 前缀的外键字符串可以交叉验证 —— **请核对这个划分**。
- **两条可空外键**(`Enrollment.venue_slot`、`VenueEquipment.activity`,都是 `null=True`)
  在图上按 `1:N` 画 —— 契约的 `cardinality` 只有 `1:N / N:1 / 1:1 / N:M`,**表达不了 `0..1`**。
- `ActivityTag.activities` 是多对多,按规则收敛成一条 `N:M`,**自动中间表未单列**。
- 表名全部按 Django 默认命名推断(`accounts_user` 等),源码里没有 `Meta.db_table`。
- 关系的中文标签部分取 `verbose_name` 去指代后缀,部分是意译(如"配备""划分")——
  若论文有固定叫法,告诉我统一替换。
