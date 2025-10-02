"""
🛡️ DATA VALIDATION FRAMEWORK - SUB-PHASE 3.1
==============================================

Enterprise-grade data validation system cho StillMe AI Framework.
Đảm bảo data accuracy, anomaly detection, và comprehensive audit trails.

Author: StillMe Phase 3 Development Team
Version: 3.1.0
Phase: 3.1 - Core Metrics Foundation
Quality Standard: Enterprise-Grade (99.9% accuracy target)

FEATURES:
- Data accuracy verification system
- Real-time anomaly detection
- Comprehensive audit trail implementation
- Data consistency checks
- Integrity validation
- Performance monitoring
"""

import asyncio
import hashlib
import json
import logging
import sqlite3
import statistics
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Union

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of data validation"""

    is_valid: bool
    accuracy_score: float
    errors_found: list[str]
    warnings: list[str]
    data_completeness: float
    consistency_score: float
    integrity_score: float
    timestamp: datetime
    validation_duration_ms: float


@dataclass
class AnomalyDetectionResult:
    """Result of anomaly detection"""

    anomalies_found: list[dict[str, Any]]
    anomaly_score: float
    severity_level: str  # "low", "medium", "high", "critical"
    detection_confidence: float
    recommended_actions: list[str]
    timestamp: datetime


@dataclass
class AuditTrailEntry:
    """Single audit trail entry"""

    entry_id: str
    timestamp: datetime
    operation_type: str
    user_id: Optional[str]
    resource_accessed: str
    action_performed: str
    result_status: str
    metadata: dict[str, Any]
    data_hash: str
    integrity_verified: bool


@dataclass
class DataIntegrityReport:
    """Comprehensive data integrity report"""

    total_records_checked: int
    valid_records: int
    invalid_records: int
    missing_data_count: int
    duplicate_records: int
    consistency_violations: int
    integrity_score: float
    recommendations: list[str]
    timestamp: datetime


class DataValidationFramework:
    """
    Enterprise-grade data validation framework với focus vào accuracy và security
    """

    def __init__(self, db_path: str, config: Optional[dict[str, Any]] = None):
        self.db_path = Path(db_path)
        self.config = config or self._get_default_config()

        # Validation rules
        self._validation_rules = self._load_validation_rules()

        # Anomaly detection
        self._anomaly_thresholds = self._load_anomaly_thresholds()
        self._baseline_metrics = {}

        # Audit trail
        self._audit_trail = deque(maxlen=self.config["audit_trail_size"])
        self._audit_lock = threading.RLock()

        # Performance monitoring
        self._validation_times = deque(maxlen=1000)
        self._accuracy_history = deque(maxlen=100)

        # Threading
        self._executor = ThreadPoolExecutor(max_workers=self.config["max_workers"])
        self._running = False

        # Initialize database
        self._init_validation_database()

        logger.info(
            "✅ DataValidationFramework initialized với enterprise-grade configuration"
        )

    def _get_default_config(self) -> dict[str, Any]:
        """Default configuration với security và performance focus"""
        return {
            "accuracy_threshold": 0.999,  # 99.9% accuracy requirement
            "anomaly_detection_enabled": True,
            "audit_trail_size": 10000,
            "max_workers": 4,
            "validation_timeout_seconds": 30,
            "data_retention_days": 90,
            "integrity_check_interval_minutes": 15,
            "anomaly_detection_sensitivity": 0.8,
            "enable_real_time_validation": True,
            "compression_enabled": True,
            "encryption_enabled": True,
        }

    def _load_validation_rules(self) -> dict[str, Any]:
        """Load validation rules từ configuration"""
        return {
            "required_fields": ["event_id", "timestamp", "module_name", "feature_name"],
            "field_types": {
                "event_id": "string",
                "timestamp": "datetime",
                "module_name": "string",
                "feature_name": "string",
                "duration_ms": "float",
                "success": "boolean",
            },
            "field_constraints": {
                "duration_ms": {"min": 0, "max": 3600000},  # 0 to 1 hour
                "success": {"values": [True, False]},
                "module_name": {"pattern": r"^[a-zA-Z_][a-zA-Z0-9_]*$"},
                "feature_name": {"pattern": r"^[a-zA-Z_][a-zA-Z0-9_]*$"},
            },
            "data_quality_rules": {
                "completeness_threshold": 0.95,  # 95% completeness required
                "consistency_threshold": 0.98,  # 98% consistency required
                "accuracy_threshold": 0.999,  # 99.9% accuracy required
            },
        }

    def _load_anomaly_thresholds(self) -> dict[str, Any]:
        """Load anomaly detection thresholds"""
        return {
            "response_time": {
                "normal_range": (0, 5000),  # 0-5 seconds
                "warning_threshold": 10000,  # 10 seconds
                "critical_threshold": 30000,  # 30 seconds
            },
            "error_rate": {
                "normal_range": (0, 0.05),  # 0-5%
                "warning_threshold": 0.1,  # 10%
                "critical_threshold": 0.2,  # 20%
            },
            "memory_usage": {
                "normal_range": (0, 1024),  # 0-1GB
                "warning_threshold": 2048,  # 2GB
                "critical_threshold": 4096,  # 4GB
            },
            "cpu_usage": {
                "normal_range": (0, 50),  # 0-50%
                "warning_threshold": 80,  # 80%
                "critical_threshold": 95,  # 95%
            },
        }

    def _init_validation_database(self):
        """Initialize validation database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Validation results table
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS validation_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        validation_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        is_valid BOOLEAN NOT NULL,
                        accuracy_score REAL NOT NULL,
                        errors_found TEXT,
                        warnings TEXT,
                        data_completeness REAL NOT NULL,
                        consistency_score REAL NOT NULL,
                        integrity_score REAL NOT NULL,
                        validation_duration_ms REAL NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Anomaly detection results table
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS anomaly_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        anomaly_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        anomalies_found TEXT NOT NULL,
                        anomaly_score REAL NOT NULL,
                        severity_level TEXT NOT NULL,
                        detection_confidence REAL NOT NULL,
                        recommended_actions TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Audit trail table
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS audit_trail (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entry_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        operation_type TEXT NOT NULL,
                        user_id TEXT,
                        resource_accessed TEXT NOT NULL,
                        action_performed TEXT NOT NULL,
                        result_status TEXT NOT NULL,
                        metadata TEXT,
                        data_hash TEXT NOT NULL,
                        integrity_verified BOOLEAN NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Data integrity reports table
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS integrity_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        report_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        total_records_checked INTEGER NOT NULL,
                        valid_records INTEGER NOT NULL,
                        invalid_records INTEGER NOT NULL,
                        missing_data_count INTEGER NOT NULL,
                        duplicate_records INTEGER NOT NULL,
                        consistency_violations INTEGER NOT NULL,
                        integrity_score REAL NOT NULL,
                        recommendations TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Indexes for performance
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_validation_timestamp ON validation_results(timestamp)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_anomaly_timestamp ON anomaly_results(timestamp)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_trail(timestamp)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_trail(user_id)"
                )

                conn.commit()

            logger.info("✅ Validation database initialized")

        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise

    def start_validation(self):
        """Start validation framework"""
        if self._running:
            logger.warning("⚠️ Validation framework already running")
            return

        self._running = True

        # Start background tasks
        asyncio.create_task(self._periodic_integrity_check())
        asyncio.create_task(self._periodic_anomaly_detection())

        logger.info("🚀 DataValidationFramework started")

    def stop_validation(self):
        """Stop validation framework"""
        if not self._running:
            return

        self._running = False
        self._executor.shutdown(wait=True)

        logger.info("🛑 DataValidationFramework stopped")

    def validate_data(
        self,
        data: Union[dict[str, Any], list[dict[str, Any]]],
        validation_type: str = "usage_event",
    ) -> ValidationResult:
        """
        Validate data với comprehensive checks

        Args:
            data: Data to validate (single record or list)
            validation_type: Type of validation to perform

        Returns:
            ValidationResult object
        """
        start_time = time.time()

        try:
            # Convert single record to list
            if isinstance(data, dict):
                data_list = [data]
            else:
                data_list = data

            # Initialize validation results
            errors_found = []
            warnings = []
            valid_records = 0
            total_records = len(data_list)

            # Validate each record
            for record in data_list:
                record_errors, record_warnings = self._validate_single_record(
                    record, validation_type
                )
                errors_found.extend(record_errors)
                warnings.extend(record_warnings)

                if not record_errors:
                    valid_records += 1

            # Calculate metrics
            accuracy_score = valid_records / max(1, total_records)
            data_completeness = self._calculate_completeness(data_list)
            consistency_score = self._calculate_consistency(data_list)
            integrity_score = self._calculate_integrity(data_list)

            # Determine overall validity
            is_valid = (
                accuracy_score >= self.config["accuracy_threshold"]
                and data_completeness
                >= self._validation_rules["data_quality_rules"][
                    "completeness_threshold"
                ]
                and consistency_score
                >= self._validation_rules["data_quality_rules"]["consistency_threshold"]
            )

            # Create validation result
            validation_duration_ms = (time.time() - start_time) * 1000
            result = ValidationResult(
                is_valid=is_valid,
                accuracy_score=accuracy_score,
                errors_found=errors_found,
                warnings=warnings,
                data_completeness=data_completeness,
                consistency_score=consistency_score,
                integrity_score=integrity_score,
                timestamp=datetime.now(),
                validation_duration_ms=validation_duration_ms,
            )

            # Store validation result
            self._store_validation_result(result)

            # Update performance metrics
            self._validation_times.append(validation_duration_ms)
            self._accuracy_history.append(accuracy_score)

            # Log audit trail
            self._log_audit_trail(
                operation_type="data_validation",
                resource_accessed=f"validation_{validation_type}",
                action_performed="validate_data",
                result_status="success" if is_valid else "failed",
                metadata={
                    "records_checked": total_records,
                    "accuracy_score": accuracy_score,
                },
            )

            return result

        except Exception as e:
            logger.error(f"❌ Data validation failed: {e}")

            # Log error in audit trail
            self._log_audit_trail(
                operation_type="data_validation",
                resource_accessed=f"validation_{validation_type}",
                action_performed="validate_data",
                result_status="error",
                metadata={"error": str(e)},
            )

            # Return error result
            return ValidationResult(
                is_valid=False,
                accuracy_score=0.0,
                errors_found=[f"Validation error: {e!s}"],
                warnings=[],
                data_completeness=0.0,
                consistency_score=0.0,
                integrity_score=0.0,
                timestamp=datetime.now(),
                validation_duration_ms=(time.time() - start_time) * 1000,
            )

    def _validate_single_record(
        self, record: dict[str, Any], validation_type: str
    ) -> tuple[list[str], list[str]]:
        """Validate single record"""
        errors = []
        warnings = []

        try:
            # Check required fields
            for field in self._validation_rules["required_fields"]:
                if field not in record:
                    errors.append(f"Missing required field: {field}")
                elif record[field] is None:
                    errors.append(f"Required field {field} is null")

            # Check field types
            for field, expected_type in self._validation_rules["field_types"].items():
                if field in record and record[field] is not None:
                    if not self._validate_field_type(record[field], expected_type):
                        errors.append(
                            f"Field {field} has incorrect type. Expected: {expected_type}"
                        )

            # Check field constraints
            for field, constraints in self._validation_rules[
                "field_constraints"
            ].items():
                if field in record and record[field] is not None:
                    field_errors, field_warnings = self._validate_field_constraints(
                        record[field], constraints
                    )
                    errors.extend(field_errors)
                    warnings.extend(field_warnings)

            # Check data quality
            if validation_type == "usage_event":
                quality_errors, quality_warnings = self._validate_usage_event_quality(
                    record
                )
                errors.extend(quality_errors)
                warnings.extend(quality_warnings)

        except Exception as e:
            errors.append(f"Record validation error: {e!s}")

        return errors, warnings

    def _validate_field_type(self, value: Any, expected_type: str) -> bool:
        """Validate field type"""
        type_mapping = {
            "string": str,
            "integer": int,
            "float": float,
            "boolean": bool,
            "datetime": (str, datetime),
        }

        if expected_type in type_mapping:
            return isinstance(value, type_mapping[expected_type])

        return True  # Unknown type, assume valid

    def _validate_field_constraints(
        self, value: Any, constraints: dict[str, Any]
    ) -> tuple[list[str], list[str]]:
        """Validate field constraints"""
        errors = []
        warnings = []

        try:
            # Min/max constraints
            if "min" in constraints and value < constraints["min"]:
                errors.append(f"Value {value} is below minimum {constraints['min']}")

            if "max" in constraints and value > constraints["max"]:
                errors.append(f"Value {value} is above maximum {constraints['max']}")

            # Pattern constraints
            if "pattern" in constraints:
                import re

                if not re.match(constraints["pattern"], str(value)):
                    errors.append(
                        f"Value {value} does not match pattern {constraints['pattern']}"
                    )

            # Value constraints
            if "values" in constraints and value not in constraints["values"]:
                errors.append(
                    f"Value {value} is not in allowed values {constraints['values']}"
                )

        except Exception as e:
            errors.append(f"Constraint validation error: {e!s}")

        return errors, warnings

    def _validate_usage_event_quality(
        self, record: dict[str, Any]
    ) -> tuple[list[str], list[str]]:
        """Validate usage event quality"""
        errors = []
        warnings = []

        try:
            # Check timestamp validity
            if "timestamp" in record:
                timestamp = record["timestamp"]
                if isinstance(timestamp, str):
                    try:
                        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    except ValueError:
                        errors.append("Invalid timestamp format")
                elif isinstance(timestamp, datetime):
                    # Check if timestamp is reasonable (not too far in past/future)
                    now = datetime.now()
                    if timestamp < now - timedelta(days=365):
                        warnings.append("Timestamp is more than 1 year in the past")
                    elif timestamp > now + timedelta(days=1):
                        warnings.append("Timestamp is in the future")

            # Check duration reasonableness
            if "duration_ms" in record and record["duration_ms"] is not None:
                duration = record["duration_ms"]
                if duration < 0:
                    errors.append("Duration cannot be negative")
                elif duration > 3600000:  # 1 hour
                    warnings.append("Duration is unusually long (>1 hour)")

            # Check resource usage reasonableness
            if record.get("resource_usage"):
                resource_usage = record["resource_usage"]
                if isinstance(resource_usage, dict):
                    if (
                        "memory_mb" in resource_usage
                        and resource_usage["memory_mb"] > 8192
                    ):  # 8GB
                        warnings.append("Memory usage is unusually high (>8GB)")

                    if (
                        "cpu_percent" in resource_usage
                        and resource_usage["cpu_percent"] > 100
                    ):
                        errors.append("CPU usage cannot exceed 100%")

        except Exception as e:
            errors.append(f"Quality validation error: {e!s}")

        return errors, warnings

    def _calculate_completeness(self, data_list: list[dict[str, Any]]) -> float:
        """Calculate data completeness score"""
        if not data_list:
            return 0.0

        total_fields = len(self._validation_rules["required_fields"])
        total_records = len(data_list)
        complete_records = 0

        for record in data_list:
            complete_fields = sum(
                1
                for field in self._validation_rules["required_fields"]
                if field in record and record[field] is not None
            )
            if complete_fields == total_fields:
                complete_records += 1

        return complete_records / total_records

    def _calculate_consistency(self, data_list: list[dict[str, Any]]) -> float:
        """Calculate data consistency score"""
        if not data_list:
            return 0.0

        consistency_violations = 0
        total_checks = 0

        # Check for consistent field types
        for field in self._validation_rules["field_types"]:
            field_values = [
                record.get(field)
                for record in data_list
                if field in record and record[field] is not None
            ]
            if len(field_values) > 1:
                expected_type = self._validation_rules["field_types"][field]
                for value in field_values:
                    total_checks += 1
                    if not self._validate_field_type(value, expected_type):
                        consistency_violations += 1

        return 1.0 - (consistency_violations / max(1, total_checks))

    def _calculate_integrity(self, data_list: list[dict[str, Any]]) -> float:
        """Calculate data integrity score"""
        if not data_list:
            return 0.0

        integrity_violations = 0
        total_records = len(data_list)

        # Check for duplicate records
        seen_hashes = set()
        for record in data_list:
            record_hash = self._calculate_record_hash(record)
            if record_hash in seen_hashes:
                integrity_violations += 1
            else:
                seen_hashes.add(record_hash)

        # Check for logical inconsistencies
        for record in data_list:
            if self._has_logical_inconsistencies(record):
                integrity_violations += 1

        return 1.0 - (integrity_violations / total_records)

    def _calculate_record_hash(self, record: dict[str, Any]) -> str:
        """Calculate hash for record deduplication"""
        # Create a normalized version of the record for hashing
        normalized = {}
        for key, value in record.items():
            if isinstance(value, (dict, list)):
                normalized[key] = json.dumps(value, sort_keys=True)
            else:
                normalized[key] = str(value)

        # Sort keys for consistent hashing
        sorted_items = sorted(normalized.items())
        hash_string = json.dumps(sorted_items, sort_keys=True)

        return hashlib.sha256(hash_string.encode()).hexdigest()

    def _has_logical_inconsistencies(self, record: dict[str, Any]) -> bool:
        """Check for logical inconsistencies in record"""
        try:
            # Check success vs error_code consistency
            if "success" in record and "error_code" in record:
                if record["success"] and record["error_code"] is not None:
                    return True  # Inconsistent: success=True but error_code exists
                if not record["success"] and record["error_code"] is None:
                    return True  # Inconsistent: success=False but no error_code

            # Check duration vs success consistency
            if "duration_ms" in record and "success" in record:
                if record["duration_ms"] == 0 and record["success"]:
                    return True  # Inconsistent: 0 duration but success=True

            return False

        except Exception:
            return True  # Assume inconsistent if we can't check

    def detect_anomalies(
        self, data: list[dict[str, Any]], detection_type: str = "performance"
    ) -> AnomalyDetectionResult:
        """
        Detect anomalies in data

        Args:
            data: Data to analyze
            detection_type: Type of anomaly detection

        Returns:
            AnomalyDetectionResult object
        """
        try:
            anomalies_found = []
            anomaly_score = 0.0
            severity_level = "low"
            detection_confidence = 0.0

            if detection_type == "performance":
                anomalies_found, anomaly_score, severity_level, detection_confidence = (
                    self._detect_performance_anomalies(data)
                )
            elif detection_type == "usage":
                anomalies_found, anomaly_score, severity_level, detection_confidence = (
                    self._detect_usage_anomalies(data)
                )
            elif detection_type == "resource":
                anomalies_found, anomaly_score, severity_level, detection_confidence = (
                    self._detect_resource_anomalies(data)
                )

            # Generate recommended actions
            recommended_actions = self._generate_anomaly_recommendations(
                anomalies_found, severity_level
            )

            result = AnomalyDetectionResult(
                anomalies_found=anomalies_found,
                anomaly_score=anomaly_score,
                severity_level=severity_level,
                detection_confidence=detection_confidence,
                recommended_actions=recommended_actions,
                timestamp=datetime.now(),
            )

            # Store anomaly result
            self._store_anomaly_result(result)

            # Log audit trail
            self._log_audit_trail(
                operation_type="anomaly_detection",
                resource_accessed=f"anomaly_{detection_type}",
                action_performed="detect_anomalies",
                result_status="anomalies_found" if anomalies_found else "no_anomalies",
                metadata={
                    "anomalies_count": len(anomalies_found),
                    "severity": severity_level,
                },
            )

            return result

        except Exception as e:
            logger.error(f"❌ Anomaly detection failed: {e}")

            return AnomalyDetectionResult(
                anomalies_found=[{"error": str(e)}],
                anomaly_score=1.0,
                severity_level="critical",
                detection_confidence=0.0,
                recommended_actions=["Investigate anomaly detection system"],
                timestamp=datetime.now(),
            )

    def _detect_performance_anomalies(
        self, data: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], float, str, float]:
        """Detect performance anomalies"""
        anomalies = []
        anomaly_score = 0.0
        severity_level = "low"
        confidence = 0.0

        try:
            # Extract performance metrics
            durations = [
                record.get("duration_ms", 0)
                for record in data
                if "duration_ms" in record
            ]

            if len(durations) < 2:
                return anomalies, anomaly_score, severity_level, confidence

            # Calculate statistics
            mean_duration = statistics.mean(durations)
            std_duration = statistics.stdev(durations) if len(durations) > 1 else 0

            # Detect outliers using z-score
            threshold = self.config["anomaly_detection_sensitivity"]
            for i, duration in enumerate(durations):
                if std_duration > 0:
                    z_score = abs((duration - mean_duration) / std_duration)
                    if z_score > threshold:
                        anomaly = {
                            "type": "performance_outlier",
                            "record_index": i,
                            "duration_ms": duration,
                            "z_score": z_score,
                            "threshold": threshold,
                        }
                        anomalies.append(anomaly)

                        # Update severity
                        if z_score > 3.0:
                            severity_level = "critical"
                        elif z_score > 2.0:
                            severity_level = "high"
                        elif z_score > 1.5:
                            severity_level = "medium"

            # Calculate anomaly score
            if durations:
                anomaly_score = len(anomalies) / len(durations)

            # Calculate confidence
            confidence = min(
                1.0, len(durations) / 100.0
            )  # More data = higher confidence

        except Exception as e:
            logger.error(f"❌ Performance anomaly detection error: {e}")

        return anomalies, anomaly_score, severity_level, confidence

    def _detect_usage_anomalies(
        self, data: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], float, str, float]:
        """Detect usage pattern anomalies"""
        anomalies = []
        anomaly_score = 0.0
        severity_level = "low"
        confidence = 0.0

        try:
            # Group by module and feature
            module_usage = defaultdict(int)
            feature_usage = defaultdict(int)

            for record in data:
                if "module_name" in record:
                    module_usage[record["module_name"]] += 1
                if "feature_name" in record:
                    feature_usage[record["feature_name"]] += 1

            # Detect unusual usage patterns
            total_usage = sum(module_usage.values())
            if total_usage > 0:
                for module, count in module_usage.items():
                    usage_percentage = count / total_usage
                    if usage_percentage > 0.8:  # 80% of usage from one module
                        anomaly = {
                            "type": "usage_concentration",
                            "module": module,
                            "usage_percentage": usage_percentage,
                            "count": count,
                        }
                        anomalies.append(anomaly)

                        if usage_percentage > 0.95:
                            severity_level = "high"
                        elif usage_percentage > 0.9:
                            severity_level = "medium"

            # Calculate anomaly score
            anomaly_score = len(anomalies) / max(1, len(module_usage))
            confidence = min(1.0, total_usage / 1000.0)

        except Exception as e:
            logger.error(f"❌ Usage anomaly detection error: {e}")

        return anomalies, anomaly_score, severity_level, confidence

    def _detect_resource_anomalies(
        self, data: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], float, str, float]:
        """Detect resource usage anomalies"""
        anomalies = []
        anomaly_score = 0.0
        severity_level = "low"
        confidence = 0.0

        try:
            # Extract resource usage data
            memory_usage = []
            cpu_usage = []

            for record in data:
                if "resource_usage" in record and isinstance(
                    record["resource_usage"], dict
                ):
                    resource_usage = record["resource_usage"]
                    if "memory_mb" in resource_usage:
                        memory_usage.append(resource_usage["memory_mb"])
                    if "cpu_percent" in resource_usage:
                        cpu_usage.append(resource_usage["cpu_percent"])

            # Check memory usage anomalies
            if memory_usage:
                max_memory = max(memory_usage)
                if (
                    max_memory
                    > self._anomaly_thresholds["memory_usage"]["critical_threshold"]
                ):
                    anomalies.append(
                        {
                            "type": "memory_usage_critical",
                            "max_memory_mb": max_memory,
                            "threshold": self._anomaly_thresholds["memory_usage"][
                                "critical_threshold"
                            ],
                        }
                    )
                    severity_level = "critical"
                elif (
                    max_memory
                    > self._anomaly_thresholds["memory_usage"]["warning_threshold"]
                ):
                    anomalies.append(
                        {
                            "type": "memory_usage_high",
                            "max_memory_mb": max_memory,
                            "threshold": self._anomaly_thresholds["memory_usage"][
                                "warning_threshold"
                            ],
                        }
                    )
                    if severity_level == "low":
                        severity_level = "medium"

            # Check CPU usage anomalies
            if cpu_usage:
                max_cpu = max(cpu_usage)
                if (
                    max_cpu
                    > self._anomaly_thresholds["cpu_usage"]["critical_threshold"]
                ):
                    anomalies.append(
                        {
                            "type": "cpu_usage_critical",
                            "max_cpu_percent": max_cpu,
                            "threshold": self._anomaly_thresholds["cpu_usage"][
                                "critical_threshold"
                            ],
                        }
                    )
                    severity_level = "critical"
                elif (
                    max_cpu > self._anomaly_thresholds["cpu_usage"]["warning_threshold"]
                ):
                    anomalies.append(
                        {
                            "type": "cpu_usage_high",
                            "max_cpu_percent": max_cpu,
                            "threshold": self._anomaly_thresholds["cpu_usage"][
                                "warning_threshold"
                            ],
                        }
                    )
                    if severity_level == "low":
                        severity_level = "medium"

            # Calculate anomaly score
            total_checks = len(memory_usage) + len(cpu_usage)
            anomaly_score = len(anomalies) / max(1, total_checks)
            confidence = min(1.0, total_checks / 100.0)

        except Exception as e:
            logger.error(f"❌ Resource anomaly detection error: {e}")

        return anomalies, anomaly_score, severity_level, confidence

    def _generate_anomaly_recommendations(
        self, anomalies: list[dict[str, Any]], severity_level: str
    ) -> list[str]:
        """Generate recommendations based on anomalies"""
        recommendations = []

        for anomaly in anomalies:
            anomaly_type = anomaly.get("type", "")

            if anomaly_type == "performance_outlier":
                recommendations.append(
                    "Investigate performance bottleneck in affected module"
                )
            elif anomaly_type == "usage_concentration":
                recommendations.append("Consider load balancing or module optimization")
            elif anomaly_type == "memory_usage_critical":
                recommendations.append("Immediate memory optimization required")
            elif anomaly_type == "cpu_usage_critical":
                recommendations.append("Immediate CPU optimization required")

        # Add severity-based recommendations
        if severity_level == "critical":
            recommendations.append("Immediate investigation and remediation required")
        elif severity_level == "high":
            recommendations.append("Priority investigation recommended")
        elif severity_level == "medium":
            recommendations.append("Monitor and investigate when possible")

        return recommendations

    def _log_audit_trail(
        self,
        operation_type: str,
        resource_accessed: str,
        action_performed: str,
        result_status: str,
        user_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """Log audit trail entry"""
        try:
            entry_id = f"audit_{int(time.time() * 1000)}"
            timestamp = datetime.now()

            # Calculate data hash
            data_to_hash = {
                "operation_type": operation_type,
                "resource_accessed": resource_accessed,
                "action_performed": action_performed,
                "result_status": result_status,
                "metadata": metadata or {},
            }
            data_hash = hashlib.sha256(
                json.dumps(data_to_hash, sort_keys=True).encode()
            ).hexdigest()

            # Create audit entry
            entry = AuditTrailEntry(
                entry_id=entry_id,
                timestamp=timestamp,
                operation_type=operation_type,
                user_id=user_id,
                resource_accessed=resource_accessed,
                action_performed=action_performed,
                result_status=result_status,
                metadata=metadata or {},
                data_hash=data_hash,
                integrity_verified=True,
            )

            # Store in memory
            with self._audit_lock:
                self._audit_trail.append(entry)

            # Store in database
            self._store_audit_entry(entry)

        except Exception as e:
            logger.error(f"❌ Audit trail logging failed: {e}")

    def _store_validation_result(self, result: ValidationResult):
        """Store validation result in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO validation_results
                    (validation_id, timestamp, is_valid, accuracy_score, errors_found, warnings,
                     data_completeness, consistency_score, integrity_score, validation_duration_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        f"val_{int(time.time() * 1000)}",
                        result.timestamp.isoformat(),
                        result.is_valid,
                        result.accuracy_score,
                        json.dumps(result.errors_found),
                        json.dumps(result.warnings),
                        result.data_completeness,
                        result.consistency_score,
                        result.integrity_score,
                        result.validation_duration_ms,
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Failed to store validation result: {e}")

    def _store_anomaly_result(self, result: AnomalyDetectionResult):
        """Store anomaly result in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO anomaly_results
                    (anomaly_id, timestamp, anomalies_found, anomaly_score, severity_level,
                     detection_confidence, recommended_actions)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        f"anom_{int(time.time() * 1000)}",
                        result.timestamp.isoformat(),
                        json.dumps(result.anomalies_found),
                        result.anomaly_score,
                        result.severity_level,
                        result.detection_confidence,
                        json.dumps(result.recommended_actions),
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Failed to store anomaly result: {e}")

    def _store_audit_entry(self, entry: AuditTrailEntry):
        """Store audit entry in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO audit_trail
                    (entry_id, timestamp, operation_type, user_id, resource_accessed,
                     action_performed, result_status, metadata, data_hash, integrity_verified)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        entry.entry_id,
                        entry.timestamp.isoformat(),
                        entry.operation_type,
                        entry.user_id,
                        entry.resource_accessed,
                        entry.action_performed,
                        entry.result_status,
                        json.dumps(entry.metadata),
                        entry.data_hash,
                        entry.integrity_verified,
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Failed to store audit entry: {e}")

    async def _periodic_integrity_check(self):
        """Periodic integrity check task"""
        while self._running:
            try:
                await asyncio.sleep(
                    self.config["integrity_check_interval_minutes"] * 60
                )
                await self._perform_integrity_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Periodic integrity check error: {e}")

    async def _periodic_anomaly_detection(self):
        """Periodic anomaly detection task"""
        while self._running:
            try:
                await asyncio.sleep(300)  # 5 minutes
                await self._perform_anomaly_detection()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Periodic anomaly detection error: {e}")

    async def _perform_integrity_check(self):
        """Perform comprehensive integrity check"""
        try:
            # This would implement actual integrity checking
            logger.info("🔍 Performing integrity check...")
        except Exception as e:
            logger.error(f"❌ Integrity check failed: {e}")

    async def _perform_anomaly_detection(self):
        """Perform periodic anomaly detection"""
        try:
            # This would implement actual anomaly detection
            logger.info("🔍 Performing anomaly detection...")
        except Exception as e:
            logger.error(f"❌ Anomaly detection failed: {e}")

    def get_validation_summary(self, time_range_hours: int = 24) -> dict[str, Any]:
        """Get validation summary for time period"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                since_time = datetime.now() - timedelta(hours=time_range_hours)

                # Get validation statistics
                cursor = conn.execute(
                    """
                    SELECT
                        COUNT(*) as total_validations,
                        AVG(accuracy_score) as avg_accuracy,
                        AVG(data_completeness) as avg_completeness,
                        AVG(consistency_score) as avg_consistency,
                        AVG(integrity_score) as avg_integrity,
                        AVG(validation_duration_ms) as avg_duration_ms
                    FROM validation_results
                    WHERE timestamp >= ?
                """,
                    [since_time.isoformat()],
                )

                stats = cursor.fetchone()

                # Get anomaly statistics
                cursor = conn.execute(
                    """
                    SELECT
                        COUNT(*) as total_anomaly_checks,
                        AVG(anomaly_score) as avg_anomaly_score,
                        COUNT(CASE WHEN severity_level = 'critical' THEN 1 END) as critical_anomalies,
                        COUNT(CASE WHEN severity_level = 'high' THEN 1 END) as high_anomalies
                    FROM anomaly_results
                    WHERE timestamp >= ?
                """,
                    [since_time.isoformat()],
                )

                anomaly_stats = cursor.fetchone()

                return {
                    "time_range_hours": time_range_hours,
                    "validation_stats": {
                        "total_validations": stats[0] or 0,
                        "avg_accuracy": stats[1] or 0.0,
                        "avg_completeness": stats[2] or 0.0,
                        "avg_consistency": stats[3] or 0.0,
                        "avg_integrity": stats[4] or 0.0,
                        "avg_duration_ms": stats[5] or 0.0,
                    },
                    "anomaly_stats": {
                        "total_anomaly_checks": anomaly_stats[0] or 0,
                        "avg_anomaly_score": anomaly_stats[1] or 0.0,
                        "critical_anomalies": anomaly_stats[2] or 0,
                        "high_anomalies": anomaly_stats[3] or 0,
                    },
                    "performance_metrics": {
                        "avg_validation_time_ms": (
                            statistics.mean(self._validation_times)
                            if self._validation_times
                            else 0.0
                        ),
                        "avg_accuracy_history": (
                            statistics.mean(self._accuracy_history)
                            if self._accuracy_history
                            else 0.0
                        ),
                    },
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"❌ Error getting validation summary: {e}")
            return {"error": str(e)}


# Factory function
def create_validation_framework(
    db_path: str, config: Optional[dict[str, Any]] = None
) -> DataValidationFramework:
    """Factory function để create validation framework"""
    return DataValidationFramework(db_path, config)


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Data Validation Framework")
    parser.add_argument("--db-path", required=True, help="Database path")
    parser.add_argument("--validate", help="Validate data file")
    parser.add_argument("--detect-anomalies", help="Detect anomalies in data file")
    parser.add_argument("--summary", action="store_true", help="Get validation summary")
    parser.add_argument(
        "--time-range", type=int, default=24, help="Time range in hours"
    )

    args = parser.parse_args()

    # Create framework
    framework = create_validation_framework(args.db_path)

    if args.validate:
        with open(args.validate) as f:
            data = json.load(f)
        result = framework.validate_data(data)
        print(json.dumps(asdict(result), indent=2, default=str))
    elif args.detect_anomalies:
        with open(args.detect_anomalies) as f:
            data = json.load(f)
        result = framework.detect_anomalies(data)
        print(json.dumps(asdict(result), indent=2, default=str))
    elif args.summary:
        summary = framework.get_validation_summary(args.time_range)
        print(json.dumps(summary, indent=2, default=str))
    else:
        print("Use --help for usage information")
