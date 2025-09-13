# integration_test.py
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from typing import Any, Dict

import httpx


def pretty(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


async def get_health(client: httpx.AsyncClient) -> Dict[str, Any]:
    r = await client.get("/health/ai")
    r.raise_for_status()
    return r.json()


async def post_bridge(
    client: httpx.AsyncClient,
    prompt: str,
    mode: str = "fast",
    **params: Any,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"prompt": prompt, "mode": mode}
    # chỉ thêm các tham số có giá trị khác None
    for k, v in params.items():
        if v is not None:
            payload[k] = v
    r = await client.post("/dev-agent/bridge", json=payload)
    r.raise_for_status()
    return r.json()


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke test Dev Agent API (/health/ai, /dev-agent/bridge)"
    )
    parser.add_argument(
        "--base",
        default=os.getenv("BRIDGE_BASE", "http://127.0.0.1:8000"),
        help="Base URL của API server (mặc định: %(default)s hoặc env BRIDGE_BASE)",
    )
    parser.add_argument(
        "--fast-prompt",
        default="xin chào, hãy trả lời ngắn gọn",
        help="Prompt cho mode fast",
    )
    parser.add_argument(
        "--safe-prompt",
        default="hãy chào bằng tiếng Việt, một câu lịch sự",
        help="Prompt cho mode safe",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=64,
        help="Giới hạn độ dài sinh (map sang num_predict của Ollama)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Nhiệt độ tạo sinh",
    )
    args = parser.parse_args()

    # timeout rộng một chút để model lớn lần đầu load
    timeout = httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=30.0)

    print(f"→ BASE = {args.base}")
    async with httpx.AsyncClient(base_url=args.base, timeout=timeout) as client:
        # 1) /health/ai
        print("\n[1/3] GET /health/ai …")
        t0 = time.perf_counter()
        health = await get_health(client)
        dt = (time.perf_counter() - t0) * 1000
        print(f"  ✓ status: ok ({dt:.0f} ms)")
        print("  body:", pretty(health))

        # sanity checks
        if "ollama" not in health or "ok" not in health["ollama"]:
            print("  ✗ /health/ai thiếu field 'ollama.ok'", file=sys.stderr)
            return 2
        if not bool(health["ollama"]["ok"]):
            print("  ✗ Ollama không sẵn sàng (ollama.ok = false)", file=sys.stderr)
            return 3

        # 2) POST /dev-agent/bridge (fast)
        print("\n[2/3] POST /dev-agent/bridge (mode=fast) …")
        t0 = time.perf_counter()
        fast = await post_bridge(
            client,
            prompt=args.fast_prompt,
            mode="fast",
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        )
        dt = (time.perf_counter() - t0) * 1000
        print(f"  ✓ status: ok ({dt:.0f} ms)")
        print("  body:", pretty(fast))

        # sanity checks fast
        for key in ("provider", "mode", "content"):
            if key not in fast:
                print(f"  ✗ thiếu field '{key}' trong response fast", file=sys.stderr)
                return 4
        if not fast["content"]:
            print("  ✗ fast.content rỗng", file=sys.stderr)
            return 5

        # 3) POST /dev-agent/bridge (safe)
        print("\n[3/3] POST /dev-agent/bridge (mode=safe) …")
        t0 = time.perf_counter()
        safe = await post_bridge(
            client,
            prompt=args.safe_prompt,
            mode="safe",
            max_tokens=args.max_tokens,
            temperature=max(0.0, args.temperature - 0.1),
        )
        dt = (time.perf_counter() - t0) * 1000
        print(f"  ✓ status: ok ({dt:.0f} ms)")
        print("  body:", pretty(safe))

        # sanity checks safe
        for key in ("provider", "mode", "content", "safe_passed"):
            if key not in safe:
                print(f"  ✗ thiếu field '{key}' trong response safe", file=sys.stderr)
                return 6
        if not safe["content"]:
            print("  ✗ safe.content rỗng", file=sys.stderr)
            return 7

    print("\n✅ ALL GOOD — health + fast + safe đều ok.")
    return 0


if __name__ == "__main__":
    try:
        code = asyncio.run(main())
    except httpx.HTTPStatusError as e:
        print(f"\n✗ HTTP {e.response.status_code}:\n{e.response.text}", file=sys.stderr)
        code = 10
    except Exception as e:
        print(f"\n✗ ERROR: {e}", file=sys.stderr)
        code = 11
    sys.exit(code)
