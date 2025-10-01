#!/usr/bin/env python3
"""Extract test metrics from JUnit XML and generate metrics.json"""

import json
import os
import xml.etree.ElementTree as ET
from collections import defaultdict

JUNIT = "reports/junit.xml"
OUT = "docs/metrics.json"

def cat_from_name(name: str, classname: str, file: str):
    """Categorize test based on name, classname, and file path."""
    s = (name or "") + " " + (classname or "") + " " + (file or "")
    s = s.lower()
    if "/ethics/" in s or "ethics" in s:
        return "ethics"
    if "/security/" in s or "security" in s:
        return "security"
    if "/safety/" in s or "safety" in s or "user_safety" in s:
        return "safety"
    return "other"

def main():
    """Extract metrics from JUnit XML and save to JSON."""
    if not os.path.exists(JUNIT):
        print(f"Warning: {JUNIT} not found, creating empty metrics")
        stats = {
            "ethics": {"total": 0, "pass": 0, "fail": 0, "error": 0, "skip": 0, "pass_rate": 0.0},
            "security": {"total": 0, "pass": 0, "fail": 0, "error": 0, "skip": 0, "pass_rate": 0.0},
            "safety": {"total": 0, "pass": 0, "fail": 0, "error": 0, "skip": 0, "pass_rate": 0.0},
            "other": {"total": 0, "pass": 0, "fail": 0, "error": 0, "skip": 0, "pass_rate": 0.0}
        }
    else:
        tree = ET.parse(JUNIT)
        root = tree.getroot()
        stats = defaultdict(lambda: {"total": 0, "fail": 0, "error": 0, "skip": 0})

        for tc in root.iter("testcase"):
            name = tc.attrib.get("name", "")
            classname = tc.attrib.get("classname", "")
            file = tc.attrib.get("file", "")
            cat = cat_from_name(name, classname, file)
            stats[cat]["total"] += 1

            if tc.find("failure") is not None:
                stats[cat]["fail"] += 1
            if tc.find("error") is not None:
                stats[cat]["error"] += 1
            if tc.find("skipped") is not None:
                stats[cat]["skip"] += 1

        # Compute pass rate
        for c, v in stats.items():
            passed = v["total"] - v["fail"] - v["error"]
            v["pass"] = passed
            v["pass_rate"] = round(100.0 * passed / v["total"], 1) if v["total"] else 0.0

    # Ensure all categories exist
    for cat in ["ethics", "security", "safety", "other"]:
        if cat not in stats:
            stats[cat] = {"total": 0, "pass": 0, "fail": 0, "error": 0, "skip": 0, "pass_rate": 0.0}

    # Create output directory
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    # Write metrics
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()
