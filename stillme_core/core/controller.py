"""
controller.py - AgentDev orchestration controller
"""

import logging
import time
from typing import Any

from .executor import PatchExecutor
from .logging_utils import log_session_end, log_session_start, log_step
from .metrics import record_session
from .planner import Planner
from .verifier import Verifier

logger = logging.getLogger("AgentDev-Controller")


class AgentController:
    """
    Main controller for AgentDev orchestration.
    Orchestrates plan → execute → verify → report workflow.
    """

    def __init__(self, repo_root: str = "."):
        self.planner = Planner()
        self.executor = PatchExecutor(repo_root=repo_root)
        self.verifier = Verifier()
        self.repo_root = repo_root

    def run_agent(self, goal: str, max_steps: int = 5) -> dict[str, Any]:
        """
        Run AgentDev orchestration loop.

        Args:
            goal: Goal description for the agent
            max_steps: Maximum number of steps to execute

        Returns:
            dict: {
                "summary": str,
                "steps": [ { "id": int, "desc": str, "action": str,
                           "exec_ok": bool, "stdout_tail": str, "duration_s": float } ],
                "pass_rate": float
            }
        """
        logger.info(f"Starting AgentDev with goal: '{goal}', max_steps: {max_steps}")

        # Log session start
        log_session_start(goal=goal, max_steps=max_steps)

        start_time = time.time()
        steps = []
        passed_steps = 0

        try:
            # Step 1: Create plan with error handling
            logger.info("Creating plan...")
            try:
                plan_items = self.planner.build_plan(max_items=max_steps)
            except Exception as e:
                logger.error(f"Failed to create plan: {e}")
                return self._create_result(
                    goal=goal,
                    steps=[],
                    passed_steps=0,
                    total_duration=time.time() - start_time,
                    summary=f"Plan creation failed: {e!s}",
                )

            if not plan_items:
                logger.warning("No plan items generated")
                return self._create_result(
                    goal=goal,
                    steps=[],
                    passed_steps=0,
                    total_duration=time.time() - start_time,
                    summary="No plan items generated",
                )

            logger.info(f"Generated {len(plan_items)} plan items")

            # Step 2: Execute each plan item
            for i, plan_item in enumerate(plan_items[:max_steps]):
                step_start_time = time.time()
                step_id = i + 1

                logger.info(f"Executing step {step_id}: {plan_item.title}")

                try:
                    # Execute the plan item with error handling
                    try:
                        exec_result = self.executor.apply_patch_and_test(plan_item)
                        exec_ok = exec_result.get("ok", False)
                    except Exception as e:
                        logger.error(f"Execution failed for step {step_id}: {e}")
                        exec_result = {
                            "ok": False,
                            "error": str(e),
                            "stdout": "",
                            "stderr": str(e),
                        }
                        exec_ok = False

                    # Verify the result with error handling
                    try:
                        verification = self.verifier.verify(
                            step={
                                "action": plan_item.action,
                                "title": plan_item.title,
                                "success_criteria": getattr(
                                    plan_item, "success_criteria", None
                                ),
                            },
                            exec_result=exec_result,
                        )
                    except Exception as e:
                        logger.error(f"Verification failed for step {step_id}: {e}")
                        verification = {"passed": False, "error": str(e)}

                    # Determine if step passed
                    step_passed = exec_ok and (
                        verification is True
                        or (
                            isinstance(verification, dict)
                            and verification.get("passed", False)
                        )
                    )

                    if step_passed:
                        passed_steps += 1
                        logger.info(f"Step {step_id} passed")
                    else:
                        logger.warning(f"Step {step_id} failed")

                    # Extract stdout tail (last 500 chars)
                    stdout = exec_result.get("stdout", "")
                    stderr = exec_result.get("stderr", "")
                    # Include stderr in tail if execution failed
                    if not exec_ok and stderr:
                        stdout_tail = (stdout + "\n" + stderr)[-500:]
                    else:
                        stdout_tail = stdout[-500:] if len(stdout) > 500 else stdout

                    # Create step result
                    step_result = {
                        "id": step_id,
                        "desc": plan_item.title,
                        "action": plan_item.action,
                        "exec_ok": exec_ok,
                        "stdout_tail": stdout_tail,
                        "duration_s": round(time.time() - step_start_time, 2),
                        "verification": verification,
                        "target": getattr(plan_item, "target", ""),
                        "tests_run": exec_result.get("tests_run", []),
                    }

                    steps.append(step_result)

                    # Log step execution
                    log_step(
                        step_id=step_id,
                        action=plan_item.action,
                        ok=step_passed,
                        duration_s=step_result["duration_s"],
                        stdout_tail=step_result["stdout_tail"],
                        description=plan_item.title,
                        target=getattr(plan_item, "target", ""),
                        tests_run=exec_result.get("tests_run", []),
                    )

                    logger.info(
                        f"Step {step_id} {'PASSED' if step_passed else 'FAILED'} "
                        f"({step_result['duration_s']}s)"
                    )

                    # If step failed and it's critical, we might want to stop
                    if not step_passed and getattr(plan_item, "risk", "low") == "high":
                        logger.warning(
                            f"High-risk step {step_id} failed, continuing with remaining steps"
                        )

                except Exception as e:
                    logger.error(f"Error executing step {step_id}: {e}")

                    step_result = {
                        "id": step_id,
                        "desc": plan_item.title,
                        "action": plan_item.action,
                        "exec_ok": False,
                        "stdout_tail": f"Error: {e!s}",
                        "duration_s": round(time.time() - step_start_time, 2),
                        "verification": {
                            "passed": False,
                            "reason": f"Exception: {e!s}",
                        },
                        "target": getattr(plan_item, "target", ""),
                        "tests_run": [],
                    }

                    steps.append(step_result)

                    # Log step execution (for exception case)
                    log_step(
                        step_id=step_id,
                        action=plan_item.action,
                        ok=False,
                        duration_s=step_result["duration_s"],
                        stdout_tail=step_result["stdout_tail"],
                        description=plan_item.title,
                        target=getattr(plan_item, "target", ""),
                        tests_run=[],
                    )

            # Calculate pass rate
            total_steps = len(steps)
            pass_rate = (passed_steps / total_steps) if total_steps > 0 else 0.0

            # Create summary
            summary = self._create_summary(goal, steps, passed_steps, total_steps)

            total_duration = time.time() - start_time

            # Log session end
            log_session_end(
                goal=goal,
                total_steps=total_steps,
                passed_steps=passed_steps,
                pass_rate=pass_rate,
                total_duration_s=total_duration,
            )

            # Record metrics
            record_session(
                goal=goal,
                total_steps=total_steps,
                passed_steps=passed_steps,
                failed_steps=total_steps - passed_steps,
                pass_rate=pass_rate,
                total_duration_s=total_duration,
                steps_details=steps,
            )

            logger.info(
                f"AgentDev completed: {passed_steps}/{total_steps} steps passed "
                f"({pass_rate:.1%}) in {total_duration:.2f}s"
            )

            return self._create_result(
                goal=goal,
                steps=steps,
                passed_steps=passed_steps,
                total_duration=total_duration,
                summary=summary,
            )

        except Exception as e:
            logger.error(f"AgentDev orchestration failed: {e}")
            return self._create_result(
                goal=goal,
                steps=steps,
                passed_steps=passed_steps,
                total_duration=time.time() - start_time,
                summary=f"AgentDev failed: {e!s}",
            )

    def _create_result(
        self,
        goal: str,
        steps: list[dict[str, Any]],
        passed_steps: int,
        total_duration: float,
        summary: str,
    ) -> dict[str, Any]:
        """Create final result dictionary."""
        total_steps = len(steps)
        pass_rate = (passed_steps / total_steps) if total_steps > 0 else 0.0

        return {
            "summary": summary,
            "steps": steps,
            "pass_rate": round(pass_rate, 3),
            "total_steps": total_steps,
            "passed_steps": passed_steps,
            "total_duration_s": round(total_duration, 2),
            "goal": goal,
        }

    def _create_summary(
        self,
        goal: str,
        steps: list[dict[str, Any]],
        passed_steps: int,
        total_steps: int,
    ) -> str:
        """Create human-readable summary."""
        if total_steps == 0:
            return f"AgentDev completed for goal '{goal}': No steps executed"

        pass_rate = (passed_steps / total_steps) * 100

        summary_parts = [
            f"AgentDev completed for goal '{goal}'",
            f"Executed {total_steps} steps: {passed_steps} passed, {total_steps - passed_steps} failed",
            f"Pass rate: {pass_rate:.1f}%",
        ]

        # Add details about failed steps
        failed_steps = [s for s in steps if not s.get("exec_ok", False)]
        if failed_steps:
            failed_actions = [s["action"] for s in failed_steps]
            summary_parts.append(f"Failed actions: {', '.join(set(failed_actions))}")

        return ". ".join(summary_parts) + "."


# Convenience function for direct usage
def run_agent(goal: str, max_steps: int = 5, repo_root: str = ".") -> dict[str, Any]:
    """
    Convenience function to run AgentDev.

    Args:
        goal: Goal description
        max_steps: Maximum steps to execute
        repo_root: Repository root path

    Returns:
        dict: AgentDev result
    """
    controller = AgentController(repo_root=repo_root)
    return controller.run_agent(goal, max_steps)