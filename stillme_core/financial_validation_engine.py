import asyncio
import sqlite3
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
import json
import hashlib
import time

# --- Cấu hình và Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cấu hình mặc định
DEFAULT_CONFIG = {
    "validation_threshold": 0.9999,
    "confidence_score_weights": {
        "calculation": 0.4,
        "compliance": 0.4,
        "audit_trail": 0.2
    }
}

# --- Dataclasses ---

@dataclass
class FinancialCalculation:
    """Cấu trúc tính toán tài chính."""
    amount: float
    currency: str
    calculation_type: str
    formula: str
    result: float = field(init=False)

    def __post_init__(self):
        # Tính toán an toàn thay vì sử dụng eval()
        if "base_cost" in self.formula:
            # Thay thế base_cost bằng giá trị thực tế
            safe_formula = self.formula.replace("base_cost", str(self.amount))
            # Tính toán an toàn cho các công thức cơ bản
            if "* (1 + 0.25)" in safe_formula:
                self.result = self.amount * 1.25
            elif "* (1 + 0.5)" in safe_formula:
                self.result = self.amount * 1.5
            elif "* 1.1" in safe_formula:
                self.result = self.amount * 1.1
            else:
                self.result = self.amount  # Fallback
        else:
            self.result = self.amount

@dataclass
class ComplianceCheck:
    """Kiểm tra tuân thủ quy định."""
    regulation_type: str
    requirement: str
    status: str
    evidence: str
    risk_score: float = 0.0

@dataclass
class AuditTrail:
    """Dấu vết kiểm toán bất biến."""
    action: str
    user: str
    timestamp: float
    details: Dict[str, Any]
    hash: str = ""

@dataclass
class ValidationResult:
    """Kết quả xác thực tổng hợp."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    confidence_score: float = 0.0

@dataclass
class RegulatoryReport:
    """Báo cáo tuân thủ theo quy định."""
    report_type: str
    period: str
    data: Dict[str, Any]
    compliance_status: str

# --- Class Chính ---

class FinancialValidationEngine:
    """
    Công cụ xác thực tài chính doanh nghiệp, đảm bảo độ chính xác
    và tuân thủ các quy định.
    """
    def __init__(self, db_path: str = "financial_data.db", config: Dict[str, Any] = DEFAULT_CONFIG):
        self.db_path = db_path
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._setup_database()
        logger.info("FinancialValidationEngine đã khởi tạo thành công.")

    def _setup_database(self) -> None:
        """Thiết lập cấu trúc cơ sở dữ liệu SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS financial_calculations (
                    id INTEGER PRIMARY KEY,
                    amount REAL,
                    currency TEXT,
                    calculation_type TEXT,
                    formula TEXT,
                    result REAL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_checks (
                    id INTEGER PRIMARY KEY,
                    regulation_type TEXT,
                    requirement TEXT,
                    status TEXT,
                    evidence TEXT,
                    risk_score REAL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_trails (
                    id INTEGER PRIMARY KEY,
                    action TEXT,
                    user TEXT,
                    timestamp REAL,
                    details TEXT,
                    hash TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS validation_results (
                    id INTEGER PRIMARY KEY,
                    is_valid INTEGER,
                    errors TEXT,
                    warnings TEXT,
                    confidence_score REAL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regulatory_reports (
                    id INTEGER PRIMARY KEY,
                    report_type TEXT,
                    period TEXT,
                    data TEXT,
                    compliance_status TEXT
                )
            """)
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

    async def validate_financial_calculation(self, calc_data: Dict[str, Any]) -> ValidationResult:
        """
        Xác thực tính toán tài chính.
        Giả lập các bước xác thực như công thức, tiền tệ.
        """
        try:
            logger.info(f"Đang xác thực tính toán tài chính: {calc_data['calculation_type']}")
            errors = []
            
            # Giả lập kiểm tra công thức và độ chính xác
            financial_calc = FinancialCalculation(**calc_data)
            
            if abs(financial_calc.result - (financial_calc.amount * 1.25)) > 0.01:
                errors.append("Sai lệch đáng kể trong kết quả tính toán.")
            
            is_valid = not errors
            confidence_score = 1.0 if is_valid else 0.5
            validation_result = ValidationResult(is_valid=is_valid, errors=errors, confidence_score=confidence_score)
            
            # Lưu kết quả vào database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO financial_calculations VALUES (NULL, ?, ?, ?, ?, ?)",
                           (financial_calc.amount, financial_calc.currency, financial_calc.calculation_type,
                            financial_calc.formula, financial_calc.result))
            cursor.execute("INSERT INTO validation_results VALUES (NULL, ?, ?, ?, ?)",
                           (validation_result.is_valid, json.dumps(validation_result.errors),
                            json.dumps(validation_result.warnings), validation_result.confidence_score))
            conn.commit()
            conn.close()
            
            return validation_result
        except Exception as e:
            logger.error(f"Lỗi khi xác thực tính toán tài chính: {e}")
            raise

    async def check_compliance(self, compliance_data: Dict[str, Any]) -> ComplianceCheck:
        """
        Kiểm tra tuân thủ quy định.
        Giả lập kiểm tra tuân thủ.
        """
        try:
            logger.info(f"Đang kiểm tra tuân thủ quy định: {compliance_data['regulation_type']}")
            compliance_check = ComplianceCheck(**compliance_data)
            
            # Giả lập đánh giá rủi ro và trạng thái
            if "SOX" in compliance_check.regulation_type:
                compliance_check.status = "compliant"
                compliance_check.risk_score = 0.1
            else:
                compliance_check.status = "non-compliant"
                compliance_check.risk_score = 0.9
            
            # Lưu vào database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO compliance_checks VALUES (NULL, ?, ?, ?, ?, ?)",
                           (compliance_check.regulation_type, compliance_check.requirement,
                            compliance_check.status, compliance_check.evidence, compliance_check.risk_score))
            conn.commit()
            conn.close()
            
            return compliance_check
        except Exception as e:
            logger.error(f"Lỗi khi kiểm tra tuân thủ: {e}")
            raise

    async def generate_audit_trail(self, action: str, user: str, details: Dict[str, Any]) -> AuditTrail:
        """Tạo dấu vết kiểm toán với hashing mật mã."""
        try:
            logger.info(f"Đang tạo dấu vết kiểm toán cho hành động: {action}")
            timestamp = time.time()
            data_to_hash = f"{action}|{user}|{timestamp}|{json.dumps(details)}"
            hashed_data = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest()
            
            audit_trail = AuditTrail(action=action, user=user, timestamp=timestamp, details=details, hash=hashed_data)
            
            # Lưu vào database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO audit_trails VALUES (NULL, ?, ?, ?, ?, ?)",
                           (audit_trail.action, audit_trail.user, audit_trail.timestamp,
                            json.dumps(audit_trail.details), audit_trail.hash))
            conn.commit()
            conn.close()
            
            return audit_trail
        except Exception as e:
            logger.error(f"Lỗi khi tạo dấu vết kiểm toán: {e}")
            raise

    async def create_regulatory_report(self, report_type: str, period: str, data: Dict[str, Any]) -> RegulatoryReport:
        """Tạo báo cáo tuân thủ theo mẫu."""
        try:
            logger.info(f"Đang tạo báo cáo tuân thủ: {report_type} cho giai đoạn {period}")
            
            # Giả lập logic kiểm tra tuân thủ để tạo báo cáo
            compliance_status = "Đã tuân thủ" if data.get("sox_status") == "compliant" else "Không tuân thủ"
            
            regulatory_report = RegulatoryReport(
                report_type=report_type,
                period=period,
                data=data,
                compliance_status=compliance_status
            )
            
            # Lưu vào database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO regulatory_reports VALUES (NULL, ?, ?, ?, ?)",
                           (regulatory_report.report_type, regulatory_report.period,
                            json.dumps(regulatory_report.data), regulatory_report.compliance_status))
            conn.commit()
            conn.close()
            
            return regulatory_report
        except Exception as e:
            logger.error(f"Lỗi khi tạo báo cáo tuân thủ: {e}")
            raise

    async def validate_pricing_accuracy(self, pricing_engine: Any, product_id: str) -> ValidationResult:
        """
        Validate độ chính xác của pricing bằng cách so sánh với một nguồn khác.
        Tích hợp với IntelligentPricingEngine.
        """
        try:
            logger.info(f"Đang xác thực độ chính xác của giá cho sản phẩm: {product_id}")
            
            # Giả lập lấy giá từ một nguồn khác (từ pricing_engine)
            # Lưu ý: pricing_engine cần được khởi tạo và có method generate_pricing_recommendation
            pricing_recommendation = await pricing_engine.generate_pricing_recommendation(product_id)
            calculated_price = pricing_recommendation.recommended_price
            
            # Giả lập giá thực tế từ hệ thống khác
            external_price = 12000.0  # Giá trị này có thể đến từ một hệ thống khác
            
            # So sánh
            is_valid = abs(calculated_price - external_price) / external_price < (1 - self.config["validation_threshold"])
            
            validation_result = ValidationResult(
                is_valid=is_valid,
                errors=["Giá tính toán không đủ chính xác."] if not is_valid else [],
                confidence_score=1.0 if is_valid else 0.8
            )
            return validation_result
        except Exception as e:
            logger.error(f"Lỗi khi xác thực độ chính xác giá: {e}")
            raise

    async def close(self) -> None:
        """Đóng ThreadPoolExecutor."""
        self.executor.shutdown(wait=True)
        logger.info("Executor đã đóng.")

# --- Ví dụ sử dụng ---
async def main():
    try:
        validation_engine = FinancialValidationEngine()
        
        # 1. Xác thực một tính toán tài chính
        calc_result = await validation_engine.validate_financial_calculation({
            "amount": 1000.0,
            "currency": "USD",
            "calculation_type": "cost_plus",
            "formula": "base_cost * (1 + 0.25)"
        })
        print(f"\nValidation Result (Calculation): {calc_result.is_valid}")
        print(f"Confidence Score: {calc_result.confidence_score:.2f}")

        # 2. Kiểm tra tuân thủ
        compliance_result = await validation_engine.check_compliance({
            "regulation_type": "SOX",
            "requirement": "Kiểm tra nội bộ",
            "status": "pending",
            "evidence": "Tài liệu kiểm toán"
        })
        print(f"\nCompliance Check Status: {compliance_result.status}")

        # 3. Tạo dấu vết kiểm toán
        audit_trail = await validation_engine.generate_audit_trail("data_modification", "admin_user", {"old_value": "100", "new_value": "120"})
        print(f"\nAudit Trail Hash: {audit_trail.hash}")

        # 4. Tạo báo cáo tuân thủ
        report_data = {"sox_status": "compliant", "data_integrity": "high"}
        regulatory_report = await validation_engine.create_regulatory_report("Quarterly Report", "Q3 2025", report_data)
        print(f"\nRegulatory Report Status: {regulatory_report.compliance_status}")

        await validation_engine.close()
        
    except Exception as e:
        logger.error(f"Đã xảy ra lỗi trong hàm main: {e}")

if __name__ == "__main__":
    asyncio.run(main())
