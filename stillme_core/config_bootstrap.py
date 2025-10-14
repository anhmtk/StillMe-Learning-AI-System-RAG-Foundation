#!/usr/bin/env python3
"""
Config Bootstrap Module
=======================

Tự động tạo các file cấu hình mẫu khi thiếu để đảm bảo framework có thể chạy ngay.
Module này được thiết kế để chạy sớm trong quá trình khởi tạo framework.
"""

import os
import pathlib
import yaml
from typing import Dict, Any, Optional


def ensure_minimum_config() -> None:
    """
    Đảm bảo các file cấu hình tối thiểu tồn tại.
    Tạo file mẫu nếu thiếu, không ghi đè file đã có.
    """
    config_dir = pathlib.Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # Danh sách các file cấu hình cần thiết
    required_configs = {
        "reflection.yaml": _get_reflection_config(),
        "runtime_base_url.txt": "http://localhost:8000",
        "env/dev.yaml": _get_dev_config(),
        "env/prod.yaml": _get_prod_config(),
        "env/staging.yaml": _get_staging_config(),
    }
    
    created_files = []
    
    for config_path, content in required_configs.items():
        full_path = config_dir / config_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not full_path.exists():
            _create_config_file(full_path, content)
            created_files.append(str(full_path))
    
    # Tạo .env từ env.example nếu chưa có
    env_path = pathlib.Path(".env")
    env_example_path = pathlib.Path("env.example")
    
    if not env_path.exists() and env_example_path.exists():
        _create_env_from_example(env_example_path, env_path)
        created_files.append(str(env_path))
    
    # Log kết quả
    if created_files:
        print(f"🔧 Config bootstrap: Created {len(created_files)} sample config files")
        for file_path in created_files:
            print(f"   📄 {file_path}")
        print("   ⚠️  Please review and edit these files as needed")
    else:
        print("✅ Config bootstrap: All required config files exist")


def _create_config_file(file_path: pathlib.Path, content: Any) -> None:
    """Tạo file cấu hình với nội dung mẫu"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    if file_path.suffix == '.yaml' or file_path.suffix == '.yml':
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# GENERATED SAMPLE CONFIG - PLEASE EDIT\n")
            f.write("# This file was automatically created by config bootstrap\n")
            f.write("# Please review and customize the values below\n\n")
            yaml.dump(content, f, default_flow_style=False, allow_unicode=True)
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# GENERATED SAMPLE CONFIG - PLEASE EDIT\n")
            f.write("# This file was automatically created by config bootstrap\n")
            f.write("# Please review and customize the value below\n\n")
            f.write(str(content))


def _create_env_from_example(example_path: pathlib.Path, env_path: pathlib.Path) -> None:
    """Tạo .env từ env.example"""
    with open(example_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Thêm header cho .env
    env_content = "# GENERATED FROM env.example - PLEASE EDIT\n"
    env_content += "# This file was automatically created by config bootstrap\n"
    env_content += "# Please review and customize the values below\n\n"
    env_content += content
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)


def _get_reflection_config() -> Dict[str, Any]:
    """Cấu hình reflection mẫu"""
    return {
        "reflection": {
            "enabled": True,
            "interval_minutes": 30,
            "max_entries": 1000,
            "auto_cleanup": True
        },
        "learning": {
            "enabled": True,
            "adaptive_mode": True,
            "feedback_weight": 0.7
        },
        "safety": {
            "content_filtering": True,
            "pii_redaction": True,
            "rate_limiting": True
        }
    }


def _get_dev_config() -> Dict[str, Any]:
    """Cấu hình development mẫu"""
    return {
        "environment": "development",
        "debug": True,
        "log_level": "DEBUG",
        "api_keys": {
            "openai": "sk-dev-xxxx",
            "openrouter": "sk-or-dev-xxxx"
        },
        "services": {
            "ollama": {
                "base_url": "http://localhost:11434",
                "model_fast": "llama3.2:3b",
                "model_safe": "llama3.2:3b"
            }
        },
        "features": {
            "dry_run": True,
            "mock_providers": True,
            "offline_mode": True
        }
    }


def _get_prod_config() -> Dict[str, Any]:
    """Cấu hình production mẫu"""
    return {
        "environment": "production",
        "debug": False,
        "log_level": "INFO",
        "api_keys": {
            "openai": "sk-prod-xxxx",
            "openrouter": "sk-or-prod-xxxx"
        },
        "services": {
            "ollama": {
                "base_url": "http://ollama-server:11434",
                "model_fast": "llama3.2:7b",
                "model_safe": "llama3.2:7b"
            }
        },
        "features": {
            "dry_run": False,
            "mock_providers": False,
            "offline_mode": False
        },
        "security": {
            "rate_limiting": True,
            "content_filtering": True,
            "pii_redaction": True
        }
    }


def _get_staging_config() -> Dict[str, Any]:
    """Cấu hình staging mẫu"""
    return {
        "environment": "staging",
        "debug": True,
        "log_level": "INFO",
        "api_keys": {
            "openai": "sk-staging-xxxx",
            "openrouter": "sk-or-staging-xxxx"
        },
        "services": {
            "ollama": {
                "base_url": "http://staging-ollama:11434",
                "model_fast": "llama3.2:3b",
                "model_safe": "llama3.2:3b"
            }
        },
        "features": {
            "dry_run": True,
            "mock_providers": False,
            "offline_mode": False
        }
    }


def check_config_health() -> Dict[str, Any]:
    """
    Kiểm tra tình trạng cấu hình và trả về báo cáo.
    """
    config_dir = pathlib.Path("config")
    health_report = {
        "config_dir_exists": config_dir.exists(),
        "required_files": {},
        "env_file_exists": pathlib.Path(".env").exists(),
        "env_example_exists": pathlib.Path("env.example").exists(),
        "issues": []
    }
    
    required_files = [
        "reflection.yaml",
        "runtime_base_url.txt",
        "env/dev.yaml",
        "env/prod.yaml", 
        "env/staging.yaml"
    ]
    
    for file_name in required_files:
        file_path = config_dir / file_name
        health_report["required_files"][file_name] = {
            "exists": file_path.exists(),
            "readable": file_path.exists() and file_path.is_file()
        }
        
        if not file_path.exists():
            health_report["issues"].append(f"Missing config file: {file_name}")
    
    if not health_report["env_file_exists"] and health_report["env_example_exists"]:
        health_report["issues"].append("Missing .env file (env.example exists)")
    
    return health_report


if __name__ == "__main__":
    # Chạy bootstrap khi gọi trực tiếp
    ensure_minimum_config()
    
    # In báo cáo health
    health = check_config_health()
    print(f"\n📊 Config Health Report:")
    print(f"   Config dir exists: {health['config_dir_exists']}")
    print(f"   .env file exists: {health['env_file_exists']}")
    print(f"   Issues found: {len(health['issues'])}")
    
    if health['issues']:
        print("   ⚠️  Issues:")
        for issue in health['issues']:
            print(f"      - {issue}")
    else:
        print("   ✅ All config files are healthy")
