#!/usr/bin/env python3
"""Update README.md with metrics from metrics.json"""

import json
import pathlib
import re
import sys


def main():
    if len(sys.argv) != 3:
        print("Usage: python update_readme_from_metrics.py <metrics.json> <README.md>")
        sys.exit(1)

    METRICS = pathlib.Path(sys.argv[1])
    README = pathlib.Path(sys.argv[2])

    if not METRICS.exists():
        print(f"Error: {METRICS} not found")
        sys.exit(1)

    if not README.exists():
        print(f"Error: {README} not found")
        sys.exit(1)

    with open(METRICS, encoding="utf-8") as f:
        m = json.load(f)

    def pct(cat):
        return f'{m.get(cat, {}).get("pass", 0)}/{m.get(cat, {}).get("total", 0)} ({m.get(cat, {}).get("pass_rate", 0)}%)'

    with open(README, encoding="utf-8") as f:
        content = f.read()

    # Update metrics table
    table = (
        "| Suite | Result |\n"
        "|---|---|\n"
        f"| Ethics | {pct('ethics')} |\n"
        f"| Security | {pct('security')} |\n"
        f"| User Safety | {pct('safety')} |\n"
        f"| Other | {pct('other')} |\n"
    )

    content = re.sub(
        r"(<!-- BEGIN:METRICS_TABLE -->)(.*?)(<!-- END:METRICS_TABLE -->)",
        r"\1\n" + table + r"\3",
        content,
        flags=re.S
    )

    # Update Mermaid diagram
    mermaid_content = f"""```mermaid
flowchart LR
  Core[Core Framework]
  Ethics[EthicsGuard — {m.get('ethics', {}).get('pass_rate', 0)}% pass]
  Security[Security Suite — {m.get('security', {}).get('pass_rate', 0)}% pass]
  Safety[User Safety — {m.get('safety', {}).get('pass_rate', 0)}% pass]
  RouterIface[Router Interface]
  Pro[Pro Plugin (private, optional)]
  Stub[Stub Plugin (public)]

  Core --> Ethics
  Core --> Security
  Core --> Safety
  Core --> RouterIface
  RouterIface -->|auto-detect| Pro
  RouterIface -->|fallback| Stub
```"""

    content = re.sub(
        r"(<!-- BEGIN:MERMAID -->)(.*?)(<!-- END:MERMAID -->)",
        r"\1\n" + mermaid_content + r"\n\3",
        content,
        flags=re.S
    )

    with open(README, "w", encoding="utf-8") as f:
        f.write(content)

    print("README updated with metrics.")

if __name__ == "__main__":
    main()
