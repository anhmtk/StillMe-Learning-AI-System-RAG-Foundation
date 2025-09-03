import argparse, sys
from stillme_core.config import DEFAULT_MODE, WARMUP_ON_START
from stillme_core.ai_manager import set_mode, warmup, dev_agent, health

def main():
    p = argparse.ArgumentParser(description="StillMe Dev Agent CLI")
    p.add_argument("prompt", help="Your task/prompt", nargs="+")
    p.add_argument("--mode", "-m", default=DEFAULT_MODE,
                   choices=["fast","code","think"], help="Agent mode")
    p.add_argument("--no-warmup", action="store_true", help="Skip warmup on start")
    p.add_argument("--health", action="store_true", help="Only run health check and exit")
    args = p.parse_args()

    if args.health:
        print(health())
        return 0

    prompt = " ".join(args.prompt)
    print(set_mode(args.mode))
    if WARMUP_ON_START and not args.no_warmup:
        print(warmup())

    out = dev_agent(prompt, mode=args.mode)
    print(out)
    return 0

if __name__ == "__main__":
    sys.exit(main())
