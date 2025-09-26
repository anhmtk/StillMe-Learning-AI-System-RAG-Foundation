#!/usr/bin/env python3
"""
StillMe Collaborative Learning System
====================================

Learn from community datasets with safety-first validation.

Author: StillMe AI Framework Team
Version: 1.0.0
Status: EXPERIMENTAL
"""

import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class DatasetSource(Enum):
    """Sources of community datasets"""
    COMMUNITY_CONTRIBUTION = "community_contribution"
    OPEN_SOURCE = "open_source"
    RESEARCH_DATASET = "research_dataset"
    BENCHMARK_DATASET = "benchmark_dataset"

class ValidationStatus(Enum):
    """Validation status for community datasets"""
    PENDING = "pending"
    VALIDATING = "validating"
    APPROVED = "approved"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"

@dataclass
class CommunityDataset:
    """Community dataset metadata"""
    dataset_id: str
    name: str
    description: str
    source: str
    contributor: str
    file_path: str
    file_hash: str
    size_bytes: int
    record_count: int
    validation_status: str
    validation_timestamp: str
    validation_errors: List[str]
    ethics_score: float
    quality_score: float
    safety_flags: List[str]

@dataclass
class ValidationResult:
    """Result of dataset validation"""
    dataset_id: str
    validation_status: str
    ethics_score: float
    quality_score: float
    safety_flags: List[str]
    validation_errors: List[str]
    validation_timestamp: str
    validator_version: str

class CollaborativeLearning:
    """
    Collaborative learning system that safely integrates community datasets.
    
    Features:
    - Community dataset ingestion with validation
    - Ethics and safety checks before integration
    - Quality scoring and filtering
    - Audit trail for all merges
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logger
        
        # Storage
        self.community_datasets: Dict[str, CommunityDataset] = {}
        self.validation_results: List[ValidationResult] = []
        self.merge_history: List[Dict[str, Any]] = []
        
        # Configuration
        self.datasets_path = Path("datasets/community")
        self.datasets_path.mkdir(exist_ok=True)
        
        self.logs_path = Path("logs")
        self.logs_path.mkdir(exist_ok=True)
        
        # Validation thresholds
        self.validation_thresholds = {
            "min_ethics_score": 0.9,      # 90% ethics compliance required
            "min_quality_score": 0.8,     # 80% quality score required
            "max_safety_flags": 0,        # No safety flags allowed
            "min_record_count": 10,       # Minimum 10 records
            "max_file_size_mb": 100       # Maximum 100MB file size
        }
        
        # Import validation components (these would be actual imports in production)
        self.ethics_guard = None  # Would import EthicsGuard
        self.metrics_collector = None  # Would import LearningMetricsCollector
        
        self.logger.info("✅ CollaborativeLearning initialized (EXPERIMENTAL)")
    
    async def ingest_community_dataset(
        self,
        file_path: str,
        name: str,
        description: str,
        contributor: str,
        source: DatasetSource = DatasetSource.COMMUNITY_CONTRIBUTION
    ) -> Tuple[bool, str, Optional[CommunityDataset]]:
        """
        Ingest a community dataset with validation.
        
        Args:
            file_path: Path to the dataset file
            name: Dataset name
            description: Dataset description
            contributor: Contributor identifier
            source: Dataset source type
            
        Returns:
            Tuple of (success, message, dataset_object)
        """
        try:
            # Generate dataset ID
            dataset_id = self._generate_dataset_id(name, contributor)
            
            # Check if dataset already exists
            if dataset_id in self.community_datasets:
                return False, "Dataset already exists", None
            
            # Validate file
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return False, "File not found", None
            
            # Calculate file hash and size
            file_hash = self._calculate_file_hash(file_path)
            file_size = file_path_obj.stat().st_size
            
            # Check file size limit
            if file_size > self.validation_thresholds["max_file_size_mb"] * 1024 * 1024:
                return False, f"File too large ({file_size / 1024 / 1024:.1f}MB > {self.validation_thresholds['max_file_size_mb']}MB)", None
            
            # Create dataset object
            dataset = CommunityDataset(
                dataset_id=dataset_id,
                name=name,
                description=description,
                source=source.value,
                contributor=contributor,
                file_path=str(file_path_obj.absolute()),
                file_hash=file_hash,
                size_bytes=file_size,
                record_count=0,  # Will be calculated during validation
                validation_status=ValidationStatus.PENDING.value,
                validation_timestamp="",
                validation_errors=[],
                ethics_score=0.0,
                quality_score=0.0,
                safety_flags=[]
            )
            
            # Validate dataset
            validation_result = await self._validate_dataset(dataset)
            
            # Update dataset with validation results
            dataset.validation_status = validation_result.validation_status
            dataset.validation_timestamp = validation_result.validation_timestamp
            dataset.validation_errors = validation_result.validation_errors
            dataset.ethics_score = validation_result.ethics_score
            dataset.quality_score = validation_result.quality_score
            dataset.safety_flags = validation_result.safety_flags
            
            # Store dataset
            self.community_datasets[dataset_id] = dataset
            self.validation_results.append(validation_result)
            
            # Log validation result
            await self._log_validation_result(dataset, validation_result)
            
            if validation_result.validation_status == ValidationStatus.APPROVED.value:
                self.logger.info(f"✅ Dataset {name} approved for integration")
                return True, "Dataset approved for integration", dataset
            else:
                self.logger.warning(f"❌ Dataset {name} rejected: {', '.join(validation_result.validation_errors)}")
                return False, f"Dataset rejected: {', '.join(validation_result.validation_errors)}", dataset
                
        except Exception as e:
            self.logger.error(f"Error ingesting dataset {name}: {e}")
            return False, f"Error ingesting dataset: {str(e)}", None
    
    async def merge_approved_dataset(
        self,
        dataset_id: str,
        target_path: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Merge an approved dataset into the learning system.
        
        Args:
            dataset_id: Dataset ID to merge
            target_path: Optional target path for merge
            
        Returns:
            Tuple of (success, message)
        """
        if dataset_id not in self.community_datasets:
            return False, "Dataset not found"
        
        dataset = self.community_datasets[dataset_id]
        
        if dataset.validation_status != ValidationStatus.APPROVED.value:
            return False, f"Dataset not approved (status: {dataset.validation_status})"
        
        try:
            # Perform merge
            merge_result = await self._perform_merge(dataset, target_path)
            
            # Record merge in history
            merge_record = {
                "timestamp": datetime.now().isoformat(),
                "dataset_id": dataset_id,
                "dataset_name": dataset.name,
                "contributor": dataset.contributor,
                "merge_result": merge_result,
                "target_path": target_path
            }
            
            self.merge_history.append(merge_record)
            
            # Log merge
            await self._log_merge(merge_record)
            
            self.logger.info(f"✅ Successfully merged dataset {dataset.name}")
            return True, "Dataset merged successfully"
            
        except Exception as e:
            self.logger.error(f"Error merging dataset {dataset.name}: {e}")
            return False, f"Error merging dataset: {str(e)}"
    
    async def get_validation_status(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get validation status for a dataset"""
        if dataset_id not in self.community_datasets:
            return None
        
        dataset = self.community_datasets[dataset_id]
        
        return {
            "dataset_id": dataset_id,
            "name": dataset.name,
            "validation_status": dataset.validation_status,
            "ethics_score": dataset.ethics_score,
            "quality_score": dataset.quality_score,
            "safety_flags": dataset.safety_flags,
            "validation_errors": dataset.validation_errors,
            "validation_timestamp": dataset.validation_timestamp
        }
    
    async def list_community_datasets(
        self,
        status_filter: Optional[ValidationStatus] = None
    ) -> List[Dict[str, Any]]:
        """List community datasets with optional status filter"""
        datasets = []
        
        for dataset_id, dataset in self.community_datasets.items():
            if status_filter and dataset.validation_status != status_filter.value:
                continue
            
            datasets.append({
                "dataset_id": dataset_id,
                "name": dataset.name,
                "description": dataset.description,
                "contributor": dataset.contributor,
                "source": dataset.source,
                "validation_status": dataset.validation_status,
                "ethics_score": dataset.ethics_score,
                "quality_score": dataset.quality_score,
                "record_count": dataset.record_count,
                "size_bytes": dataset.size_bytes,
                "validation_timestamp": dataset.validation_timestamp
            })
        
        return datasets
    
    async def _validate_dataset(self, dataset: CommunityDataset) -> ValidationResult:
        """Validate a community dataset"""
        validation_errors = []
        safety_flags = []
        
        # Parse and validate file content
        try:
            records = await self._parse_dataset_file(dataset.file_path)
            dataset.record_count = len(records)
            
            if dataset.record_count < self.validation_thresholds["min_record_count"]:
                validation_errors.append(f"Insufficient records ({dataset.record_count} < {self.validation_thresholds['min_record_count']})")
            
        except Exception as e:
            validation_errors.append(f"File parsing error: {str(e)}")
            records = []
        
        # Ethics validation (mock implementation)
        ethics_score = await self._validate_ethics(records)
        if ethics_score < self.validation_thresholds["min_ethics_score"]:
            validation_errors.append(f"Low ethics score ({ethics_score:.2f} < {self.validation_thresholds['min_ethics_score']})")
        
        # Quality validation (mock implementation)
        quality_score = await self._validate_quality(records)
        if quality_score < self.validation_thresholds["min_quality_score"]:
            validation_errors.append(f"Low quality score ({quality_score:.2f} < {self.validation_thresholds['min_quality_score']})")
        
        # Safety validation (mock implementation)
        safety_flags = await self._validate_safety(records)
        if len(safety_flags) > self.validation_thresholds["max_safety_flags"]:
            validation_errors.append(f"Safety flags detected: {', '.join(safety_flags)}")
        
        # Determine validation status
        if not validation_errors:
            validation_status = ValidationStatus.APPROVED.value
        else:
            validation_status = ValidationStatus.REJECTED.value
        
        return ValidationResult(
            dataset_id=dataset.dataset_id,
            validation_status=validation_status,
            ethics_score=ethics_score,
            quality_score=quality_score,
            safety_flags=safety_flags,
            validation_errors=validation_errors,
            validation_timestamp=datetime.now().isoformat(),
            validator_version="1.0.0"
        )
    
    async def _parse_dataset_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse dataset file (supports JSONL format)"""
        records = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    record = json.loads(line)
                    records.append(record)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Invalid JSON on line {line_num}: {e}")
                    continue
        
        return records
    
    async def _validate_ethics(self, records: List[Dict[str, Any]]) -> float:
        """Validate ethics compliance (mock implementation)"""
        if not records:
            return 0.0
        
        # Mock ethics validation
        # In production, this would use EthicsGuard
        ethics_violations = 0
        
        for record in records:
            # Check for harmful content (simplified)
            content = str(record).lower()
            if any(keyword in content for keyword in ["harmful", "violence", "hate", "discrimination"]):
                ethics_violations += 1
        
        ethics_score = max(0.0, 1.0 - (ethics_violations / len(records)))
        return ethics_score
    
    async def _validate_quality(self, records: List[Dict[str, Any]]) -> float:
        """Validate data quality (mock implementation)"""
        if not records:
            return 0.0
        
        # Mock quality validation
        quality_issues = 0
        
        for record in records:
            # Check for required fields
            if not isinstance(record, dict):
                quality_issues += 1
                continue
            
            # Check for minimum required fields
            required_fields = ["input", "expected_output"]
            if not all(field in record for field in required_fields):
                quality_issues += 1
                continue
            
            # Check for empty or invalid content
            if not record.get("input") or not record.get("expected_output"):
                quality_issues += 1
        
        quality_score = max(0.0, 1.0 - (quality_issues / len(records)))
        return quality_score
    
    async def _validate_safety(self, records: List[Dict[str, Any]]) -> List[str]:
        """Validate safety (mock implementation)"""
        safety_flags = []
        
        for record in records:
            content = str(record).lower()
            
            # Check for potential security issues
            if "password" in content or "secret" in content:
                safety_flags.append("potential_credential_exposure")
            
            if "sql" in content and "injection" in content:
                safety_flags.append("potential_sql_injection")
            
            if "eval(" in content or "exec(" in content:
                safety_flags.append("potential_code_injection")
        
        return list(set(safety_flags))  # Remove duplicates
    
    async def _perform_merge(self, dataset: CommunityDataset, target_path: Optional[str]) -> Dict[str, Any]:
        """Perform the actual merge operation (mock implementation)"""
        # In production, this would integrate with the learning system
        merge_result = {
            "records_merged": dataset.record_count,
            "merge_timestamp": datetime.now().isoformat(),
            "target_path": target_path or "default_learning_path",
            "merge_method": "append",
            "backup_created": True
        }
        
        return merge_result
    
    async def _log_validation_result(self, dataset: CommunityDataset, result: ValidationResult):
        """Log validation result"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "dataset_validation",
            "dataset_id": dataset.dataset_id,
            "dataset_name": dataset.name,
            "contributor": dataset.contributor,
            "validation_status": result.validation_status,
            "ethics_score": result.ethics_score,
            "quality_score": result.quality_score,
            "safety_flags": result.safety_flags,
            "validation_errors": result.validation_errors
        }
        
        await self._write_log_entry(log_entry)
    
    async def _log_merge(self, merge_record: Dict[str, Any]):
        """Log merge operation"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "dataset_merge",
            **merge_record
        }
        
        await self._write_log_entry(log_entry)
    
    async def _write_log_entry(self, log_entry: Dict[str, Any]):
        """Write log entry to file"""
        log_file = self.logs_path / "collab_learning.log"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def _generate_dataset_id(self, name: str, contributor: str) -> str:
        """Generate unique dataset ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_hash = hashlib.md5(name.encode()).hexdigest()[:8]
        contributor_hash = hashlib.md5(contributor.encode()).hexdigest()[:8]
        
        return f"dataset_{timestamp}_{name_hash}_{contributor_hash}"
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics"""
        total_datasets = len(self.community_datasets)
        
        if total_datasets == 0:
            return {"total_datasets": 0}
        
        status_counts = {}
        for dataset in self.community_datasets.values():
            status = dataset.validation_status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        avg_ethics_score = sum(d.ethics_score for d in self.community_datasets.values()) / total_datasets
        avg_quality_score = sum(d.quality_score for d in self.community_datasets.values()) / total_datasets
        
        return {
            "total_datasets": total_datasets,
            "status_distribution": status_counts,
            "avg_ethics_score": avg_ethics_score,
            "avg_quality_score": avg_quality_score,
            "total_merges": len(self.merge_history)
        }
