#!/usr/bin/env python3
import json, sys, os, collections, datetime
from pathlib import Path

LEDGER = Path("reports/cost_ledger.jsonl")
OUT = Path("reports/COSTS.md")

def load():
    if not LEDGER.exists():
        return []
    rows=[]
    with LEDGER.open("r", encoding="utf-8") as f:
        for ln in f:
            ln=ln.strip()
            if not ln: continue
            try:
                rows.append(json.loads(ln))
            except Exception:
                pass
    return rows

def month_key(ts):
    try:
        d = datetime.date.fromisoformat(ts)
        return d.strftime("%Y-%m")
    except:
        return "unknown"

def fmt_usd(x):
    return f"${x:,.2f}"

def render(rows):
    total=sum(r.get("amount_usd",0) for r in rows if isinstance(r.get("amount_usd",0),(int,float)))
    by_cat=collections.defaultdict(float)
    by_month=collections.defaultdict(float)
    dons=0.0
    for r in rows:
        amt = r.get("amount_usd",0) or 0.0
        cat = r.get("category","unknown")
        by_cat[cat]+=amt
        by_month[month_key(r.get("ts","unknown"))]+=amt
        if cat.startswith("donation"): dons+=amt

    lines=[]
    lines.append("# StillMe – Monthly Cost Report\n")
    lines.append("> Generated automatically from `reports/cost_ledger.jsonl`.\n")
    lines.append("## Summary\n")
    lines.append(f"- Total (all-time): **{fmt_usd(total)}**")
    if by_month:
        last_month = sorted(k for k in by_month if k!="unknown")[-1] if any(k!="unknown" for k in by_month) else None
        if last_month:
            lines.append(f"- Last month ({last_month}): **{fmt_usd(by_month[last_month])}**")
    lines.append(f"- Donations (all-time): **{fmt_usd(dons)}**\n")

    lines.append("## Breakdown by Category\n")
    for cat, amt in sorted(by_cat.items(), key=lambda x:-x[1]):
        lines.append(f"- {cat}: **{fmt_usd(amt)}**")
    lines.append("")

    lines.append("## Raw Entries (last 20)\n")
    tail = rows[-20:]
    for r in tail:
        ts=r.get("ts","")
        cat=r.get("category","")
        amt=fmt_usd(r.get("amount_usd",0) or 0.0)
        note=r.get("note","")
        lines.append(f"- {ts} · {cat} · {amt} {('· '+note) if note else ''}")

    OUT.write_text("\n".join(lines), encoding="utf-8")

def main():
    rows=load()
    render(rows)

if __name__=="__main__":
    main()
