#!/usr/bin/env python3
"""
StillMe Interaction Policy Loader (Python)
Bắt buộc nạp policy ở mọi entrypoint

Purpose: Đảm bảo tất cả entrypoints đều tuân thủ INTERACTION_POLICY.yaml
Usage: Gọi load_interaction_policy() ở đầu mọi entrypoint
"""

import os
import yaml
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global policy instance
_policy: Optional[Dict[str, Any]] = None
_policy_loaded = False

def load_interaction_policy(policy_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load Interaction Policy từ YAML file
    
    Args:
        policy_path: Đường dẫn đến policy file (mặc định: policies/INTERACTION_POLICY.yaml)
    
    Returns:
        Dict[str, Any]: InteractionPolicy object
    
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
        policy_path = os.path.join(os.getcwd(), 'policies', 'INTERACTION_POLICY.yaml')

    try:
        # Check if policy file exists
        if not os.path.exists(policy_path):
            raise FileNotFoundError(f"Interaction Policy file not found: {policy_path}")

        # Read and parse YAML
        with open(policy_path, 'r', encoding='utf-8') as file:
            policy = yaml.safe_load(file)

        # Validate policy structure
        _validate_policy(policy)

        # Cache policy
        _policy = policy
        _policy_loaded = True

        logger.info(f"✅ Interaction Policy loaded successfully from: {policy_path}")
        logger.info(f"📋 Policy version: {policy['version']}")
        logger.info(f"📝 Skip semantics: {policy['skip']['semantics']}")
        logger.info(f"🚫 Cancel on skip: {policy['skip']['cancel_on_skip']}")

        return policy

    except Exception as error:
        error_message = f"Failed to load Interaction Policy from {policy_path}: {error}"
        logger.error(f"❌ {error_message}")
        raise ValueError(error_message)

def _validate_policy(policy: Dict[str, Any]) -> None:
    """
    Validate policy structure
    
    Args:
        policy: Policy object to validate
    
    Raises:
        ValueError: Nếu policy không hợp lệ
    """
    required_fields = [
        'version', 'metadata', 'skip', 'cancel', 'abort', 'stop',
        'heartbeat', 'logs', 'pid', 'ui', 'compliance'
    ]

    for field in required_fields:
        if field not in policy:
            raise ValueError(f"Missing required field in policy: {field}")

    # Validate skip semantics
    if policy['skip']['semantics'] != 'diagnose':
        raise ValueError(f"Invalid skip semantics: {policy['skip']['semantics']}. Must be 'diagnose'")

    # Validate cancel_on_skip
    if policy['skip']['cancel_on_skip'] is not False:
        raise ValueError(f"Invalid cancel_on_skip: {policy['skip']['cancel_on_skip']}. Must be false")

    # Validate required outputs
    required_outputs = ['COMPLETED', 'RUNNING', 'STALLED', 'UNKNOWN']
    for output in required_outputs:
        if output not in policy['skip']['outputs']:
            raise ValueError(f"Missing required skip output: {output}")

def get_interaction_policy() -> Dict[str, Any]:
    """
    Get cached policy (must be loaded first)
    
    Returns:
        Dict[str, Any]: InteractionPolicy object
    
    Raises:
        ValueError: Nếu policy chưa được load
    """
    if not _policy_loaded or not _policy:
        raise ValueError("Interaction Policy not loaded. Call load_interaction_policy() first.")
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

def get_skip_button_config(language: str = 'en') -> Dict[str, Any]:
    """
    Get skip button configuration
    
    Args:
        language: Language code ('vi' or 'en')
    
    Returns:
        Dict[str, Any]: Skip button config
    """
    policy = get_interaction_policy()
    button = policy['ui']['skip_button']

    return {
        'text': button[f'text_{language}'],
        'tooltip': button[f'tooltip_{language}'],
        'icon': button['icon'],
        'semantics': policy['skip']['semantics'],
        'cancel_on_skip': policy['skip']['cancel_on_skip']
    }

def get_cancel_button_config(language: str = 'en') -> Dict[str, Any]:
    """
    Get cancel button configuration
    
    Args:
        language: Language code ('vi' or 'en')
    
    Returns:
        Dict[str, Any]: Cancel button config
    """
    policy = get_interaction_policy()
    button = policy['ui']['cancel_button']

    return {
        'text': button[f'text_{language}'],
        'tooltip': button[f'tooltip_{language}'],
        'icon': button['icon'],
        'semantics': policy['cancel']['semantics'],
        'require_confirmation': policy['cancel']['require_confirmation'],
        'confirmation_message': button[f'confirmation_message_{language}']
    }

def get_skip_prompt(state: str, language: str = 'en') -> str:
    """
    Get prompt for skip diagnosis result
    
    Args:
        state: Diagnosis state ('COMPLETED', 'RUNNING', 'STALLED', 'UNKNOWN')
        language: Language code ('vi' or 'en')
    
    Returns:
        str: Prompt message
    """
    policy = get_interaction_policy()
    key = f"{state.lower()}_{language}"
    return policy['skip']['prompts'].get(key, f"Unknown state: {state}")

def get_log_tailing_config() -> Dict[str, Any]:
    """
    Get log tailing configuration
    
    Returns:
        Dict[str, Any]: Log tailing config
    """
    policy = get_interaction_policy()
    return policy['skip']['log_tailing']

def get_heartbeat_config() -> Dict[str, Any]:
    """
    Get heartbeat configuration
    
    Returns:
        Dict[str, Any]: Heartbeat config
    """
    policy = get_interaction_policy()
    return policy['heartbeat']

def get_pid_config() -> Dict[str, Any]:
    """
    Get PID monitoring configuration
    
    Returns:
        Dict[str, Any]: PID config
    """
    policy = get_interaction_policy()
    return policy['pid']

def get_compliance_config() -> Dict[str, Any]:
    """
    Check compliance requirements
    
    Returns:
        Dict[str, Any]: Compliance config
    """
    policy = get_interaction_policy()
    return policy['compliance']

def ensure_policy_loaded() -> None:
    """
    Ensure policy is loaded, auto-load if not
    
    Raises:
        ValueError: Nếu không thể load policy
    """
    if not is_policy_loaded():
        try:
            load_interaction_policy()
        except Exception as e:
            raise ValueError(f"Failed to auto-load Interaction Policy: {e}")

# Auto-load policy on module import
try:
    load_interaction_policy()
except Exception as e:
    logger.warning(f"⚠️ Could not auto-load Interaction Policy: {e}")
    logger.warning("⚠️ Make sure to call load_interaction_policy() manually in your entrypoint")

# Export for easy import
__all__ = [
    'load_interaction_policy',
    'get_interaction_policy',
    'is_policy_loaded',
    'reset_policy_cache',
    'get_skip_button_config',
    'get_cancel_button_config',
    'get_skip_prompt',
    'get_log_tailing_config',
    'get_heartbeat_config',
    'get_pid_config',
    'get_compliance_config',
    'ensure_policy_loaded'
]
