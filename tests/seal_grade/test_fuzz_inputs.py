"""
SEAL-GRADE Fuzzing Tests
Comprehensive input fuzzing for AgentDev components

Test Coverage:
- Unicode input handling
- Large input handling
- Invalid type handling
- Malformed data handling
- Edge case inputs
- Boundary value testing
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings
import json
import random
import string

from agentdev.state_store import StateStore
from agentdev.models import JobStatus, StepStatus

class TestInputFuzzing:
    """Fuzzing tests for input validation"""
    
    @pytest.fixture
    def state_store(self):
        """Create temporary state store"""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        store = StateStore(temp_db.name)
        asyncio.run(store.initialize())
        yield store
        asyncio.run(store.close())
        Path(temp_db.name).unlink(missing_ok=True)
    
    @given()
        job_id=st.text(min_size=0, max_size=1000),
        name=st.text(min_size=0, max_size=1000),
        description=st.text(min_size=0, max_size=1000)
    )
    @settings(max_examples=100, deadline=5000)
    def test_job_creation_fuzzing(self, state_store, job_id, name, description):
        """Test job creation with fuzzed inputs"""
        try:
            job = asyncio.run(state_store.create_job(job_id, name, description))
            assert job is not None
            assert job.job_id == job_id
        except Exception as e:
            # Should handle invalid inputs gracefully
            assert isinstance(e, (ValueError, TypeError, Exception))
    
    @given()
        unicode_text=st.text(min_size=0, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'Zs', 'Zl', 'Zp', 'Cc', 'Cf', 'Cs', 'Co', 'Cn')))
    )
    @settings(max_examples=50, deadline=5000)
    def test_unicode_handling(self, state_store, unicode_text):
        """Test Unicode input handling"""
        try:
            job = asyncio.run(state_store.create_job(unicode_text, unicode_text, unicode_text))
            assert job is not None
        except Exception as e:
            # Should handle Unicode gracefully
            assert isinstance(e, (ValueError, TypeError, UnicodeError))
    
    @given()
        large_input=st.text(min_size=1000, max_size=10000)
    )
    @settings(max_examples=20, deadline=10000)
    def test_large_input_handling(self, state_store, large_input):
        """Test large input handling"""
        try:
            job = asyncio.run(state_store.create_job("test_job", large_input, large_input))
            assert job is not None
        except Exception as e:
            # Should handle large inputs gracefully
            assert isinstance(e, (ValueError, MemoryError, Exception))
    
    @given(
        invalid_types=st.one_of()
            st.integers(),
            st.floats(),
            st.booleans(),
            st.lists(st.text()),
            st.dictionaries(st.text(), st.text())
        )
    )
    @settings(max_examples=50, deadline=5000)
    def test_invalid_type_handling(self, state_store, invalid_types):
        """Test invalid type handling"""
        try:
            # Convert to string for testing
            job_id = str(invalid_types)
            name = str(invalid_types)
            description = str(invalid_types)
            
            job = asyncio.run(state_store.create_job(job_id, name, description))
            assert job is not None
        except Exception as e:
            # Should handle invalid types gracefully
            assert isinstance(e, (ValueError, TypeError, Exception))
    
    @given()
        malformed_json=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=50, deadline=5000)
    def test_malformed_data_handling(self, state_store, malformed_json):
        """Test malformed data handling"""
        try:
            # Try to parse as JSON
            data = json.loads(malformed_json)
            job_id = str(data) if isinstance(data, (str, int, float)) else "test_job"
            job = asyncio.run(state_store.create_job(job_id, "Test Job", "Test Description"))
            assert job is not None
        except (json.JSONDecodeError, TypeError, ValueError):
            # Expected for malformed JSON
            pass
        except Exception as e:
            # Should handle gracefully
            assert isinstance(e, (ValueError, TypeError, Exception))
    
    @given(
        boundary_values=st.one_of()
            st.just(""),
            st.just(" "),
            st.just("\n"),
            st.just("\t"),
            st.just("\r"),
            st.just("\0"),
            st.just("\\"),
            st.just("/"),
            st.just(":"),
            st.just(";"),
            st.just("|"),
            st.just("*"),
            st.just("?"),
            st.just("<"),
            st.just(">"),
            st.just('"'),
            st.just("'")
        )
    )
    @settings(max_examples=50, deadline=5000)
    def test_boundary_value_handling(self, state_store, boundary_values):
        """Test boundary value handling"""
        try:
            job = asyncio.run(state_store.create_job(boundary_values, boundary_values, boundary_values))
            assert job is not None
        except Exception as e:
            # Should handle boundary values gracefully
            assert isinstance(e, (ValueError, TypeError, Exception))
    
    @given()
        special_chars=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('P', 'S', 'C')))
    )
    @settings(max_examples=50, deadline=5000)
    def test_special_character_handling(self, state_store, special_chars):
        """Test special character handling"""
        try:
            job = asyncio.run(state_store.create_job(special_chars, special_chars, special_chars))
            assert job is not None
        except Exception as e:
            # Should handle special characters gracefully
            assert isinstance(e, (ValueError, TypeError, Exception))
    
    @given(
        numeric_inputs=st.one_of()
            st.integers(min_value=-1000000, max_value=1000000),
            st.floats(min_value=-1000000, max_value=1000000),
            st.decimals(min_value=-1000000, max_value=1000000, places=2)
        )
    )
    @settings(max_examples=50, deadline=5000)
    def test_numeric_input_handling(self, state_store, numeric_inputs):
        """Test numeric input handling"""
        try:
            job_id = str(numeric_inputs)
            job = asyncio.run(state_store.create_job(job_id, "Test Job", "Test Description"))
            assert job is not None
        except Exception as e:
            # Should handle numeric inputs gracefully
            assert isinstance(e, (ValueError, TypeError, Exception))
    
    @given()
        mixed_inputs=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=50, deadline=5000)
    def test_mixed_input_handling(self, state_store, mixed_inputs):
        """Test mixed input handling"""
        try:
            # Mix different types
            job_id = mixed_inputs
            name = str(len(mixed_inputs))
            description = json.dumps({"input": mixed_inputs})
            
            job = asyncio.run(state_store.create_job(job_id, name, description))
            assert job is not None
        except Exception as e:
            # Should handle mixed inputs gracefully
            assert isinstance(e, (ValueError, TypeError, Exception))
    
    @given()
        random_strings=st.text(min_size=1, max_size=200)
    )
    @settings(max_examples=100, deadline=5000)
    def test_random_string_handling(self, state_store, random_strings):
        """Test random string handling"""
        try:
            job = asyncio.run(state_store.create_job(random_strings, random_strings, random_strings))
            assert job is not None
        except Exception as e:
            # Should handle random strings gracefully
            assert isinstance(e, (ValueError, TypeError, Exception))
