import asyncio
import json
import logging
import sqlite3
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

# --- Cấu hình và Logging ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Cấu hình mặc định
DEFAULT_CONFIG = {
    "tax_rates": {"VAT_VIETNAM": 0.10, "GST_US": 0.05},
    "payment_methods": ["credit_card", "bank_transfer", "crypto"],
    "currencies": ["USD", "VND", "EUR"],
}

# --- Dataclasses ---


@dataclass
class Invoice:
    """Cấu trúc hóa đơn."""

    invoice_id: str
    customer_id: str
    items: List[Dict[str, Any]]
    subtotal: float
    taxes: float
    total: float
    status: str = "draft"
    due_date: str = ""


@dataclass
class Payment:
    """Cấu trúc thanh toán."""

    payment_id: str
    invoice_id: str
    amount: float
    method: str
    status: str = "pending"
    timestamp: str = ""
    transaction_id: str = ""


@dataclass
class BillingRecord:
    """Bản ghi billing."""

    record_id: str
    customer_id: str
    service_type: str
    usage: float
    amount: float
    billing_cycle: str
    status: str = "unbilled"


@dataclass
class TaxCalculation:
    """Tính toán thuế."""

    tax_type: str
    rate: float
    amount: float
    jurisdiction: str
    exemption_status: bool = False


@dataclass
class RevenueRecognition:
    """Nhận diện doanh thu."""

    revenue_id: str
    amount: float
    recognition_date: str
    service_period: str
    status: str = "pending"


@dataclass
class BillingAnalytics:
    """Analytics về billing."""

    customer_id: str
    total_spent: float
    last_payment_date: str
    invoice_count: int


# --- Class Chính ---


class BillingFoundation:
    """
    Nền tảng Billing cốt lõi để quản lý hóa đơn, thanh toán và doanh thu.
    """

    def __init__(
        self, db_path: str = "billing_data.db", config: Dict[str, Any] = DEFAULT_CONFIG
    ):
        self.db_path = db_path
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._setup_database()
        logger.info("BillingFoundation đã khởi tạo thành công.")

    def _setup_database(self) -> None:
        """Thiết lập cấu trúc cơ sở dữ liệu SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS invoices (
                    invoice_id TEXT PRIMARY KEY,
                    customer_id TEXT,
                    items TEXT,
                    subtotal REAL,
                    taxes REAL,
                    total REAL,
                    status TEXT,
                    due_date TEXT
                )
            """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS payments (
                    payment_id TEXT PRIMARY KEY,
                    invoice_id TEXT,
                    amount REAL,
                    method TEXT,
                    status TEXT,
                    timestamp TEXT,
                    transaction_id TEXT
                )
            """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS billing_records (
                    record_id TEXT PRIMARY KEY,
                    customer_id TEXT,
                    service_type TEXT,
                    usage REAL,
                    amount REAL,
                    billing_cycle TEXT,
                    status TEXT
                )
            """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tax_calculations (
                    id INTEGER PRIMARY KEY,
                    tax_type TEXT,
                    rate REAL,
                    amount REAL,
                    jurisdiction TEXT,
                    exemption_status INTEGER
                )
            """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS revenue_recognition (
                    revenue_id TEXT PRIMARY KEY,
                    amount REAL,
                    recognition_date TEXT,
                    service_period TEXT,
                    status TEXT
                )
            """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS billing_analytics (
                    customer_id TEXT PRIMARY KEY,
                    total_spent REAL,
                    last_payment_date TEXT,
                    invoice_count INTEGER
                )
            """
            )
            conn.commit()
            logger.info("Cơ sở dữ liệu đã được thiết lập.")
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi thiết lập cơ sở dữ liệu: {e}")
        finally:
            conn.close()

    async def _run_in_thread(self, func, *args):
        """Chạy một hàm trong luồng để tránh block I/O."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args)

    async def generate_invoice(self, data: Dict[str, Any]) -> Invoice:
        """Tạo một hóa đơn mới từ dữ liệu sử dụng."""
        try:
            logger.info(f"Đang tạo hóa đơn cho khách hàng: {data['customer_id']}")
            invoice_id = str(uuid.uuid4())
            subtotal = sum(item["quantity"] * item["rate"] for item in data["items"])

            # Tính thuế dựa trên jurisdiction
            jurisdiction = data.get("jurisdiction", "VAT_VIETNAM")
            tax_rate = self.config["tax_rates"].get(jurisdiction, 0.0)
            tax_amount = subtotal * tax_rate
            total = subtotal + tax_amount

            invoice = Invoice(
                invoice_id=invoice_id,
                customer_id=data["customer_id"],
                items=data["items"],
                subtotal=subtotal,
                taxes=tax_amount,
                total=total,
                due_date=str(datetime.now().date()),
            )

            # Lưu vào database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO invoices VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    invoice.invoice_id,
                    invoice.customer_id,
                    json.dumps(invoice.items),
                    invoice.subtotal,
                    invoice.taxes,
                    invoice.total,
                    invoice.status,
                    invoice.due_date,
                ),
            )
            conn.commit()
            conn.close()

            logger.info(f"Đã tạo hóa đơn {invoice.invoice_id} thành công.")
            return invoice
        except Exception as e:
            logger.error(f"Lỗi khi tạo hóa đơn: {e}")
            raise

    async def process_payment(self, data: Dict[str, Any]) -> Payment:
        """Xử lý thanh toán cho một hóa đơn."""
        try:
            logger.info(f"Đang xử lý thanh toán cho hóa đơn: {data['invoice_id']}")
            payment_id = str(uuid.uuid4())

            # Giả lập xử lý thanh toán và trạng thái
            if data["method"] in self.config["payment_methods"]:
                status = "completed"
                transaction_id = str(uuid.uuid4())
            else:
                status = "failed"
                transaction_id = ""

            payment = Payment(
                payment_id=payment_id,
                invoice_id=data["invoice_id"],
                amount=data["amount"],
                method=data["method"],
                status=status,
                timestamp=str(datetime.now()),
                transaction_id=transaction_id,
            )

            # Lưu vào database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO payments VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    payment.payment_id,
                    payment.invoice_id,
                    payment.amount,
                    payment.method,
                    payment.status,
                    payment.timestamp,
                    payment.transaction_id,
                ),
            )

            # Cập nhật trạng thái hóa đơn
            if status == "completed":
                cursor.execute(
                    "UPDATE invoices SET status = 'paid' WHERE invoice_id = ?",
                    (payment.invoice_id,),
                )

            conn.commit()
            conn.close()

            logger.info(
                f"Đã xử lý thanh toán {payment.payment_id} với trạng thái: {status}"
            )
            return payment
        except Exception as e:
            logger.error(f"Lỗi khi xử lý thanh toán: {e}")
            raise

    async def track_billing(self, data: Dict[str, Any]) -> BillingRecord:
        """Ghi lại một bản ghi billing mới."""
        try:
            logger.info(
                f"Đang ghi lại bản ghi billing cho khách hàng: {data['customer_id']}"
            )
            record_id = str(uuid.uuid4())

            record = BillingRecord(
                record_id=record_id,
                customer_id=data["customer_id"],
                service_type=data["service_type"],
                usage=data["usage"],
                amount=data["amount"],
                billing_cycle=data["billing_cycle"],
            )

            # Lưu vào database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO billing_records VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    record.record_id,
                    record.customer_id,
                    record.service_type,
                    record.usage,
                    record.amount,
                    record.billing_cycle,
                    record.status,
                ),
            )
            conn.commit()
            conn.close()

            logger.info(f"Đã ghi lại bản ghi billing {record.record_id}.")
            return record
        except Exception as e:
            logger.error(f"Lỗi khi theo dõi billing: {e}")
            raise

    async def calculate_taxes(
        self, subtotal: float, jurisdiction: str
    ) -> TaxCalculation:
        """Tính toán thuế dựa trên khu vực pháp lý."""
        try:
            logger.info(f"Đang tính thuế cho khu vực: {jurisdiction}")
            tax_rate = self.config["tax_rates"].get(jurisdiction.upper(), 0.0)
            tax_amount = subtotal * tax_rate

            tax_calc = TaxCalculation(
                tax_type="VAT",
                rate=tax_rate,
                amount=tax_amount,
                jurisdiction=jurisdiction,
                exemption_status=False,
            )

            # Lưu vào database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tax_calculations VALUES (NULL, ?, ?, ?, ?, ?)",
                (
                    "VAT",
                    tax_calc.rate,
                    tax_calc.amount,
                    tax_calc.jurisdiction,
                    tax_calc.exemption_status,
                ),
            )
            conn.commit()
            conn.close()

            return tax_calc
        except Exception as e:
            logger.error(f"Lỗi khi tính thuế: {e}")
            raise

    async def recognize_revenue(self, data: Dict[str, Any]) -> RevenueRecognition:
        """Nhận diện doanh thu tuân thủ GAAP."""
        try:
            logger.info(
                f"Đang nhận diện doanh thu cho giai đoạn: {data['service_period']}"
            )
            revenue_id = str(uuid.uuid4())

            revenue = RevenueRecognition(
                revenue_id=revenue_id,
                amount=data["amount"],
                recognition_date=str(datetime.now().date()),
                service_period=data["service_period"],
                status="recognized",
            )

            # Lưu vào database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO revenue_recognition VALUES (?, ?, ?, ?, ?)",
                (
                    revenue.revenue_id,
                    revenue.amount,
                    revenue.recognition_date,
                    revenue.service_period,
                    revenue.status,
                ),
            )
            conn.commit()
            conn.close()

            logger.info(f"Đã nhận diện doanh thu {revenue.revenue_id}.")
            return revenue
        except Exception as e:
            logger.error(f"Lỗi khi nhận diện doanh thu: {e}")
            raise

    async def close(self) -> None:
        """Đóng ThreadPoolExecutor."""
        self.executor.shutdown(wait=True)
        logger.info("Executor đã đóng.")


# --- Ví dụ sử dụng ---
async def main():
    try:
        billing = BillingFoundation()

        # 1. Tạo hóa đơn
        invoice_data = {
            "customer_id": "cust_001",
            "items": [{"service": "API calls", "quantity": 1000, "rate": 0.01}],
            "billing_cycle": "monthly",
        }
        invoice = await billing.generate_invoice(invoice_data)
        print(
            f"\nĐã tạo hóa đơn {invoice.invoice_id} cho khách hàng {invoice.customer_id}"
        )
        print(f"Tổng cộng: ${invoice.total:.2f}")

        # 2. Xử lý thanh toán
        payment_data = {
            "invoice_id": invoice.invoice_id,
            "amount": invoice.total,
            "method": "credit_card",
        }
        payment = await billing.process_payment(payment_data)
        print(f"Trạng thái thanh toán: {payment.status}")

        # 3. Theo dõi billing
        billing_record = await billing.track_billing(
            {
                "customer_id": "cust_001",
                "service_type": "API calls",
                "usage": 1500,
                "amount": 15.00,
                "billing_cycle": "monthly",
            }
        )
        print(f"Đã ghi lại bản ghi billing {billing_record.record_id}")

        # 4. Nhận diện doanh thu
        revenue = await billing.recognize_revenue(
            {"amount": 100.0, "service_period": "2025-09"}
        )
        print(f"Trạng thái nhận diện doanh thu: {revenue.status}")

        await billing.close()
    except Exception as e:
        logger.error(f"Đã xảy ra lỗi trong hàm main: {e}")


if __name__ == "__main__":
    asyncio.run(main())
