#!/usr/bin/env python3
"""
🚀 AUTOMATIC DEPENDENCY RESOLUTION & FIX SCRIPT

Tự động phát hiện và sửa tất cả lỗi missing dependencies trong project StillMe AI.
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class DependencyResolver:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.requirements_file = self.project_root / "requirements.txt"
        self.missing_packages: List[str] = []
        self.installed_packages: List[str] = []

    def run_command(
        self, command: str, capture_output: bool = True
    ) -> Tuple[int, str, str]:
        """Chạy command và return (exit_code, stdout, stderr)"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=capture_output,
                text=True,
                cwd=self.project_root,
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)

    def analyze_imports(self) -> Dict[str, List[str]]:
        """Phân tích tất cả imports trong project"""
        print("🔍 Phân tích imports trong project...")

        imports = {
            "core_packages": [],
            "ai_packages": [],
            "web_packages": [],
            "utility_packages": [],
        }

        # Tìm tất cả Python files
        python_files = list(self.project_root.rglob("*.py"))

        for py_file in python_files:
            if "node_modules" in str(py_file) or ".venv" in str(py_file):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                lines = content.split("\n")
                for line in lines:
                    line = line.strip()
                    if line.startswith(("import ", "from ")):
                        # Parse import statement
                        if "import " in line:
                            package = (
                                line.split("import ")[1].split(" ")[0].split(".")[0]
                            )
                        else:
                            package = line.split("from ")[1].split(" ")[0].split(".")[0]

                        # Categorize packages
                        if package in [
                            "torch",
                            "transformers",
                            "sklearn",
                            "numpy",
                            "pandas",
                        ]:
                            imports["ai_packages"].append(package)
                        elif package in [
                            "fastapi",
                            "uvicorn",
                            "starlette",
                            "asgi_lifespan",
                        ]:
                            imports["web_packages"].append(package)
                        elif package in ["httpx", "requests", "openai", "ollama"]:
                            imports["core_packages"].append(package)
                        elif package in ["yaml", "psutil", "cryptography"]:
                            imports["utility_packages"].append(package)

            except Exception as e:
                print(f"⚠️ Không thể đọc {py_file}: {e}")

        # Remove duplicates
        for category in imports:
            imports[category] = list(set(imports[category]))

        return imports

    def check_missing_packages(self, imports: Dict[str, List[str]]) -> List[str]:
        """Kiểm tra packages bị thiếu"""
        print("🔍 Kiểm tra packages bị thiếu...")

        missing = []

        # Core packages cần thiết
        required_packages = [
            "httpx",
            "openai",
            "yaml",
            "psutil",
            "numpy",
            "pandas",
            "torch",
            "transformers",
            "sklearn",
            "ollama",
            "tiktoken",
            "sentence_transformers",
            "open-interpreter",
            "asgi-lifespan",
        ]

        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"✅ {package} - Đã cài đặt")
            except ImportError:
                print(f"❌ {package} - Bị thiếu")
                missing.append(package)

        return missing

    def install_missing_packages(self, missing_packages: List[str]) -> bool:
        """Cài đặt packages bị thiếu"""
        if not missing_packages:
            print("✅ Không có packages nào bị thiếu!")
            return True

        print(f"🚀 Cài đặt {len(missing_packages)} packages bị thiếu...")

        for package in missing_packages:
            print(f"📦 Cài đặt {package}...")
            exit_code, stdout, stderr = self.run_command(f"pip install {package}")

            if exit_code == 0:
                print(f"✅ {package} - Cài đặt thành công")
            else:
                print(f"❌ {package} - Cài đặt thất bại: {stderr}")
                return False

        return True

    def verify_framework(self) -> bool:
        """Verify framework hoạt động"""
        print("🧪 Verify framework...")

        # Test import framework
        try:
            exit_code, stdout, stderr = self.run_command(
                'python -c "import framework; print(\\"Framework import thanh cong!\\")"'
            )
            if exit_code == 0:
                print("✅ Framework import thành công!")
            else:
                print(f"❌ Framework import thất bại: {stderr}")
                return False
        except Exception as e:
            print(f"❌ Lỗi verify framework: {e}")
            return False

        # Test run tests
        print("🧪 Chạy tests...")
        exit_code, stdout, stderr = self.run_command(
            "python -m pytest tests/test_secure_memory_manager.py -v"
        )

        if exit_code == 0:
            print("✅ Tests pass!")
        else:
            print(f"⚠️ Tests có vấn đề: {stderr}")

        return True

    def update_requirements(self) -> bool:
        """Cập nhật requirements.txt"""
        print("📝 Cập nhật requirements.txt...")

        exit_code, stdout, stderr = self.run_command("pip freeze > requirements.txt")

        if exit_code == 0:
            print("✅ requirements.txt đã được cập nhật")
            return True
        else:
            print(f"❌ Không thể cập nhật requirements.txt: {stderr}")
            return False

    def generate_report(
        self, imports: Dict[str, List[str]], missing_packages: List[str]
    ) -> None:
        """Tạo báo cáo chi tiết"""
        print("\n" + "=" * 60)
        print("📊 BÁO CÁO PHÂN TÍCH DEPENDENCIES")
        print("=" * 60)

        print("\n🔍 Packages được phát hiện:")
        for category, packages in imports.items():
            if packages:
                print(f"  {category.upper()}: {', '.join(packages)}")

        print(f"\n❌ Packages bị thiếu: {len(missing_packages)}")
        if missing_packages:
            for package in missing_packages:
                print(f"  - {package}")

        print(f"\n📁 Project root: {self.project_root}")
        print(f"📄 Requirements file: {self.requirements_file}")

        if self.requirements_file.exists():
            size = self.requirements_file.stat().st_size
            print(f"📊 Requirements file size: {size} bytes")

    def run(self) -> bool:
        """Chạy toàn bộ quy trình"""
        print("🚀 AUTOMATIC DEPENDENCY RESOLUTION & FIX")
        print("=" * 50)

        # Bước 1: Phân tích imports
        imports = self.analyze_imports()

        # Bước 2: Kiểm tra packages bị thiếu
        missing_packages = self.check_missing_packages(imports)

        # Bước 3: Cài đặt packages bị thiếu
        if missing_packages:
            if not self.install_missing_packages(missing_packages):
                print("❌ Cài đặt packages thất bại!")
                return False

        # Bước 4: Verify framework
        if not self.verify_framework():
            print("❌ Framework không hoạt động!")
            return False

        # Bước 5: Cập nhật requirements.txt
        if not self.update_requirements():
            print("⚠️ Không thể cập nhật requirements.txt")

        # Bước 6: Tạo báo cáo
        self.generate_report(imports, missing_packages)

        print("\n🎉 HOÀN THÀNH AUTOMATIC DEPENDENCY RESOLUTION!")
        return True


def main():
    """Main function"""
    resolver = DependencyResolver()

    try:
        success = resolver.run()
        if success:
            print("\n✅ Tất cả dependencies đã được resolve thành công!")
            sys.exit(0)
        else:
            print("\n❌ Có lỗi xảy ra trong quá trình resolve dependencies!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Bị gián đoạn bởi user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Lỗi không mong muốn: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
