
#!/usr/bin/env python3
"""
Protected Files Compliance Check
Ensures protected files are not modified or deleted
"""

import sys
from pathlib import Path


def get_protected_files() -> set[str]:
    """Get list of protected files"""
    protected = {
        ".env",
        ".env.local",
        ".env.production",
        "config/secrets.yaml",
        "config/production.yaml",
        "*.keystore",
        "*.pem",
        "*.key",
        "*.crt",
        "*.p12",
        "private_keys/",
        "secrets/",
        "certificates/"
    }

    # Add files from .gitignore that should be protected
    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        with open(gitignore_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    protected.add(line)

    return protected

def check_file_protection(file_path: Path, protected_patterns: set[str]) -> bool:
    """Check if file matches protected patterns"""
    file_str = str(file_path)

    for pattern in protected_patterns:
        if pattern.endswith('/'):
            # Directory pattern
            if pattern.rstrip('/') in file_str:
                return True
        elif '*' in pattern:
            # Wildcard pattern
            import fnmatch
            if fnmatch.fnmatch(file_path.name, pattern):
                return True
        else:
            # Exact match
            if file_path.name == pattern or file_str.endswith(pattern):
                return True

    return False

def check_git_status() -> list[str]:
    """Check git status for modified files"""
    import subprocess

    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            check=True
        )

        modified_files = []
        for line in result.stdout.split('\n'):
            if line.strip():
                status = line[:2]
                file_path = line[3:]

                if status[0] in ['M', 'A', 'D']:  # Modified, Added, Deleted
                    modified_files.append((status, file_path))

        return modified_files

    except subprocess.CalledProcessError as e:
        print(f"Error running git status: {e}")
        return []

def main():
    """Main protection check"""
    print("🔒 Checking protected files compliance...")

    protected_patterns = get_protected_files()
    print(f"Protected patterns: {len(protected_patterns)}")

    violations = []

    # Check git status
    modified_files = check_git_status()

    for status, file_path in modified_files:
        if check_file_protection(Path(file_path), protected_patterns):
            if status[0] == 'D':
                violations.append(f"DELETED: {file_path} (protected file)")
            elif status[0] in ['M', 'A']:
                violations.append(f"MODIFIED: {file_path} (protected file)")

    # Check for protected files in working directory
    for pattern in protected_patterns:
        if not pattern.endswith('/') and '*' not in pattern:
            file_path = Path(pattern)
            if file_path.exists():
                violations.append(f"EXISTS: {pattern} (should be in .gitignore)")

    if violations:
        print("\n❌ Protected file violations found:")
        for violation in violations:
            print(f"  - {violation}")
        print("\nProtected files should not be modified, added, or deleted.")
        print("Add them to .gitignore if they should be ignored.")
        sys.exit(1)
    else:
        print("✅ No protected file violations found")
        sys.exit(0)

if __name__ == "__main__":
    main()
