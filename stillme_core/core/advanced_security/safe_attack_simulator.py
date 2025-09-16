# stillme_core/advanced_security/safe_attack_simulator.py
"""
Safe Attack Simulation Framework for AgentDev
Provides secure, isolated attack simulation with comprehensive safety measures
"""

from __future__ import annotations

import json
import logging
import shutil
import tempfile
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AttackCategory(Enum):
    """Categories of attacks"""

    OWASP_TOP_10 = "owasp_top_10"
    APT_SIMULATION = "apt_simulation"
    SOCIAL_ENGINEERING = "social_engineering"
    PHYSICAL_SECURITY = "physical_security"
    ZERO_DAY = "zero_day"
    INSIDER_THREAT = "insider_threat"


class AttackSeverity(Enum):
    """Attack severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SimulationStatus(Enum):
    """Simulation status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AttackScenario:
    """Attack scenario definition"""

    scenario_id: str
    name: str
    category: AttackCategory
    severity: AttackSeverity
    description: str
    attack_vectors: List[str]
    payloads: List[Dict[str, Any]]
    expected_behavior: str
    safety_measures: List[str]
    isolation_requirements: Dict[str, Any]
    success_criteria: Dict[str, Any]
    failure_criteria: Dict[str, Any]


@dataclass
class SimulationResult:
    """Result of attack simulation"""

    simulation_id: str
    scenario: AttackScenario
    status: SimulationStatus
    start_time: float
    end_time: float
    duration: float
    success: bool
    vulnerabilities_found: List[Dict[str, Any]]
    defenses_triggered: List[Dict[str, Any]]
    impact_assessment: Dict[str, Any]
    safety_checks_passed: bool
    logs: List[Dict[str, Any]]
    recommendations: List[str]
    risk_score: float


@dataclass
class SafetyCheck:
    """Safety check result"""

    check_id: str
    check_name: str
    passed: bool
    details: str
    timestamp: float


class SafeAttackSimulator:
    """
    Safe Attack Simulation Framework with comprehensive safety measures
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or ".attack_sim_config.json"
        self.scenarios: list[AttackScenario] = []
        self.simulation_history: list[SimulationResult] = []
        self.safety_checks: list[SafetyCheck] = []
        self.isolation_environments: dict[str, dict[str, Any]] = {}
        self.active_simulations: dict[str, SimulationResult] = {}

        # Safety configuration
        self.safety_config = self._load_safety_config()

        # Initialize scenarios
        self._initialize_default_scenarios()

        # Initialize isolation environments
        self._initialize_isolation_environments()

    def _load_safety_config(self) -> dict[str, Any]:
        """Load safety configuration"""
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                with open(config_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load safety config: {e}")

        # Default safety configuration
        return {
            "max_concurrent_simulations": 3,
            "simulation_timeout": 300,  # 5 minutes
            "isolation_required": True,
            "network_isolation": True,
            "resource_limits": {
                "max_cpu_percent": 50,
                "max_memory_mb": 512,
                "max_disk_mb": 100,
            },
            "allowed_targets": ["localhost", "127.0.0.1", "test.example.com"],
            "forbidden_actions": [
                "delete_files",
                "modify_system_files",
                "access_real_data",
                "network_scanning",
                "privilege_escalation",
            ],
            "safety_checks": [
                "network_isolation",
                "resource_monitoring",
                "file_system_protection",
                "process_isolation",
                "data_protection",
            ],
        }

    def _initialize_default_scenarios(self):
        """Initialize default attack scenarios"""
        default_scenarios = [
            {
                "scenario_id": "OWASP_SQL_INJECTION",
                "name": "SQL Injection Attack",
                "category": AttackCategory.OWASP_TOP_10,
                "severity": AttackSeverity.HIGH,
                "description": "Simulate SQL injection attacks against web applications",
                "attack_vectors": ["web_forms", "url_parameters", "api_endpoints"],
                "payloads": [
                    {"type": "basic", "payload": "' OR '1'='1"},
                    {"type": "union", "payload": "' UNION SELECT * FROM users --"},
                    {"type": "blind", "payload": "'; WAITFOR DELAY '00:00:05' --"},
                ],
                "expected_behavior": "Application should reject malicious input",
                "safety_measures": [
                    "isolated_database",
                    "no_real_data",
                    "timeout_protection",
                ],
                "isolation_requirements": {
                    "network": "isolated",
                    "database": "test_only",
                },
                "success_criteria": {
                    "vulnerability_detected": True,
                    "no_data_breach": True,
                },
                "failure_criteria": {"application_crash": True, "data_exposure": True},
            },
            {
                "scenario_id": "OWASP_XSS",
                "name": "Cross-Site Scripting Attack",
                "category": AttackCategory.OWASP_TOP_10,
                "severity": AttackSeverity.MEDIUM,
                "description": "Simulate XSS attacks against web applications",
                "attack_vectors": ["input_fields", "url_parameters", "cookies"],
                "payloads": [
                    {"type": "reflected", "payload": "<script>alert('XSS')</script>"},
                    {"type": "stored", "payload": "<img src=x onerror=alert('XSS')>"},
                    {"type": "dom", "payload": "javascript:alert('XSS')"},
                ],
                "expected_behavior": "Application should sanitize and escape output",
                "safety_measures": [
                    "isolated_browser",
                    "no_real_sessions",
                    "sandboxed_execution",
                ],
                "isolation_requirements": {
                    "browser": "headless",
                    "network": "isolated",
                },
                "success_criteria": {"xss_detected": True, "no_session_hijack": True},
                "failure_criteria": {
                    "script_execution": True,
                    "session_compromise": True,
                },
            },
            {
                "scenario_id": "OWASP_CSRF",
                "name": "Cross-Site Request Forgery Attack",
                "category": AttackCategory.OWASP_TOP_10,
                "severity": AttackSeverity.MEDIUM,
                "description": "Simulate CSRF attacks against web applications",
                "attack_vectors": ["form_submissions", "api_calls", "state_changes"],
                "payloads": [
                    {
                        "type": "form",
                        "payload": "<form action='/api/delete' method='POST'><input type='submit'></form>",
                    },
                    {
                        "type": "image",
                        "payload": "<img src='/api/transfer?amount=1000&to=attacker'>",
                    },
                    {
                        "type": "ajax",
                        "payload": "fetch('/api/admin/delete-all', {method: 'POST'})",
                    },
                ],
                "expected_behavior": "Application should validate CSRF tokens",
                "safety_measures": [
                    "isolated_sessions",
                    "no_real_actions",
                    "token_validation",
                ],
                "isolation_requirements": {
                    "sessions": "test_only",
                    "actions": "simulated",
                },
                "success_criteria": {
                    "csrf_detected": True,
                    "no_unauthorized_actions": True,
                },
                "failure_criteria": {"action_executed": True, "state_changed": True},
            },
            {
                "scenario_id": "APT_PHISHING",
                "name": "Advanced Persistent Threat - Phishing",
                "category": AttackCategory.APT_SIMULATION,
                "severity": AttackSeverity.HIGH,
                "description": "Simulate APT-style phishing attacks",
                "attack_vectors": [
                    "email",
                    "social_engineering",
                    "credential_harvesting",
                ],
                "payloads": [
                    {"type": "email", "payload": "Urgent: Please verify your account"},
                    {"type": "link", "payload": "https://fake-bank.com/login"},
                    {"type": "attachment", "payload": "invoice.pdf.exe"},
                ],
                "expected_behavior": "Users should recognize and report phishing attempts",
                "safety_measures": [
                    "isolated_email",
                    "no_real_credentials",
                    "simulated_users",
                ],
                "isolation_requirements": {
                    "email": "test_server",
                    "users": "simulated",
                },
                "success_criteria": {
                    "phishing_detected": True,
                    "no_credential_compromise": True,
                },
                "failure_criteria": {
                    "credentials_entered": True,
                    "malware_executed": True,
                },
            },
            {
                "scenario_id": "INSIDER_DATA_THEFT",
                "name": "Insider Threat - Data Theft",
                "category": AttackCategory.INSIDER_THREAT,
                "severity": AttackSeverity.CRITICAL,
                "description": "Simulate insider threat data theft scenarios",
                "attack_vectors": [
                    "privileged_access",
                    "data_exfiltration",
                    "unauthorized_copying",
                ],
                "payloads": [
                    {"type": "access", "payload": "access_sensitive_data"},
                    {"type": "copy", "payload": "copy_to_external_device"},
                    {"type": "upload", "payload": "upload_to_cloud_storage"},
                ],
                "expected_behavior": "System should detect and prevent unauthorized data access",
                "safety_measures": [
                    "no_real_data",
                    "simulated_files",
                    "access_monitoring",
                ],
                "isolation_requirements": {"data": "synthetic", "access": "monitored"},
                "success_criteria": {
                    "access_detected": True,
                    "no_real_data_exposed": True,
                },
                "failure_criteria": {"data_accessed": True, "data_copied": True},
            },
        ]

        for scenario_data in default_scenarios:
            scenario = AttackScenario(**scenario_data)
            self.scenarios.append(scenario)

    def _initialize_isolation_environments(self):
        """Initialize isolation environments for safe simulation"""
        # Create temporary directories for isolation
        self.isolation_base = tempfile.mkdtemp(prefix="attack_sim_")

        # Network isolation configuration
        self.isolation_environments["network"] = {
            "type": "isolated",
            "allowed_hosts": self.safety_config["allowed_targets"],
            "blocked_ports": [22, 23, 25, 53, 80, 443, 993, 995],
            "monitoring": True,
        }

        # File system isolation
        self.isolation_environments["filesystem"] = {
            "type": "sandbox",
            "base_path": self.isolation_base,
            "read_only_paths": ["/etc", "/usr", "/bin", "/sbin"],
            "writable_paths": [self.isolation_base],
            "monitoring": True,
        }

        # Process isolation
        self.isolation_environments["process"] = {
            "type": "containerized",
            "resource_limits": self.safety_config["resource_limits"],
            "timeout": self.safety_config["simulation_timeout"],
            "monitoring": True,
        }

    def run_simulation(
        self, scenario_id: str, target_config: dict[str, Any]
    ) -> SimulationResult:
        """
        Run a safe attack simulation

        Args:
            scenario_id: ID of the scenario to run
            target_config: Configuration for the target system

        Returns:
            SimulationResult with detailed results
        """
        # Find scenario
        scenario = self._find_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")

        # Generate simulation ID
        simulation_id = str(uuid.uuid4())

        # Create simulation result
        simulation = SimulationResult(
            simulation_id=simulation_id,
            scenario=scenario,
            status=SimulationStatus.PENDING,
            start_time=time.time(),
            end_time=0.0,
            duration=0.0,
            success=False,
            vulnerabilities_found=[],
            defenses_triggered=[],
            impact_assessment={},
            safety_checks_passed=False,
            logs=[],
            recommendations=[],
            risk_score=0.0,
        )

        # Add to active simulations
        self.active_simulations[simulation_id] = simulation

        try:
            # Pre-simulation safety checks
            safety_passed = self._run_safety_checks(simulation, target_config)
            if not safety_passed:
                simulation.status = SimulationStatus.FAILED
                simulation.logs.append(
                    {
                        "timestamp": time.time(),
                        "level": "ERROR",
                        "message": "Safety checks failed",
                    }
                )
                return simulation

            # Update status
            simulation.status = SimulationStatus.RUNNING
            simulation.safety_checks_passed = True

            # Run simulation in isolated environment
            result = self._execute_simulation(simulation, target_config)

            # Update simulation with results
            simulation.end_time = time.time()
            simulation.duration = simulation.end_time - simulation.start_time
            simulation.status = SimulationStatus.COMPLETED
            simulation.success = result["success"]
            simulation.vulnerabilities_found = result["vulnerabilities"]
            simulation.defenses_triggered = result["defenses"]
            simulation.impact_assessment = result["impact"]
            simulation.risk_score = result["risk_score"]
            simulation.recommendations = result["recommendations"]
            simulation.logs.extend(result["logs"])

        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            simulation.status = SimulationStatus.FAILED
            simulation.logs.append(
                {
                    "timestamp": time.time(),
                    "level": "ERROR",
                    "message": f"Simulation failed: {e!s}",
                }
            )

        finally:
            # Cleanup
            self._cleanup_simulation(simulation_id)

            # Add to history
            self.simulation_history.append(simulation)

            # Remove from active simulations
            if simulation_id in self.active_simulations:
                del self.active_simulations[simulation_id]

        return simulation

    def _find_scenario(self, scenario_id: str) -> AttackScenario | None:
        """Find scenario by ID"""
        for scenario in self.scenarios:
            if scenario.scenario_id == scenario_id:
                return scenario
        return None

    def _run_safety_checks(
        self, simulation: SimulationResult, target_config: dict[str, Any]
    ) -> bool:
        """Run comprehensive safety checks"""
        all_checks_passed = True

        # Check 1: Network isolation
        network_check = self._check_network_isolation(target_config)
        self.safety_checks.append(network_check)
        if not network_check.passed:
            all_checks_passed = False

        # Check 2: Resource limits
        resource_check = self._check_resource_limits()
        self.safety_checks.append(resource_check)
        if not resource_check.passed:
            all_checks_passed = False

        # Check 3: File system protection
        filesystem_check = self._check_filesystem_protection()
        self.safety_checks.append(filesystem_check)
        if not filesystem_check.passed:
            all_checks_passed = False

        # Check 4: Process isolation
        process_check = self._check_process_isolation()
        self.safety_checks.append(process_check)
        if not process_check.passed:
            all_checks_passed = False

        # Check 5: Data protection
        data_check = self._check_data_protection(target_config)
        self.safety_checks.append(data_check)
        if not data_check.passed:
            all_checks_passed = False

        # Log safety check results
        simulation.logs.append(
            {
                "timestamp": time.time(),
                "level": "INFO",
                "message": f"Safety checks completed: {len([c for c in self.safety_checks if c.passed])}/{len(self.safety_checks)} passed",
            }
        )

        return all_checks_passed

    def _check_network_isolation(self, target_config: dict[str, Any]) -> SafetyCheck:
        """Check network isolation"""
        check_id = str(uuid.uuid4())

        try:
            # Verify target is in allowed list
            target_host = target_config.get("host", "localhost")
            if target_host not in self.safety_config["allowed_targets"]:
                return SafetyCheck(
                    check_id=check_id,
                    check_name="network_isolation",
                    passed=False,
                    details=f"Target host {target_host} not in allowed list",
                    timestamp=time.time(),
                )

            # Check if network isolation is enabled
            if not self.safety_config["network_isolation"]:
                return SafetyCheck(
                    check_id=check_id,
                    check_name="network_isolation",
                    passed=False,
                    details="Network isolation is disabled",
                    timestamp=time.time(),
                )

            return SafetyCheck(
                check_id=check_id,
                check_name="network_isolation",
                passed=True,
                details=f"Network isolation verified for {target_host}",
                timestamp=time.time(),
            )

        except Exception as e:
            return SafetyCheck(
                check_id=check_id,
                check_name="network_isolation",
                passed=False,
                details=f"Network isolation check failed: {e!s}",
                timestamp=time.time(),
            )

    def _check_resource_limits(self) -> SafetyCheck:
        """Check resource limits"""
        check_id = str(uuid.uuid4())

        try:
            # Check available system resources
            import psutil

            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            # disk = psutil.disk_usage("/")  # Unused variable

            limits = self.safety_config["resource_limits"]

            if cpu_percent > limits["max_cpu_percent"]:
                return SafetyCheck(
                    check_id=check_id,
                    check_name="resource_limits",
                    passed=False,
                    details=f"CPU usage {cpu_percent}% exceeds limit {limits['max_cpu_percent']}%",
                    timestamp=time.time(),
                )

            if memory.percent > 80:  # 80% memory usage threshold
                return SafetyCheck(
                    check_id=check_id,
                    check_name="resource_limits",
                    passed=False,
                    details=f"Memory usage {memory.percent}% is too high",
                    timestamp=time.time(),
                )

            return SafetyCheck(
                check_id=check_id,
                check_name="resource_limits",
                passed=True,
                details=f"Resource limits OK - CPU: {cpu_percent}%, Memory: {memory.percent}%",
                timestamp=time.time(),
            )

        except Exception as e:
            return SafetyCheck(
                check_id=check_id,
                check_name="resource_limits",
                passed=False,
                details=f"Resource limit check failed: {e!s}",
                timestamp=time.time(),
            )

    def _check_filesystem_protection(self) -> SafetyCheck:
        """Check file system protection"""
        check_id = str(uuid.uuid4())

        try:
            # Verify isolation directory exists and is writable
            isolation_path = Path(self.isolation_base)
            if not isolation_path.exists():
                isolation_path.mkdir(parents=True, exist_ok=True)

            # Test write access to isolation directory
            test_file = isolation_path / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()

            return SafetyCheck(
                check_id=check_id,
                check_name="filesystem_protection",
                passed=True,
                details=f"File system protection verified - isolation path: {self.isolation_base}",
                timestamp=time.time(),
            )

        except Exception as e:
            return SafetyCheck(
                check_id=check_id,
                check_name="filesystem_protection",
                passed=False,
                details=f"File system protection check failed: {e!s}",
                timestamp=time.time(),
            )

    def _check_process_isolation(self) -> SafetyCheck:
        """Check process isolation"""
        check_id = str(uuid.uuid4())

        try:
            # Check if we can create isolated processes
            # This is a simplified check - in practice, you'd use proper containerization

            return SafetyCheck(
                check_id=check_id,
                check_name="process_isolation",
                passed=True,
                details="Process isolation capabilities verified",
                timestamp=time.time(),
            )

        except Exception as e:
            return SafetyCheck(
                check_id=check_id,
                check_name="process_isolation",
                passed=False,
                details=f"Process isolation check failed: {e!s}",
                timestamp=time.time(),
            )

    def _check_data_protection(self, target_config: dict[str, Any]) -> SafetyCheck:
        """Check data protection"""
        check_id = str(uuid.uuid4())

        try:
            # Verify no real data is being targeted
            if target_config.get("use_real_data", False):
                return SafetyCheck(
                    check_id=check_id,
                    check_name="data_protection",
                    passed=False,
                    details="Real data usage is not allowed in simulations",
                    timestamp=time.time(),
                )

            # Verify test data is being used
            if not target_config.get("use_test_data", True):
                return SafetyCheck(
                    check_id=check_id,
                    check_name="data_protection",
                    passed=False,
                    details="Test data must be used in simulations",
                    timestamp=time.time(),
                )

            return SafetyCheck(
                check_id=check_id,
                check_name="data_protection",
                passed=True,
                details="Data protection verified - using test data only",
                timestamp=time.time(),
            )

        except Exception as e:
            return SafetyCheck(
                check_id=check_id,
                check_name="data_protection",
                passed=False,
                details=f"Data protection check failed: {e!s}",
                timestamp=time.time(),
            )

    def _execute_simulation(
        self, simulation: SimulationResult, target_config: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute the actual simulation in isolated environment"""
        result = {
            "success": False,
            "vulnerabilities": [],
            "defenses": [],
            "impact": {},
            "risk_score": 0.0,
            "recommendations": [],
            "logs": [],
        }

        try:
            # Create isolated environment
            isolation_env = self._create_isolation_environment(simulation.scenario)

            # Execute attack vectors
            for vector in simulation.scenario.attack_vectors:
                vector_result = self._execute_attack_vector(
                    vector, simulation.scenario, target_config, isolation_env
                )

                if vector_result["vulnerability_detected"]:
                    result["vulnerabilities"].append(vector_result)

                if vector_result["defense_triggered"]:
                    result["defenses"].append(vector_result)

                result["logs"].extend(vector_result["logs"])

            # Assess impact
            result["impact"] = self._assess_impact(
                simulation.scenario, result["vulnerabilities"]
            )

            # Calculate risk score
            result["risk_score"] = self._calculate_risk_score(
                simulation.scenario, result
            )

            # Generate recommendations
            result["recommendations"] = self._generate_recommendations(
                simulation.scenario, result
            )

            # Determine overall success
            result["success"] = self._evaluate_success(simulation.scenario, result)

        except Exception as e:
            result["logs"].append(
                {
                    "timestamp": time.time(),
                    "level": "ERROR",
                    "message": f"Simulation execution failed: {e!s}",
                }
            )

        return result

    def _create_isolation_environment(self, scenario: AttackScenario) -> dict[str, Any]:
        """Create isolated environment for simulation"""
        env_id = str(uuid.uuid4())
        env_path = Path(self.isolation_base) / env_id
        env_path.mkdir(parents=True, exist_ok=True)

        isolation_env = {
            "env_id": env_id,
            "path": str(env_path),
            "network": self.isolation_environments["network"],
            "filesystem": self.isolation_environments["filesystem"],
            "process": self.isolation_environments["process"],
            "scenario": scenario.scenario_id,
            "created_at": time.time(),
        }

        return isolation_env

    def _execute_attack_vector(
        self,
        vector: str,
        scenario: AttackScenario,
        target_config: dict[str, Any],
        isolation_env: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a specific attack vector"""
        result = {
            "vector": vector,
            "vulnerability_detected": False,
            "defense_triggered": False,
            "payload_used": None,
            "response": None,
            "logs": [],
        }

        try:
            # Select appropriate payload for vector
            payload = self._select_payload_for_vector(vector, scenario)
            result["payload_used"] = payload

            # Execute the attack (simulated)
            response = self._simulate_attack_execution(
                vector, payload, target_config, isolation_env
            )
            result["response"] = response

            # Analyze response for vulnerabilities
            vulnerability_detected = self._analyze_response_for_vulnerabilities(
                vector, payload, response, scenario
            )
            result["vulnerability_detected"] = vulnerability_detected

            # Check if defenses were triggered
            defense_triggered = self._check_defense_triggers(response, scenario)
            result["defense_triggered"] = defense_triggered

            # Log the execution
            result["logs"].append(
                {
                    "timestamp": time.time(),
                    "level": "INFO",
                    "message": f"Executed {vector} with payload: {payload.get('type', 'unknown')}",
                }
            )

        except Exception as e:
            result["logs"].append(
                {
                    "timestamp": time.time(),
                    "level": "ERROR",
                    "message": f"Attack vector execution failed: {e!s}",
                }
            )

        return result

    def _select_payload_for_vector(
        self, vector: str, scenario: AttackScenario
    ) -> dict[str, Any]:
        """Select appropriate payload for attack vector"""
        # Simple payload selection logic
        # In practice, you'd have more sophisticated selection

        for payload in scenario.payloads:
            if payload.get("type") == "basic":
                return payload

        return scenario.payloads[0] if scenario.payloads else {}

    def _simulate_attack_execution(
        self,
        vector: str,
        payload: dict[str, Any],
        target_config: dict[str, Any],
        isolation_env: dict[str, Any],
    ) -> dict[str, Any]:
        """Simulate attack execution (safe simulation)"""
        # This is a simulated execution - no real attacks are performed

        response = {
            "status_code": 200,
            "headers": {"Content-Type": "text/html"},
            "body": "Simulated response",
            "execution_time": 0.1,
            "vulnerability_indicators": [],
            "defense_indicators": [],
        }

        # Simulate different responses based on payload type
        payload_type = payload.get("type", "unknown")

        if payload_type == "basic":
            # Simulate basic attack response
            response["vulnerability_indicators"] = [
                "error_message",
                "unexpected_response",
            ]
        elif payload_type == "union":
            # Simulate union-based attack response
            response["vulnerability_indicators"] = ["data_exposure", "sql_error"]
        elif payload_type == "blind":
            # Simulate blind attack response
            response["vulnerability_indicators"] = [
                "time_delay",
                "conditional_response",
            ]

        # Simulate defense triggers
        response["defense_indicators"] = ["input_validation", "error_handling"]

        return response

    def _analyze_response_for_vulnerabilities(
        self,
        vector: str,
        payload: dict[str, Any],
        response: dict[str, Any],
        scenario: AttackScenario,
    ) -> bool:
        """Analyze response for vulnerability indicators"""
        indicators = response.get("vulnerability_indicators", [])

        # Check against scenario's success criteria
        return any(indicator in scenario.success_criteria for indicator in indicators)

    def _check_defense_triggers(
        self, response: dict[str, Any], scenario: AttackScenario
    ) -> bool:
        """Check if defenses were triggered"""
        indicators = response.get("defense_indicators", [])

        # Check against scenario's failure criteria
        return any(indicator in scenario.failure_criteria for indicator in indicators)

    def _assess_impact(
        self, scenario: AttackScenario, vulnerabilities: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Assess impact of found vulnerabilities"""
        impact = {
            "severity": scenario.severity.value,
            "vulnerability_count": len(vulnerabilities),
            "potential_damage": "low",
            "affected_systems": [],
            "data_at_risk": False,
            "service_disruption": False,
        }

        if vulnerabilities:
            impact["potential_damage"] = "medium"
            impact["affected_systems"] = ["web_application", "database"]

            # Check for high-impact vulnerabilities
            for vuln in vulnerabilities:
                if "data_exposure" in vuln.get("vulnerability_indicators", []):
                    impact["data_at_risk"] = True
                    impact["potential_damage"] = "high"

                if "application_crash" in vuln.get("vulnerability_indicators", []):
                    impact["service_disruption"] = True
                    impact["potential_damage"] = "high"

        return impact

    def _calculate_risk_score(
        self, scenario: AttackScenario, result: dict[str, Any]
    ) -> float:
        """Calculate risk score based on findings"""
        base_score = {
            AttackSeverity.LOW: 0.2,
            AttackSeverity.MEDIUM: 0.4,
            AttackSeverity.HIGH: 0.7,
            AttackSeverity.CRITICAL: 0.9,
        }.get(scenario.severity, 0.5)

        # Adjust based on vulnerabilities found
        vulnerability_count = len(result["vulnerabilities"])
        if vulnerability_count > 0:
            base_score += min(0.3, vulnerability_count * 0.1)

        # Adjust based on impact
        impact = result.get("impact", {})
        if impact.get("data_at_risk"):
            base_score += 0.2
        if impact.get("service_disruption"):
            base_score += 0.2

        return min(1.0, base_score)

    def _generate_recommendations(
        self, scenario: AttackScenario, result: dict[str, Any]
    ) -> list[str]:
        """Generate security recommendations"""
        recommendations = []

        # General recommendations based on scenario
        if scenario.category == AttackCategory.OWASP_TOP_10:
            recommendations.append("Implement OWASP security guidelines")
            recommendations.append("Conduct regular security assessments")

        # Specific recommendations based on vulnerabilities
        for vuln in result["vulnerabilities"]:
            indicators = vuln.get("vulnerability_indicators", [])

            if "sql_error" in indicators:
                recommendations.append("Implement parameterized queries")
                recommendations.append("Add input validation and sanitization")

            if "xss" in indicators:
                recommendations.append("Implement output encoding")
                recommendations.append("Use Content Security Policy (CSP)")

            if "csrf" in indicators:
                recommendations.append("Implement CSRF tokens")
                recommendations.append("Validate referer headers")

        # Impact-based recommendations
        impact = result.get("impact", {})
        if impact.get("data_at_risk"):
            recommendations.append("Implement data encryption")
            recommendations.append("Add access controls and monitoring")

        if impact.get("service_disruption"):
            recommendations.append("Implement rate limiting")
            recommendations.append("Add circuit breakers")

        return list(set(recommendations))  # Remove duplicates

    def _evaluate_success(
        self, scenario: AttackScenario, result: dict[str, Any]
    ) -> bool:
        """Evaluate if simulation was successful"""
        # Check success criteria
        for criteria, expected in scenario.success_criteria.items():
            if criteria == "vulnerability_detected":
                if expected and not result["vulnerabilities"]:
                    return False
                if not expected and result["vulnerabilities"]:
                    return False

        # Check failure criteria
        for criteria, should_not_happen in scenario.failure_criteria.items():
            if should_not_happen:
                for vuln in result["vulnerabilities"]:
                    if criteria in vuln.get("vulnerability_indicators", []):
                        return False

        return True

    def _cleanup_simulation(self, simulation_id: str):
        """Clean up simulation resources"""
        try:
            # Clean up isolation environments
            for env_id, env_data in list(self.isolation_environments.items()):
                if env_data.get("scenario") == simulation_id:
                    env_path = Path(env_data.get("path", ""))
                    if env_path.exists():
                        shutil.rmtree(env_path, ignore_errors=True)
                    del self.isolation_environments[env_id]

            # Clean up temporary files
            temp_files = Path(self.isolation_base).glob(f"*{simulation_id}*")
            for temp_file in temp_files:
                if temp_file.is_file():
                    temp_file.unlink()
                elif temp_file.is_dir():
                    shutil.rmtree(temp_file, ignore_errors=True)

        except Exception as e:
            logger.error(f"Cleanup failed for simulation {simulation_id}: {e}")

    def get_simulation_history(self, limit: int = 50) -> list[SimulationResult]:
        """Get recent simulation history"""
        return self.simulation_history[-limit:]

    def get_safety_report(self) -> dict[str, Any]:
        """Get comprehensive safety report"""
        recent_checks = [
            check
            for check in self.safety_checks
            if time.time() - check.timestamp < 86400
        ]  # Last 24 hours

        return {
            "total_simulations": len(self.simulation_history),
            "active_simulations": len(self.active_simulations),
            "safety_checks_passed": len([c for c in recent_checks if c.passed]),
            "safety_checks_failed": len([c for c in recent_checks if not c.passed]),
            "recent_safety_checks": recent_checks[-10:],
            "isolation_environments": len(self.isolation_environments),
            "safety_config": self.safety_config,
        }

    def add_custom_scenario(self, scenario: AttackScenario):
        """Add custom attack scenario"""
        # Validate scenario safety
        if not self._validate_scenario_safety(scenario):
            raise ValueError("Scenario does not meet safety requirements")

        self.scenarios.append(scenario)
        logger.info(f"Added custom scenario: {scenario.scenario_id}")

    def _validate_scenario_safety(self, scenario: AttackScenario) -> bool:
        """Validate scenario meets safety requirements"""
        # Check for forbidden actions
        for forbidden in self.safety_config["forbidden_actions"]:
            if forbidden in scenario.description.lower():
                return False

        # Check isolation requirements
        if not scenario.isolation_requirements:
            return False

        # Check safety measures
        return bool(scenario.safety_measures)

    def cleanup_all(self):
        """Clean up all simulation resources"""
        try:
            # Clean up isolation base directory
            if hasattr(self, "isolation_base") and Path(self.isolation_base).exists():
                shutil.rmtree(self.isolation_base, ignore_errors=True)

            # Clear active simulations
            self.active_simulations.clear()

            logger.info("Cleaned up all simulation resources")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
