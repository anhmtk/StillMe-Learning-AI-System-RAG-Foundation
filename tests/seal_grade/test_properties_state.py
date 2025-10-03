from hypothesis import given, settings

"""
SEAL-GRADE Property-based Tests
Using Hypothesis for comprehensive state management testing

Test Coverage:
- Idempotency properties
- Associativity properties
- Commutativity properties
- State consistency properties
- Error handling properties
- Performance properties
"""

import tempfile
import time
from pathlib import Path

import pytest
from hypothesis import strategies as st
from hypothesis.stateful import Bundle, RuleBasedStateMachine, rule

from stillme_core.compat import JobStatus, StateStore, StepStatus


class StatePropertyTests:
    """Property-based tests for state management"""

    @pytest.fixture
    async def state_store(self):
        """Create a temporary state store for testing"""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db.close()

        store = StateStore(temp_db.name)
        await store.initialize()

        yield store

        # Cleanup
        await store.close()
        Path(temp_db.name).unlink(missing_ok=True)

    @given(
        job_id=st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "_")),
        ),
        name=st.text(min_size=1, max_size=100),
        description=st.text(max_size=500),
    )
    @settings(max_examples=100, deadline=5000)
    async def test_job_creation_idempotency(
        self, state_store, job_id, name, description
    ):
        """Test that creating the same job multiple times is idempotent"""
        # Create job first time
        job1 = await state_store.create_job(job_id, name, description)

        # Create same job again
        job2 = await state_store.create_job(job_id, name, description)

        # Should be identical
        assert job1.job_id == job2.job_id
        assert job1.name == job2.name
        assert job1.description == job2.description
        assert job1.status == job2.status
        assert job1.created_at == job2.created_at

    @given(
        job_id=st.text(min_size=1, max_size=50),
        step_id=st.text(min_size=1, max_size=50),
        step_name=st.text(min_size=1, max_size=100),
        step_type=st.sampled_from(
            ["code_generation", "testing", "review", "deployment"]
        ),
    )
    @settings(max_examples=100, deadline=5000)
    async def test_step_creation_idempotency(
        self, state_store, job_id, step_id, step_name, step_type
    ):
        """Test that creating the same step multiple times is idempotent"""
        # Create job first
        await state_store.create_job(job_id, "Test Job", "Test Description")

        # Create step first time
        step1 = await state_store.create_job_step(job_id, step_id, step_name, step_type)

        # Create same step again
        step2 = await state_store.create_job_step(job_id, step_id, step_name, step_type)

        # Should be identical
        assert step1.step_id == step2.step_id
        assert step1.job_id == step2.job_id
        assert step1.name == step2.name
        assert step1.step_type == step2.step_type
        assert step1.status == step2.status

    @given(
        job_id=st.text(min_size=1, max_size=50),
        checkpoint_id=st.text(min_size=1, max_size=50),
        checkpoint_name=st.text(min_size=1, max_size=100),
    )
    @settings(max_examples=100, deadline=5000)
    async def test_checkpoint_creation_idempotency(
        self, state_store, job_id, checkpoint_id, checkpoint_name
    ):
        """Test that creating the same checkpoint multiple times is idempotent"""
        # Create job first
        await state_store.create_job(job_id, "Test Job", "Test Description")

        # Create checkpoint first time
        checkpoint1 = await state_store.create_checkpoint(
            job_id, checkpoint_id, checkpoint_name
        )

        # Create same checkpoint again
        checkpoint2 = await state_store.create_checkpoint(
            job_id, checkpoint_id, checkpoint_name
        )

        # Should be identical
        assert checkpoint1.checkpoint_id == checkpoint2.checkpoint_id
        assert checkpoint1.job_id == checkpoint2.job_id
        assert checkpoint1.name == checkpoint2.name
        assert checkpoint1.status == checkpoint2.status

    @given(
        job_id=st.text(min_size=1, max_size=50),
        artifact_id=st.text(min_size=1, max_size=50),
        artifact_name=st.text(min_size=1, max_size=100),
        artifact_type=st.sampled_from(["file", "directory", "url", "data"]),
    )
    @settings(max_examples=100, deadline=5000)
    async def test_artifact_creation_idempotency(
        self, state_store, job_id, artifact_id, artifact_name, artifact_type
    ):
        """Test that creating the same artifact multiple times is idempotent"""
        # Create job first
        await state_store.create_job(job_id, "Test Job", "Test Description")

        # Create artifact first time
        artifact1 = await state_store.store_artifact(
            job_id, artifact_id, artifact_name, artifact_type, "test_path"
        )

        # Create same artifact again
        artifact2 = await state_store.store_artifact(
            job_id, artifact_id, artifact_name, artifact_type, "test_path"
        )

        # Should be identical
        assert artifact1.artifact_id == artifact2.artifact_id
        assert artifact1.job_id == artifact2.job_id
        assert artifact1.name == artifact2.name
        assert artifact1.artifact_type == artifact2.artifact_type
        assert artifact1.path == artifact2.path

    @given(
        job_ids=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10),
        names=st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=10),
    )
    @settings(max_examples=50, deadline=10000)
    async def test_bulk_job_creation_commutativity(self, state_store, job_ids, names):
        """Test that bulk job creation is commutative"""
        # Create jobs in order A
        jobs_a = []
        for i, (job_id, name) in enumerate(zip(job_ids, names, strict=False)):
            job = await state_store.create_job(job_id, name, f"Description {i}")
            jobs_a.append(job)

        # Create jobs in reverse order B
        jobs_b = []
        for i, (job_id, name) in enumerate(reversed(list(zip(job_ids, names, strict=False)))):
            job = await state_store.create_job(job_id, name, f"Description {i}")
            jobs_b.append(job)

        # Results should be identical (commutative)
        assert len(jobs_a) == len(jobs_b)
        for job_a, job_b in zip(jobs_a, jobs_b, strict=False):
            assert job_a.job_id == job_b.job_id
            assert job_a.name == job_b.name
            assert job_a.status == job_b.status

    @given(
        job_id=st.text(min_size=1, max_size=50),
        step_count=st.integers(min_value=1, max_value=20),
        step_types=st.lists(
            st.sampled_from(["code_generation", "testing", "review", "deployment"]),
            min_size=1,
            max_size=20,
        ),
    )
    @settings(max_examples=50, deadline=10000)
    async def test_step_ordering_consistency(
        self, state_store, job_id, step_count, step_types
    ):
        """Test that step ordering is consistent regardless of creation order"""
        # Create job
        await state_store.create_job(job_id, "Test Job", "Test Description")

        # Create steps in forward order
        steps_forward = []
        for i in range(step_count):
            step_type = step_types[i % len(step_types)]
            step = await state_store.create_job_step(
                job_id, f"step_{i}", f"Step {i}", step_type
            )
            steps_forward.append(step)

        # Create steps in reverse order
        steps_reverse = []
        for i in reversed(range(step_count)):
            step_type = step_types[i % len(step_types)]
            step = await state_store.create_job_step(
                job_id, f"step_{i}", f"Step {i}", step_type
            )
            steps_reverse.append(step)

        # Results should be identical
        assert len(steps_forward) == len(steps_reverse)
        for step_f, step_r in zip(steps_forward, steps_reverse, strict=False):
            assert step_f.step_id == step_r.step_id
            assert step_f.name == step_r.name
            assert step_f.step_type == step_r.step_type

    @given(
        job_id=st.text(min_size=1, max_size=50),
        status_transitions=st.lists(
            st.sampled_from(
                [
                    JobStatus.PENDING,
                    JobStatus.RUNNING,
                    JobStatus.COMPLETED,
                    JobStatus.FAILED,
                ]
            ),
            min_size=1,
            max_size=10,
        ),
    )
    @settings(max_examples=50, deadline=5000)
    async def test_status_transition_consistency(
        self, state_store, job_id, status_transitions
    ):
        """Test that status transitions are consistent and valid"""
        # Create job
        await state_store.create_job(job_id, "Test Job", "Test Description")

        # Apply status transitions
        for status in status_transitions:
            await state_store.update_job_status(job_id, status)
            updated_job = await state_store.get_job(job_id)
            assert updated_job.status == status

        # Final status should be the last transition
        final_job = await state_store.get_job(job_id)
        assert final_job.status == status_transitions[-1]

    @given(
        job_id=st.text(min_size=1, max_size=50),
        step_id=st.text(min_size=1, max_size=50),
        error_messages=st.lists(st.text(max_size=200), min_size=1, max_size=5),
    )
    @settings(max_examples=50, deadline=5000)
    async def test_error_handling_consistency(
        self, state_store, job_id, step_id, error_messages
    ):
        """Test that error handling is consistent"""
        # Create job and step
        await state_store.create_job(job_id, "Test Job", "Test Description")
        await state_store.create_job_step(job_id, step_id, "Test Step", "testing")

        # Apply multiple error messages
        for error_msg in error_messages:
            await state_store.complete_job_step(
                job_id, step_id, success=False, error_message=error_msg
            )
            step = await state_store.get_job_step(job_id, step_id)
            assert step.status == StepStatus.FAILED
            assert step.error_message == error_msg

        # Final error should be the last one
        final_step = await state_store.get_job_step(job_id, step_id)
        assert final_step.error_message == error_messages[-1]

    @given(
        job_id=st.text(min_size=1, max_size=50),
        checkpoint_count=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=50, deadline=5000)
    async def test_checkpoint_ordering_consistency(
        self, state_store, job_id, checkpoint_count
    ):
        """Test that checkpoint ordering is consistent"""
        # Create job
        await state_store.create_job(job_id, "Test Job", "Test Description")

        # Create checkpoints
        checkpoints = []
        for i in range(checkpoint_count):
            checkpoint = await state_store.create_checkpoint(
                job_id, f"checkpoint_{i}", f"Checkpoint {i}"
            )
            checkpoints.append(checkpoint)

        # Get all checkpoints for job
        all_checkpoints = await state_store.get_job_checkpoints(job_id)

        # Should be in creation order
        assert len(all_checkpoints) == checkpoint_count
        for i, checkpoint in enumerate(all_checkpoints):
            assert checkpoint.checkpoint_id == f"checkpoint_{i}"
            assert checkpoint.name == f"Checkpoint {i}"

    @given(
        job_id=st.text(min_size=1, max_size=50),
        artifact_count=st.integers(min_value=1, max_value=10),
        artifact_types=st.lists(
            st.sampled_from(["file", "directory", "url", "data"]),
            min_size=1,
            max_size=10,
        ),
    )
    @settings(max_examples=50, deadline=5000)
    async def test_artifact_ordering_consistency(
        self, state_store, job_id, artifact_count, artifact_types
    ):
        """Test that artifact ordering is consistent"""
        # Create job
        await state_store.create_job(job_id, "Test Job", "Test Description")

        # Create artifacts
        artifacts = []
        for i in range(artifact_count):
            artifact_type = artifact_types[i % len(artifact_types)]
            artifact = await state_store.store_artifact(
                job_id, f"artifact_{i}", f"Artifact {i}", artifact_type, f"path_{i}"
            )
            artifacts.append(artifact)

        # Get all artifacts for job
        all_artifacts = await state_store.get_job_artifacts(job_id)

        # Should be in creation order
        assert len(all_artifacts) == artifact_count
        for i, artifact in enumerate(all_artifacts):
            assert artifact.artifact_id == f"artifact_{i}"
            assert artifact.name == f"Artifact {i}"
            assert artifact.artifact_type == artifact_types[i % len(artifact_types)]

    @given(
        job_id=st.text(min_size=1, max_size=50),
        step_id=st.text(min_size=1, max_size=50),
        execution_time=st.floats(min_value=0.001, max_value=10.0),
    )
    @settings(max_examples=50, deadline=5000)
    async def test_performance_consistency(
        self, state_store, job_id, step_id, execution_time
    ):
        """Test that performance metrics are consistent"""
        # Create job and step
        await state_store.create_job(job_id, "Test Job", "Test Description")
        await state_store.create_job_step(job_id, step_id, "Test Step", "testing")

        # Complete step with execution time
        start_time = time.time()
        await state_store.complete_job_step(
            job_id, step_id, success=True, execution_time=execution_time
        )
        end_time = time.time()

        # Get step and verify metrics
        step = await state_store.get_job_step(job_id, step_id)
        assert step.status == StepStatus.COMPLETED
        assert step.execution_time == execution_time
        assert step.completed_at is not None

        # Verify timing is reasonable
        actual_duration = end_time - start_time
        assert actual_duration < 1.0  # Should complete quickly

    @given(
        job_id=st.text(min_size=1, max_size=50),
        step_id=st.text(min_size=1, max_size=50),
        retry_count=st.integers(min_value=0, max_value=5),
    )
    @settings(max_examples=50, deadline=5000)
    async def test_retry_consistency(self, state_store, job_id, step_id, retry_count):
        """Test that retry logic is consistent"""
        # Create job and step
        await state_store.create_job(job_id, "Test Job", "Test Description")
        await state_store.create_job_step(job_id, step_id, "Test Step", "testing")

        # Simulate retries
        for i in range(retry_count):
            await state_store.complete_job_step(
                job_id, step_id, success=False, error_message=f"Retry {i}"
            )
            await state_store.update_job_step_status(
                job_id, step_id, StepStatus.PENDING
            )

        # Final completion
        await state_store.complete_job_step(job_id, step_id, success=True)

        # Verify final state
        step = await state_store.get_job_step(job_id, step_id)
        assert step.status == StepStatus.COMPLETED
        assert step.retry_count == retry_count

    @given(
        job_id=st.text(min_size=1, max_size=50),
        metadata=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(
                st.text(max_size=100), st.integers(), st.floats(), st.booleans()
            ),
        ),
    )
    @settings(max_examples=50, deadline=5000)
    async def test_metadata_consistency(self, state_store, job_id, metadata):
        """Test that metadata handling is consistent"""
        # Create job with metadata
        await state_store.create_job(job_id, "Test Job", "Test Description")

        # Update metadata
        await state_store.update_job_metadata(job_id, metadata)

        # Verify metadata
        updated_job = await state_store.get_job(job_id)
        assert updated_job.metadata == metadata

        # Update metadata again
        new_metadata = {**metadata, "updated": True}
        await state_store.update_job_metadata(job_id, new_metadata)

        # Verify updated metadata
        final_job = await state_store.get_job(job_id)
        assert final_job.metadata == new_metadata


class StateMachineTests(RuleBasedStateMachine):
    """State machine tests for complex state transitions"""

    jobs = Bundle("jobs")
    steps = Bundle("steps")
    checkpoints = Bundle("checkpoints")
    artifacts = Bundle("artifacts")

    def __init__(self):
        super().__init__()
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.state_store = None

    async def setup(self):
        """Setup state machine"""
        self.state_store = StateStore(self.temp_db.name)
        await self.state_store.initialize()

    async def teardown(self):
        """Teardown state machine"""
        if self.state_store:
            await self.state_store.close()
        Path(self.temp_db.name).unlink(missing_ok=True)

    @rule(target=jobs, job_id=st.text(min_size=1, max_size=50))
    async def create_job(self, job_id):
        """Create a job"""
        job = await self.state_store.create_job(
            job_id, f"Job {job_id}", f"Description {job_id}"
        )
        return job

    @rule(job=jobs, step_id=st.text(min_size=1, max_size=50))
    async def create_step(self, job, step_id):
        """Create a step for a job"""
        step = await self.state_store.create_job_step(
            job.job_id, step_id, f"Step {step_id}", "testing"
        )
        return step

    @rule(job=jobs, checkpoint_id=st.text(min_size=1, max_size=50))
    async def create_checkpoint(self, job, checkpoint_id):
        """Create a checkpoint for a job"""
        checkpoint = await self.state_store.create_checkpoint(
            job.job_id, checkpoint_id, f"Checkpoint {checkpoint_id}"
        )
        return checkpoint

    @rule(job=jobs, artifact_id=st.text(min_size=1, max_size=50))
    async def create_artifact(self, job, artifact_id):
        """Create an artifact for a job"""
        artifact = await self.state_store.store_artifact(
            job.job_id,
            artifact_id,
            f"Artifact {artifact_id}",
            "file",
            f"path_{artifact_id}",
        )
        return artifact

    @rule(
        job=jobs,
        status=st.sampled_from(
            [
                JobStatus.PENDING,
                JobStatus.RUNNING,
                JobStatus.COMPLETED,
                JobStatus.FAILED,
            ]
        ),
    )
    async def update_job_status(self, job, status):
        """Update job status"""
        await self.state_store.update_job_status(job.job_id, status)
        updated_job = await self.state_store.get_job(job.job_id)
        assert updated_job.status == status

    @rule(job=jobs, step_id=st.text(min_size=1, max_size=50), success=st.booleans())
    async def complete_step(self, job, step_id, success):
        """Complete a step"""
        # Create step if it doesn't exist
        try:
            await self.state_store.get_job_step(job.job_id, step_id)
        except Exception:
            await self.state_store.create_job_step(
                job.job_id, step_id, f"Step {step_id}", "testing"
            )

        # Complete step
        await self.state_store.complete_job_step(job.job_id, step_id, success=success)
        updated_step = await self.state_store.get_job_step(job.job_id, step_id)

        if success:
            assert updated_step.status == StepStatus.COMPLETED
        else:
            assert updated_step.status == StepStatus.FAILED

    @rule(
        job=jobs,
        metadata=st.dictionaries(
            keys=st.text(max_size=10), values=st.text(max_size=50)
        ),
    )
    async def update_metadata(self, job, metadata):
        """Update job metadata"""
        await self.state_store.update_job_metadata(job.job_id, metadata)
        updated_job = await self.state_store.get_job(job.job_id)
        assert updated_job.metadata == metadata


# Test runner for state machine
@given(st.data())
def test_state_machine(data):
    """Test the state machine"""
    # Use hypothesis state machine testing
    StateMachineTests.TestCase.settings = settings(max_examples=10)
    StateMachineTests.TestCase().run()
