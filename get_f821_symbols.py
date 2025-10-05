#!/usr/bin/env python3
import json
from collections import Counter

from agent_dev.core.agentdev import AgentDev

agentdev = AgentDev()
errors = agentdev.scan_errors()
f821_errors = [e for e in errors if e.rule == "F821"]

symbols = []
for e in f821_errors:
    if "`" in e.msg:
        parts = e.msg.split("`")
        if len(parts) >= 2:
            symbols.append(parts[1])

counter = Counter(symbols)
print(json.dumps(dict(counter.most_common(10)), indent=2))
