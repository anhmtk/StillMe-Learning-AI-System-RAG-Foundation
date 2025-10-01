#!/usr/bin/env python3
"""
API Management System - API Design, Testing & Documentation
Hệ thống quản lý API cho AgentDev Unified

Tính năng:
1. API Design - Thiết kế API (REST/gRPC minimal)
2. API Testing - Test API endpoints (contract tests, fuzz tests)
3. Integration Testing - Test integrations cross-module
4. API Documentation - Tài liệu API (OpenAPI spec auto-gen)
5. Version Management - Quản lý phiên bản API (v1, v2 baseline)
"""

import os
import json
import time
import asyncio
import aiohttp
import yaml
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import re
import random
import string

class APIMethod(Enum):
    """HTTP Methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

class APIVersion(Enum):
    """API Versions"""
    V1 = "v1"
    V2 = "v2"
    LATEST = "latest"

class TestType(Enum):
    """Test Types"""
    CONTRACT = "contract"
    FUZZ = "fuzz"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    SECURITY = "security"

@dataclass
class APIEndpoint:
    """API Endpoint definition"""
    path: str
    method: APIMethod
    version: APIVersion
    description: str
    parameters: List[Dict[str, Any]]
    request_schema: Dict[str, Any]
    response_schema: Dict[str, Any]
    status_codes: Dict[int, str]
    examples: List[Dict[str, Any]]
    tags: List[str]
    deprecated: bool = False

@dataclass
class APITestResult:
    """API Test Result"""
    test_id: str
    endpoint: str
    method: str
    test_type: TestType
    status: str  # "passed", "failed", "error"
    response_time: float
    status_code: int
    response_size: int
    error_message: Optional[str]
    test_data: Dict[str, Any]
    timestamp: datetime

@dataclass
class APIContract:
    """API Contract definition"""
    contract_id: str
    endpoint: APIEndpoint
    expected_schema: Dict[str, Any]
    validation_rules: List[Dict[str, Any]]
    test_cases: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

@dataclass
class APIManagementReport:
    """API Management Report"""
    total_endpoints: int
    tested_endpoints: int
    test_coverage: float
    performance_metrics: Dict[str, float]
    security_issues: List[str]
    contract_violations: List[str]
    recommendations: List[str]
    analysis_time: float

class APIManagementSystem:
    """API Management System - Quản lý API toàn diện"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.api_dir = self.project_root / "api"
        self.contracts_dir = self.api_dir / "contracts"
        self.tests_dir = self.api_dir / "tests"
        self.docs_dir = self.api_dir / "docs"

        # Tạo thư mục cần thiết
        self._ensure_directories()

        # API endpoints registry
        self.endpoints: Dict[str, APIEndpoint] = {}
        self.contracts: Dict[str, APIContract] = {}
        self.test_results: List[APITestResult] = []

        # Load existing APIs
        self._load_existing_apis()

    def _ensure_directories(self):
        """Đảm bảo thư mục cần thiết tồn tại"""
        for dir_path in [self.api_dir, self.contracts_dir, self.tests_dir, self.docs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def _load_existing_apis(self):
        """Load existing API definitions"""
        # Load from OpenAPI specs
        openapi_files = list(self.api_dir.glob("*.yaml")) + list(self.api_dir.glob("*.json"))
        for file_path in openapi_files:
            try:
                self._load_openapi_spec(file_path)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

    def _load_openapi_spec(self, file_path: Path):
        """Load OpenAPI specification"""
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.suffix == '.yaml':
                spec = yaml.safe_load(f)
            else:
                spec = json.load(f)

        # Parse endpoints from OpenAPI spec
        for path, methods in spec.get('paths', {}).items():
            for method, details in methods.items():
                if method.upper() in [m.value for m in APIMethod]:
                    endpoint = self._parse_openapi_endpoint(path, method, details, spec)
                    self.endpoints[f"{method.upper()}:{path}"] = endpoint

    def _parse_openapi_endpoint(self, path: str, method: str, details: Dict, spec: Dict) -> APIEndpoint:
        """Parse OpenAPI endpoint to APIEndpoint"""
        # Extract parameters
        parameters = []
        for param in details.get('parameters', []):
            parameters.append({
                'name': param.get('name'),
                'in': param.get('in'),
                'required': param.get('required', False),
                'schema': param.get('schema', {})
            })

        # Extract request/response schemas
        request_schema = {}
        response_schema = {}

        if 'requestBody' in details:
            request_schema = details['requestBody'].get('content', {})

        if 'responses' in details:
            response_schema = details['responses']

        # Extract examples
        examples = []
        if 'examples' in details:
            examples = details['examples']

        return APIEndpoint(
            path=path,
            method=APIMethod(method.upper()),
            version=APIVersion.V1,  # Default version
            description=details.get('description', ''),
            parameters=parameters,
            request_schema=request_schema,
            response_schema=response_schema,
            status_codes={int(k): v.get('description', '') for k, v in details.get('responses', {}).items() if k.isdigit()},
            examples=examples,
            tags=details.get('tags', [])
        )

    def register_endpoint(self, endpoint: APIEndpoint) -> str:
        """Register new API endpoint"""
        endpoint_id = f"{endpoint.method.value}:{endpoint.path}"
        self.endpoints[endpoint_id] = endpoint

        # Save to file
        self._save_endpoint(endpoint)

        return endpoint_id

    def _save_endpoint(self, endpoint: APIEndpoint):
        """Save endpoint to file"""
        # Sanitize path for filename
        safe_path = endpoint.path.replace('/', '_').replace(':', '_').replace('\\', '_')
        endpoint_file = self.api_dir / f"endpoint_{endpoint.method.value}_{safe_path}.json"

        with open(endpoint_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(endpoint), f, indent=2, default=str)

    def create_contract(self, endpoint_id: str, expected_schema: Dict[str, Any]) -> APIContract:
        """Create API contract"""
        if endpoint_id not in self.endpoints:
            raise ValueError(f"Endpoint {endpoint_id} not found")

        endpoint = self.endpoints[endpoint_id]

        contract = APIContract(
            contract_id=f"contract_{endpoint_id}_{int(time.time())}",
            endpoint=endpoint,
            expected_schema=expected_schema,
            validation_rules=self._generate_validation_rules(expected_schema),
            test_cases=self._generate_test_cases(endpoint, expected_schema),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self.contracts[contract.contract_id] = contract

        # Save contract
        self._save_contract(contract)

        return contract

    def _generate_validation_rules(self, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate validation rules from schema"""
        rules = []

        if 'properties' in schema:
            for prop, prop_schema in schema['properties'].items():
                rule = {
                    'field': prop,
                    'type': prop_schema.get('type', 'string'),
                    'required': prop in schema.get('required', []),
                    'validation': {}
                }

                if 'minLength' in prop_schema:
                    rule['validation']['min_length'] = prop_schema['minLength']
                if 'maxLength' in prop_schema:
                    rule['validation']['max_length'] = prop_schema['maxLength']
                if 'minimum' in prop_schema:
                    rule['validation']['minimum'] = prop_schema['minimum']
                if 'maximum' in prop_schema:
                    rule['validation']['maximum'] = prop_schema['maximum']
                if 'pattern' in prop_schema:
                    rule['validation']['pattern'] = prop_schema['pattern']

                rules.append(rule)

        return rules

    def _generate_test_cases(self, endpoint: APIEndpoint, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate test cases for endpoint"""
        test_cases = []

        # Valid test case
        valid_data = self._generate_valid_data(schema)
        test_cases.append({
            'name': 'valid_request',
            'data': valid_data,
            'expected_status': 200,
            'description': 'Valid request test case'
        })

        # Invalid test cases
        if 'properties' in schema:
            for prop in schema['properties']:
                # Missing required field
                if prop in schema.get('required', []):
                    invalid_data = valid_data.copy()
                    del invalid_data[prop]
                    test_cases.append({
                        'name': f'missing_required_{prop}',
                        'data': invalid_data,
                        'expected_status': 400,
                        'description': f'Missing required field: {prop}'
                    })

                # Invalid type
                invalid_data = valid_data.copy()
                invalid_data[prop] = "invalid_type"
                test_cases.append({
                    'name': f'invalid_type_{prop}',
                    'data': invalid_data,
                    'expected_status': 400,
                    'description': f'Invalid type for field: {prop}'
                })

        return test_cases

    def _generate_valid_data(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate valid test data from schema"""
        data = {}

        if 'properties' in schema:
            for prop, prop_schema in schema['properties'].items():
                prop_type = prop_schema.get('type', 'string')

                if prop_type == 'string':
                    data[prop] = f"test_{prop}"
                elif prop_type == 'integer':
                    data[prop] = 123
                elif prop_type == 'number':
                    data[prop] = 123.45
                elif prop_type == 'boolean':
                    data[prop] = True
                elif prop_type == 'array':
                    data[prop] = ["item1", "item2"]
                elif prop_type == 'object':
                    data[prop] = {"key": "value"}
                else:
                    data[prop] = f"test_{prop}"

        return data

    def _save_contract(self, contract: APIContract):
        """Save contract to file"""
        # Sanitize contract_id for filename
        safe_id = contract.contract_id.replace(":", "_").replace("/", "_").replace("\\", "_")
        contract_file = self.contracts_dir / f"{safe_id}.json"

        with open(contract_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(contract), f, indent=2, default=str)

    async def test_endpoint(self, endpoint_id: str, test_type: TestType,
                          base_url: str = "http://localhost:8000") -> APITestResult:
        """Test API endpoint"""
        if endpoint_id not in self.endpoints:
            raise ValueError(f"Endpoint {endpoint_id} not found")

        endpoint = self.endpoints[endpoint_id]
        test_id = f"test_{endpoint_id}_{test_type.value}_{int(time.time())}"

        start_time = time.time()

        try:
            if test_type == TestType.CONTRACT:
                result = await self._test_contract(endpoint, base_url)
            elif test_type == TestType.FUZZ:
                result = await self._test_fuzz(endpoint, base_url)
            elif test_type == TestType.INTEGRATION:
                result = await self._test_integration(endpoint, base_url)
            else:
                result = await self._test_basic(endpoint, base_url)

            response_time = time.time() - start_time

            test_result = APITestResult(
                test_id=test_id,
                endpoint=endpoint.path,
                method=endpoint.method.value,
                test_type=test_type,
                status="passed" if result['status_code'] < 400 else "failed",
                response_time=response_time,
                status_code=result['status_code'],
                response_size=result['response_size'],
                error_message=result.get('error'),
                test_data=result.get('data', {}),
                timestamp=datetime.now()
            )

        except Exception as e:
            response_time = time.time() - start_time

            test_result = APITestResult(
                test_id=test_id,
                endpoint=endpoint.path,
                method=endpoint.method.value,
                test_type=test_type,
                status="error",
                response_time=response_time,
                status_code=0,
                response_size=0,
                error_message=str(e),
                test_data={},
                timestamp=datetime.now()
            )

        self.test_results.append(test_result)
        return test_result

    async def _test_basic(self, endpoint: APIEndpoint, base_url: str) -> Dict[str, Any]:
        """Basic endpoint test"""
        url = f"{base_url}{endpoint.path}"

        async with aiohttp.ClientSession() as session:
            if endpoint.method == APIMethod.GET:
                async with session.get(url) as response:
                    return {
                        'status_code': response.status,
                        'response_size': len(await response.text()),
                        'data': await response.json() if response.content_type == 'application/json' else {}
                    }
            elif endpoint.method == APIMethod.POST:
                data = self._generate_valid_data(endpoint.request_schema)
                async with session.post(url, json=data) as response:
                    return {
                        'status_code': response.status,
                        'response_size': len(await response.text()),
                        'data': data
                    }
            else:
                # Default to GET for other methods
                async with session.get(url) as response:
                    return {
                        'status_code': response.status,
                        'response_size': len(await response.text()),
                        'data': {}
                    }

    async def _test_contract(self, endpoint: APIEndpoint, base_url: str) -> Dict[str, Any]:
        """Contract test"""
        # Find contract for this endpoint
        contract = None
        for c in self.contracts.values():
            if c.endpoint.path == endpoint.path and c.endpoint.method == endpoint.method:
                contract = c
                break

        if not contract:
            return await self._test_basic(endpoint, base_url)

        # Test with contract validation
        url = f"{base_url}{endpoint.path}"

        async with aiohttp.ClientSession() as session:
            # Test valid case
            valid_data = self._generate_valid_data(contract.expected_schema)

            if endpoint.method == APIMethod.POST:
                async with session.post(url, json=valid_data) as response:
                    return {
                        'status_code': response.status,
                        'response_size': len(await response.text()),
                        'data': valid_data
                    }
            else:
                async with session.get(url) as response:
                    return {
                        'status_code': response.status,
                        'response_size': len(await response.text()),
                        'data': {}
                    }

    async def _test_fuzz(self, endpoint: APIEndpoint, base_url: str) -> Dict[str, Any]:
        """Fuzz test"""
        url = f"{base_url}{endpoint.path}"

        # Generate fuzz data
        fuzz_data = self._generate_fuzz_data(endpoint.request_schema)

        async with aiohttp.ClientSession() as session:
            try:
                if endpoint.method == APIMethod.POST:
                    async with session.post(url, json=fuzz_data) as response:
                        return {
                            'status_code': response.status,
                            'response_size': len(await response.text()),
                            'data': fuzz_data
                        }
                else:
                    async with session.get(url) as response:
                        return {
                            'status_code': response.status,
                            'response_size': len(await response.text()),
                            'data': {}
                        }
            except Exception as e:
                return {
                    'status_code': 0,
                    'response_size': 0,
                    'error': str(e),
                    'data': fuzz_data
                }

    def _generate_fuzz_data(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fuzz test data"""
        fuzz_data = {}

        if 'properties' in schema:
            for prop, prop_schema in schema['properties'].items():
                prop_type = prop_schema.get('type', 'string')

                if prop_type == 'string':
                    # Generate random string
                    fuzz_data[prop] = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(1, 100)))
                elif prop_type == 'integer':
                    # Generate random integer
                    fuzz_data[prop] = random.randint(-1000, 1000)
                elif prop_type == 'number':
                    # Generate random number
                    fuzz_data[prop] = random.uniform(-1000, 1000)
                elif prop_type == 'boolean':
                    # Generate random boolean
                    fuzz_data[prop] = random.choice([True, False])
                elif prop_type == 'array':
                    # Generate random array
                    fuzz_data[prop] = [random.randint(1, 100) for _ in range(random.randint(1, 10))]
                else:
                    # Default to random string
                    fuzz_data[prop] = ''.join(random.choices(string.ascii_letters, k=10))

        return fuzz_data

    async def _test_integration(self, endpoint: APIEndpoint, base_url: str) -> Dict[str, Any]:
        """Integration test"""
        # Test endpoint with other related endpoints
        url = f"{base_url}{endpoint.path}"

        async with aiohttp.ClientSession() as session:
            # Test basic functionality
            if endpoint.method == APIMethod.GET:
                async with session.get(url) as response:
                    return {
                        'status_code': response.status,
                        'response_size': len(await response.text()),
                        'data': await response.json() if response.content_type == 'application/json' else {}
                    }
            else:
                # For non-GET methods, test with valid data
                data = self._generate_valid_data(endpoint.request_schema)
                async with session.post(url, json=data) as response:
                    return {
                        'status_code': response.status,
                        'response_size': len(await response.text()),
                        'data': data
                    }

    async def run_scalability_test(self, endpoint_id: str, num_requests: int = 1000,
                                 base_url: str = "http://localhost:8000") -> List[APITestResult]:
        """Run scalability test with multiple requests"""
        if endpoint_id not in self.endpoints:
            raise ValueError(f"Endpoint {endpoint_id} not found")

        endpoint = self.endpoints[endpoint_id]
        results = []

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(100)  # Max 100 concurrent requests

        async def make_request():
            async with semaphore:
                return await self.test_endpoint(endpoint_id, TestType.PERFORMANCE, base_url)

        # Run concurrent requests
        tasks = [make_request() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = [r for r in results if isinstance(r, APITestResult)]

        return valid_results

    def generate_openapi_spec(self) -> Dict[str, Any]:
        """Generate OpenAPI specification"""
        spec = {
            'openapi': '3.0.0',
            'info': {
                'title': 'AgentDev Unified API',
                'version': '1.0.0',
                'description': 'API for AgentDev Unified system'
            },
            'servers': [
                {'url': 'http://localhost:8000', 'description': 'Development server'}
            ],
            'paths': {},
            'components': {
                'schemas': {}
            }
        }

        # Add endpoints to spec
        for endpoint in self.endpoints.values():
            path_spec = {
                endpoint.method.value.lower(): {
                    'summary': endpoint.description,
                    'tags': endpoint.tags,
                    'parameters': endpoint.parameters,
                    'responses': {
                        str(code): {'description': desc}
                        for code, desc in endpoint.status_codes.items()
                    }
                }
            }

            if endpoint.request_schema:
                path_spec[endpoint.method.value.lower()]['requestBody'] = {
                    'content': endpoint.request_schema
                }

            spec['paths'][endpoint.path] = path_spec

        return spec

    def save_openapi_spec(self, filename: str = "openapi.yaml"):
        """Save OpenAPI specification to file"""
        spec = self.generate_openapi_spec()

        spec_file = self.docs_dir / filename

        with open(spec_file, 'w', encoding='utf-8') as f:
            yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

        return str(spec_file)

    def generate_api_report(self) -> APIManagementReport:
        """Generate API management report"""
        start_time = time.time()

        total_endpoints = len(self.endpoints)
        tested_endpoints = len(set(r.endpoint for r in self.test_results))
        test_coverage = (tested_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0

        # Calculate performance metrics
        performance_metrics = {}
        if self.test_results:
            response_times = [r.response_time for r in self.test_results if r.response_time > 0]
            if response_times:
                performance_metrics = {
                    'avg_response_time': sum(response_times) / len(response_times),
                    'min_response_time': min(response_times),
                    'max_response_time': max(response_times),
                    'total_requests': len(self.test_results),
                    'success_rate': len([r for r in self.test_results if r.status == 'passed']) / len(self.test_results) * 100
                }

        # Identify security issues
        security_issues = []
        for result in self.test_results:
            if result.status_code in [401, 403, 500]:
                security_issues.append(f"Security issue in {result.endpoint}: {result.error_message}")

        # Identify contract violations
        contract_violations = []
        for result in self.test_results:
            if result.test_type == TestType.CONTRACT and result.status == 'failed':
                contract_violations.append(f"Contract violation in {result.endpoint}: {result.error_message}")

        # Generate recommendations
        recommendations = []
        if test_coverage < 80:
            recommendations.append("Increase API test coverage to at least 80%")
        if performance_metrics.get('avg_response_time', 0) > 1.0:
            recommendations.append("Optimize API response times")
        if security_issues:
            recommendations.append("Address security issues in API endpoints")
        if contract_violations:
            recommendations.append("Fix contract violations")

        analysis_time = time.time() - start_time

        return APIManagementReport(
            total_endpoints=total_endpoints,
            tested_endpoints=tested_endpoints,
            test_coverage=test_coverage,
            performance_metrics=performance_metrics,
            security_issues=security_issues,
            contract_violations=contract_violations,
            recommendations=recommendations,
            analysis_time=analysis_time
        )

    def save_api_report(self, report: APIManagementReport) -> str:
        """Save API management report"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Save JSON report
        json_path = self.project_root / "artifacts" / f"api_report_{timestamp}.json"
        json_path.parent.mkdir(exist_ok=True)

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, default=str)

        return str(json_path)

def main():
    """Main function for testing"""
    api_system = APIManagementSystem(".")

    # Create sample endpoint
    endpoint = APIEndpoint(
        path="/api/v1/test",
        method=APIMethod.POST,
        version=APIVersion.V1,
        description="Test endpoint",
        parameters=[],
        request_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "integer"}
            },
            "required": ["name"]
        },
        response_schema={
            "200": {"description": "Success"},
            "400": {"description": "Bad Request"}
        },
        status_codes={200: "Success", 400: "Bad Request"},
        examples=[],
        tags=["test"]
    )

    # Register endpoint
    endpoint_id = api_system.register_endpoint(endpoint)
    print(f"Registered endpoint: {endpoint_id}")

    # Create contract
    contract = api_system.create_contract(endpoint_id, endpoint.request_schema)
    print(f"Created contract: {contract.contract_id}")

    # Generate OpenAPI spec
    spec_file = api_system.save_openapi_spec()
    print(f"OpenAPI spec saved: {spec_file}")

    # Generate report
    report = api_system.generate_api_report()
    json_path = api_system.save_api_report(report)
    print(f"API report saved: {json_path}")

if __name__ == "__main__":
    main()
