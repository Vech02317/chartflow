- `OrderStatus` 枚举**整类没标可见性记号** —— 按 UML 惯例,枚举常量可省略。
  若导师要求标,说一声,这批类一起改。
- `PaymentService` / `OrderRepository` 是接口,方法按惯例标了 `+`;`OrderService` 里
  与之对应的实现成员没画(接口实现不额外连线)。
- 关系类型按成员声明推断,**「组合」与「聚合」的界限最容易错** —— 本图按"生命周期是否
  一致"判(`Order` 与 `OrderItem` 判为组合),请对着源码复核。
- `BaseEntity` 是 `abstract`,字段标 `#`(protected) —— 与源码的 `protected` 修饰符对应。
