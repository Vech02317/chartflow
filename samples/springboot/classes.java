// 订单模块类结构节选 —— 类图抽取源(Java / Spring Boot)。
// 仅数据标本,不需要编译;多个 public 类写在一个文件里只为方便阅读。

@Entity
public abstract class BaseEntity {
    @Id
    protected Long id;
    protected LocalDateTime createdAt;
}

public enum OrderStatus {
    CREATED, PAID, CANCELLED
}

@Entity
public class Order extends BaseEntity {
    private String orderNo;
    private OrderStatus status;
    private List<OrderItem> items = new ArrayList<>();

    public void addItem(OrderItem item) { ... }
    public BigDecimal total() { ... }
    public void cancel() { ... }
}

@Entity
public class OrderItem extends BaseEntity {
    private String sku;
    private int qty;
    private BigDecimal unitPrice;

    public BigDecimal subtotal() { ... }
}

public interface PaymentService {
    boolean pay(Order order);
    boolean refund(Order order);
}

public interface OrderRepository {
    void save(Order order);
    Order findById(Long id);
}

@Service
public class OrderService {
    private final PaymentService payment;
    private final OrderRepository repo;

    public OrderService(PaymentService payment, OrderRepository repo) { ... }

    public Order create(CreateOrderCmd cmd) { ... }
    public void cancel(Long id) { ... }
}
