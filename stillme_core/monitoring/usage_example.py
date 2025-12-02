"""
Usage Example for Time Estimation

Demonstrates how to use the time estimation system.
"""

from stillme_core.monitoring import get_estimation_engine, get_task_tracker

# Example: Estimate time for a task
def example_estimate_task():
    """Example of estimating task time"""
    estimator = get_estimation_engine()
    
    # Estimate a migration task
    estimate = estimator.estimate(
        task_description="Migrate validation system to stillme_core",
        task_type="migration",
        complexity="moderate",
        size=500  # lines of code
    )
    
    # Format for user
    print(estimator.format_estimate(estimate))
    # Output: "Based on my historical performance, I estimate this will take 30-60 minutes (high confidence, 90%). Based on 10 similar tasks."


# Example: Track task execution
def example_track_task():
    """Example of tracking task execution"""
    tracker = get_task_tracker()
    estimator = get_estimation_engine()
    
    # Step 1: Estimate before starting
    estimate = estimator.estimate(
        task_description="Refactor learning system",
        task_type="refactoring",
        complexity="complex",
        size=1000
    )
    
    print(f"Estimate: {estimator.format_estimate(estimate)}")
    
    # Step 2: Start task
    task_id = tracker.start_task(
        task_type="refactoring",
        complexity="complex",
        size=1000,
        estimated_time_minutes=estimate.estimated_minutes,
        metadata={"description": "Refactor learning system"}
    )
    
    # Step 3: Do work...
    # ... actual work happens here ...
    
    # Step 4: End task
    task_record = tracker.end_task(task_id)
    
    if task_record:
        print(f"Task completed:")
        print(f"  Estimated: {task_record.estimated_time_minutes:.2f} minutes")
        print(f"  Actual: {task_record.actual_time_minutes:.2f} minutes")
        print(f"  Accuracy: {task_record.accuracy_ratio:.2f}")
        
        # Accuracy ratio:
        # - 1.0 = perfect estimate
        # - < 1.0 = overestimated (took less time)
        # - > 1.0 = underestimated (took more time)


if __name__ == "__main__":
    example_estimate_task()
    print("\n" + "="*50 + "\n")
    example_track_task()

