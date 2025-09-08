"""
CLI entrypoint for AgentDev
Usage: python -m stillme_core.agent_dev --goal "Run unit tests" --max-steps 3
"""
import argparse
import sys
import time
from typing import Optional
from .controller import run_agent


def main():
    """Main CLI entrypoint for AgentDev"""
    parser = argparse.ArgumentParser(
        description="AgentDev CLI - Automated development agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m stillme_core.agent_dev --goal "Run unit tests"
  python -m stillme_core.agent_dev --goal "Fix failing tests" --max-steps 5
  python -m stillme_core.agent_dev --goal "Add new feature" --max-steps 3 --repo-root /path/to/repo
        """
    )
    
    parser.add_argument(
        "--goal",
        required=True,
        help="Goal description for the agent (e.g., 'Run unit tests', 'Fix failing tests')"
    )
    
    parser.add_argument(
        "--max-steps",
        type=int,
        default=5,
        help="Maximum number of steps to execute (default: 5)"
    )
    
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root path (default: current directory)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Print header
    print("AgentDev CLI")
    print("=" * 50)
    print(f"Goal: {args.goal}")
    print(f"Max steps: {args.max_steps}")
    print(f"Repo root: {args.repo_root}")
    print("=" * 50)
    print()
    
    # Run AgentDev
    start_time = time.time()
    
    try:
        result = run_agent(
            goal=args.goal,
            max_steps=args.max_steps,
            repo_root=args.repo_root
        )
        
        duration = time.time() - start_time
        
        # Print results
        print("RESULTS")
        print("=" * 50)
        print(f"Summary: {result['summary']}")
        print(f"Pass rate: {result['pass_rate']:.1%}")
        print(f"Total steps: {result['total_steps']}")
        print(f"Passed steps: {result['passed_steps']}")
        print(f"Duration: {duration:.2f}s")
        print()
        
        # Print steps table
        if result['steps']:
            print("📋 STEPS")
            print("=" * 50)
            print(f"{'ID':<3} {'Action':<15} {'Status':<8} {'Duration':<10} {'Description'}")
            print("-" * 50)
            
            for step in result['steps']:
                status = "PASS" if step['exec_ok'] else "FAIL"
                duration_str = f"{step['duration_s']:.2f}s"
                description = step['desc'][:30] + "..." if len(step['desc']) > 30 else step['desc']
                
                print(f"{step['id']:<3} {step['action']:<15} {status:<8} {duration_str:<10} {description}")
            
            print()
            
            # Print failed steps details if any
            failed_steps = [s for s in result['steps'] if not s['exec_ok']]
            if failed_steps:
                print("FAILED STEPS DETAILS")
                print("=" * 50)
                for step in failed_steps:
                    print(f"Step {step['id']}: {step['desc']}")
                    print(f"Action: {step['action']}")
                    print(f"Error: {step['stdout_tail'][:200]}...")
                    print()
        
        # Exit with appropriate code
        if result['pass_rate'] == 1.0:
            print("All steps passed!")
            sys.exit(0)
        elif result['pass_rate'] > 0:
            print("Some steps failed, but partial success")
            sys.exit(1)
        else:
            print("All steps failed")
            sys.exit(2)
            
    except Exception as e:
        print(f"AgentDev failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()
