import re
import subprocess
import sys

# Lấy diff trong staged files (đang chuẩn bị commit)
res = subprocess.run(["git", "diff", "--cached", "-U0"], capture_output=True, text=True)
diff = res.stdout

pat = re.compile(r"^\+.*#\s*type:\s*ignore\b", re.IGNORECASE)
bad_lines = [ln for ln in diff.splitlines() if pat.search(ln)]

if bad_lines:
    print("❌ Commit bị chặn: phát hiện '# type: ignore' trong thay đổi staged:\n")
    for ln in bad_lines[:20]:
        print(ln)
    print("\n➡️ Sửa lỗi thực sự thay vì che giấu bằng '# type: ignore'.")
    sys.exit(1)

sys.exit(0)
