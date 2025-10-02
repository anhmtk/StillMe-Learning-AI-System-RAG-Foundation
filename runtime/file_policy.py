#!/usr/bin/env python3
"""
StillMe File Protection Policy Loader (Python)
Bắt buộc nạp file protection policy ở mọi entrypoint

Purpose: Đảm bảo tất cả entrypoints đều tuân thủ FILE_PROTECTION.yaml
Usage: Gọi load_file_policy() ở đầu mọi entrypoint
"""

import logging
import os
import re
import shutil
from datetime import datetime
from typing import Any, Optional

import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global policy instance
_policy: Optional[dict[str, Any]] = None
_policy_loaded = False

def load_file_policy(policy_path: Optional[str] = None) -> dict[str, Any]:
    """
    Load File Protection Policy từ YAML file

    Args:
        policy_path: Đường dẫn đến policy file (mặc định: policies/FILE_PROTECTION.yaml)

    Returns:
        Dict[str, Any]: FileProtectionPolicy object

    Raises:
        FileNotFoundError: Nếu không tìm thấy policy file
        yaml.YAMLError: Nếu không parse được YAML
        ValueError: Nếu policy không hợp lệ
    """
    global _policy, _policy_loaded

    if _policy_loaded and _policy:
        return _policy

    # Default path
    if policy_path is None:
        policy_path = os.path.join(os.getcwd(), 'policies', 'FILE_PROTECTION.yaml')

    try:
        # Check if policy file exists
        if not os.path.exists(policy_path):
            raise FileNotFoundError(f"File Protection Policy file not found: {policy_path}")

        # Read and parse YAML
        with open(policy_path, encoding='utf-8') as file:
            policy = yaml.safe_load(file)

        # Validate policy structure
        _validate_policy(policy)

        # Cache policy
        _policy = policy
        _policy_loaded = True

        logger.info(f"✅ File Protection Policy loaded successfully from: {policy_path}")
        logger.info(f"📋 Policy version: {policy['version']}")
        logger.info(f"🔒 Protected files: {len(policy['protected_files'])}")
        logger.info(f"🛡️ Protection enabled: {policy['enforcement']['runtime']['enabled']}")

        return policy

    except Exception as error:
        error_message = f"Failed to load File Protection Policy from {policy_path}: {error}"
        logger.error(f"❌ {error_message}")
        raise ValueError(error_message)

def _validate_policy(policy: dict[str, Any]) -> None:
    """
    Validate policy structure

    Args:
        policy: Policy object to validate

    Raises:
        ValueError: Nếu policy không hợp lệ
    """
    required_fields = [
        'version', 'metadata', 'protected_files', 'rules', 'commit',
        'messages', 'validation', 'backup', 'monitoring', 'compliance'
    ]

    for field in required_fields:
        if field not in policy:
            raise ValueError(f"Missing required field in policy: {field}")

    # Validate protected files
    if not policy['protected_files']:
        raise ValueError("No protected files defined in policy")

    # Validate rules
    required_operations = ['delete', 'rename', 'move', 'modify', 'copy', 'read']
    for operation in required_operations:
        if operation not in policy['rules']:
            raise ValueError(f"Missing rule for operation: {operation}")

def get_file_policy() -> dict[str, Any]:
    """
    Get cached policy (must be loaded first)

    Returns:
        Dict[str, Any]: FileProtectionPolicy object

    Raises:
        ValueError: Nếu policy chưa được load
    """
    if not _policy_loaded or not _policy:
        raise ValueError("File Protection Policy not loaded. Call load_file_policy() first.")
    return _policy

def is_policy_loaded() -> bool:
    """
    Check if policy is loaded

    Returns:
        bool: True nếu policy đã được load
    """
    return _policy_loaded and _policy is not None

def reset_policy_cache() -> None:
    """
    Reset policy cache (for testing)
    """
    global _policy, _policy_loaded
    _policy = None
    _policy_loaded = False

def is_protected_file(file_path: str) -> bool:
    """
    Check if file is protected

    Args:
        file_path: Path to file to check

    Returns:
        bool: True nếu file được bảo vệ
    """
    policy = get_file_policy()
    file_name = os.path.basename(file_path)

    return file_name in policy['protected_files']

def assert_protected_files(action: str, file_paths: list[str]) -> None:
    """
    Assert that protected files are not being modified

    Args:
        action: Action being performed ('delete', 'rename', 'move', 'modify')
        file_paths: List of file paths being affected

    Raises:
        ValueError: Nếu vi phạm policy
    """
    policy = get_file_policy()

    for file_path in file_paths:
        if is_protected_file(file_path):
            rule = policy['rules'].get(action, {})

            if rule.get('action') == 'deny':
                message = policy['messages'].get(f'{action}_violation_vi',
                                               f'Cannot {action} protected file: {file_path}')
                raise ValueError(message)

            elif rule.get('action') == 'require_approval':
                if not rule.get('require_approval', False):
                    message = policy['messages'].get(f'{action}_violation_vi',
                                                   f'Approval required to {action} protected file: {file_path}')
                    raise ValueError(message)

def validate_env_file(file_path: str) -> tuple[bool, list[str]]:
    """
    Validate .env file content

    Args:
        file_path: Path to .env file

    Returns:
        Tuple[bool, List[str]]: (is_valid, error_messages)
    """
    policy = get_file_policy()
    validation = policy['validation']
    errors = []

    try:
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > validation['file_size_limit']:
            errors.append(f"File size {file_size} exceeds limit {validation['file_size_limit']}")

        # Read and validate content
        with open(file_path, encoding='utf-8') as f:
            lines = f.readlines()

            if len(lines) > validation['line_limit']:
                errors.append(f"Line count {len(lines)} exceeds limit {validation['line_limit']}")

            # Check required keys
            content = ''.join(lines)
            for required_key in validation['required_keys']:
                if required_key not in content:
                    errors.append(f"Missing required key: {required_key}")

            # Validate key patterns
            for line in lines:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    if key in validation['key_patterns']:
                        pattern = validation['key_patterns'][key]
                        if not re.match(pattern, value):
                            errors.append(f"Invalid pattern for {key}: {value}")

        return len(errors) == 0, errors

    except Exception as e:
        return False, [f"Validation error: {e}"]

def create_backup(file_path: str, operation: str = 'manual') -> str:
    """
    Create backup of protected file

    Args:
        file_path: Path to file to backup
        operation: Operation that triggered backup

    Returns:
        str: Path to backup file
    """
    policy = get_file_policy()
    backup_config = policy['backup']

    if not backup_config['enabled']:
        return None

    # Create backup directory
    backup_dir = backup_config['directory']
    os.makedirs(backup_dir, exist_ok=True)

    # Generate backup filename
    timestamp = datetime.now().strftime(backup_config['naming_pattern'].split('.')[-2])
    backup_filename = backup_config['naming_pattern'].format(
        timestamp=timestamp,
        operation=operation
    )
    backup_path = os.path.join(backup_dir, backup_filename)

    try:
        # Copy file to backup
        shutil.copy2(file_path, backup_path)

        # Compress if enabled
        if backup_config['compression']:
            import gzip
            with open(backup_path, 'rb') as f_in:
                with gzip.open(f"{backup_path}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(backup_path)
            backup_path = f"{backup_path}.gz"

        # Cleanup old backups
        _cleanup_old_backups(backup_dir, backup_config['max_backups'])

        logger.info(f"✅ Created backup: {backup_path}")
        return backup_path

    except Exception as e:
        logger.error(f"❌ Failed to create backup: {e}")
        raise

def _cleanup_old_backups(backup_dir: str, max_backups: int) -> None:
    """
    Cleanup old backup files

    Args:
        backup_dir: Backup directory path
        max_backups: Maximum number of backups to keep
    """
    try:
        backup_files = []
        for filename in os.listdir(backup_dir):
            if filename.startswith('.env.backup.'):
                file_path = os.path.join(backup_dir, filename)
                backup_files.append((file_path, os.path.getmtime(file_path)))

        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x[1], reverse=True)

        # Remove old backups
        for file_path, _ in backup_files[max_backups:]:
            os.remove(file_path)
            logger.info(f"🗑️ Removed old backup: {file_path}")

    except Exception as e:
        logger.error(f"❌ Failed to cleanup old backups: {e}")

def get_protected_files() -> list[str]:
    """
    Get list of protected files

    Returns:
        List[str]: List of protected file names
    """
    policy = get_file_policy()
    return policy['protected_files']

def get_commit_rules() -> dict[str, str]:
    """
    Get commit rules for protected files

    Returns:
        Dict[str, str]: Commit rules (file_name -> action)
    """
    policy = get_file_policy()
    return policy['commit']

def get_validation_rules() -> dict[str, Any]:
    """
    Get validation rules

    Returns:
        Dict[str, Any]: Validation rules
    """
    policy = get_file_policy()
    return policy['validation']

def get_backup_config() -> dict[str, Any]:
    """
    Get backup configuration

    Returns:
        Dict[str, Any]: Backup configuration
    """
    policy = get_file_policy()
    return policy['backup']

def get_monitoring_config() -> dict[str, Any]:
    """
    Get monitoring configuration

    Returns:
        Dict[str, Any]: Monitoring configuration
    """
    policy = get_file_policy()
    return policy['monitoring']

def get_compliance_config() -> dict[str, Any]:
    """
    Get compliance configuration

    Returns:
        Dict[str, Any]: Compliance configuration
    """
    policy = get_file_policy()
    return policy['compliance']

def ensure_policy_loaded() -> None:
    """
    Ensure policy is loaded, auto-load if not

    Raises:
        ValueError: Nếu không thể load policy
    """
    if not is_policy_loaded():
        try:
            load_file_policy()
        except Exception as e:
            raise ValueError(f"Failed to auto-load File Protection Policy: {e}")

# Auto-load policy on module import
try:
    load_file_policy()
except Exception as e:
    logger.warning(f"⚠️ Could not auto-load File Protection Policy: {e}")
    logger.warning("⚠️ Make sure to call load_file_policy() manually in your entrypoint")

# Export for easy import
__all__ = [
    'load_file_policy',
    'get_file_policy',
    'is_policy_loaded',
    'reset_policy_cache',
    'is_protected_file',
    'assert_protected_files',
    'validate_env_file',
    'create_backup',
    'get_protected_files',
    'get_commit_rules',
    'get_validation_rules',
    'get_backup_config',
    'get_monitoring_config',
    'get_compliance_config',
    'ensure_policy_loaded'
]
