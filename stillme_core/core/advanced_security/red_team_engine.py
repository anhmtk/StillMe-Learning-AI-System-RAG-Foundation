#!/usr/bin/env python3
"""
🎯 RED TEAM ENGINE - PHASE 2
🎯 ĐỘNG CƠ RED TEAM - GIAI ĐOẠN 2

PURPOSE / MỤC ĐÍCH:
- AI-powered attack generation và pattern-based detection
- Tạo tấn công dựa trên AI và phát hiện lỗ hổng theo pattern
- Adaptive attack strategies với learning capabilities
- Chiến lược tấn công thích ứng với khả năng học
- Integration với Experience Memory và Decision Engine
- Tích hợp với Experience Memory và Decision Engine
- Safe execution trong sandbox environment
- Thực thi an toàn trong môi trường sandbox
"""

import asyncio
import json
import logging
import re
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

# Import existing modules for integration
from stillme_core.decision_making.decision_engine import RiskLevel

try:
    from stillme_core.core.advanced_security.safe_attack_simulator import (
        SafeAttackSimulator,
    )
    from stillme_core.core.advanced_security.sandbox_controller import (
        SandboxController,
        SandboxType,
    )
    from stillme_core.decision_making.decision_engine import (
        DecisionEngine,
    )
    from stillme_core.modules.layered_memory_v1 import LayeredMemoryV1
except ImportError as e:
    logging.warning(f"Some modules not available: {e}")

logger = logging.getLogger(__name__)


class AttackStrategy(Enum):
    """Attack strategy types"""

    BRUTE_FORCE = "brute_force"
    STEALTH = "stealth"
    ADAPTIVE = "adaptive"
    PERSISTENT = "persistent"
    MULTI_VECTOR = "multi_vector"


class VulnerabilityType(Enum):
    """Vulnerability types"""

    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    BUFFER_OVERFLOW = "buffer_overflow"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    AUTHENTICATION_BYPASS = "authentication_bypass"
    DATA_EXPOSURE = "data_exposure"
    CODE_INJECTION = "code_injection"
    PATH_TRAVERSAL = "path_traversal"
    INSECURE_DESERIALIZATION = "insecure_deserialization"


class AttackPhase(Enum):
    """Attack phases"""

    RECONNAISSANCE = "reconnaissance"
    SCANNING = "scanning"
    EXPLOITATION = "exploitation"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    CLEANUP = "cleanup"


@dataclass
class AttackContext:
    """Context for attack generation"""

    target_type: str  # web_app, api, database, etc.
    target_technology: str  # python, nodejs, java, etc.
    target_framework: str  # django, flask, express, etc.
    known_vulnerabilities: list[str]
    defense_mechanisms: list[str]
    previous_attacks: list[dict[str, Any]]
    success_rate: float
    environment_info: dict[str, Any]


@dataclass
class AttackPattern:
    """Attack pattern definition"""

    pattern_id: str
    name: str
    vulnerability_type: VulnerabilityType
    attack_phase: AttackPhase
    pattern_regex: str
    confidence_score: float
    success_rate: float
    detection_difficulty: float
    payload_templates: list[dict[str, Any]]
    mitigation_techniques: list[str]


@dataclass
class GeneratedAttack:
    """Generated attack payload"""

    attack_id: str
    pattern_id: str
    payload: str
    attack_vector: str
    target_parameter: str
    expected_response: str
    success_indicators: list[str]
    failure_indicators: list[str]
    risk_level: RiskLevel
    confidence: float
    adaptation_strategy: str | None = None


@dataclass
class AttackResult:
    """Result of attack execution"""

    attack_id: str
    success: bool
    response_code: int
    response_body: str
    response_time: float
    vulnerabilities_detected: list[str]
    defenses_triggered: list[str]
    adaptation_applied: bool
    learning_insights: list[str]
    risk_assessment: dict[str, Any]


class RedTeamEngine:
    """
    🎯 Advanced Red Team Engine với AI-powered capabilities
    🎯 Động cơ Red Team nâng cao với khả năng AI
    """

    def __init__(
        self, config: dict[str, Any] | None = None, config_path: str | None = None
    ):
        """
        Initialize Red Team Engine

        Args:
            config: Configuration dictionary
            config_path: Path to configuration file
        """
        self.config_path = config_path or ".red_team_config.json"
        if config is not None:
            self.config = config
        else:
            self.config = self._load_configuration()

        # Initialize components
        self.memory_manager = None
        self.decision_engine = None
        self.sandbox_controller = None
        self.attack_simulator = None

        # Attack patterns database
        self.attack_patterns: dict[str, AttackPattern] = {}
        self.attack_history: list[AttackResult] = []
        self.learning_insights: list[dict[str, Any]] = []

        # Performance metrics
        self.metrics = {
            "total_attacks": 0,
            "successful_attacks": 0,
            "patterns_learned": 0,
            "adaptations_made": 0,
            "vulnerabilities_found": 0,
        }

        # Initialize attack patterns
        self._initialize_attack_patterns()

        # Initialize components safely
        self._initialize_components()

        logger.info("🎯 RedTeamEngine initialized successfully")

    def _load_configuration(self) -> dict[str, Any]:
        """Load configuration from file"""
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                with open(config_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")

        # Default configuration
        return {
            "ai_attack_generation": {
                "enabled": True,
                "confidence_threshold": 0.7,
                "max_payloads_per_pattern": 10,
                "adaptation_enabled": True,
            },
            "pattern_detection": {
                "enabled": True,
                "min_confidence": 0.6,
                "max_patterns": 50,
                "learning_enabled": True,
            },
            "integration": {
                "memory_manager": True,
                "decision_engine": True,
                "sandbox_controller": True,
                "attack_simulator": True,
            },
            "safety": {
                "max_attack_duration": 300,  # 5 minutes
                "max_concurrent_attacks": 3,
                "sandbox_only": True,
                "no_real_targets": True,
            },
        }

    def _initialize_components(self):
        """Initialize integrated components safely"""
        try:
            # Initialize Experience Memory
            if self.config["integration"]["memory_manager"]:
                self.memory_manager = LayeredMemoryV1()
                logger.info("✅ Experience Memory integrated")
        except Exception as e:
            logger.warning(f"Memory manager not available: {e}")

        try:
            # Initialize Decision Engine
            if self.config["integration"]["decision_engine"]:
                self.decision_engine = DecisionEngine()
                logger.info("✅ Decision Engine integrated")
        except Exception as e:
            logger.warning(f"Decision engine not available: {e}")

        try:
            # Initialize Sandbox Controller
            if self.config["integration"]["sandbox_controller"]:
                self.sandbox_controller = SandboxController()
                logger.info("✅ Sandbox Controller integrated")
        except Exception as e:
            logger.warning(f"Sandbox controller not available: {e}")

        try:
            # Initialize Attack Simulator
            if self.config["integration"]["attack_simulator"]:
                self.attack_simulator = SafeAttackSimulator()
                logger.info("✅ Attack Simulator integrated")
        except Exception as e:
            logger.warning(f"Attack simulator not available: {e}")

    def _initialize_attack_patterns(self):
        """Initialize attack patterns database"""
        # SQL Injection Patterns
        sql_patterns = [
            {
                "pattern_id": "SQL_BASIC_UNION",
                "name": "Basic SQL Union Injection",
                "vulnerability_type": VulnerabilityType.SQL_INJECTION,
                "attack_phase": AttackPhase.EXPLOITATION,
                "pattern_regex": r"(?i)(union\s+select|union\s+all\s+select)",
                "confidence_score": 0.9,
                "success_rate": 0.7,
                "detection_difficulty": 0.3,
                "payload_templates": [
                    {"type": "union", "payload": "' UNION SELECT 1,2,3,4,5 --"},
                    {
                        "type": "union",
                        "payload": "' UNION ALL SELECT NULL,NULL,NULL,NULL --",
                    },
                    {
                        "type": "union",
                        "payload": "' UNION SELECT user(),version(),database(),4,5 --",
                    },
                ],
                "mitigation_techniques": [
                    "parameterized_queries",
                    "input_validation",
                    "sql_escaping",
                ],
            },
            {
                "pattern_id": "SQL_BLIND_TIME",
                "name": "Blind SQL Time-based Injection",
                "vulnerability_type": VulnerabilityType.SQL_INJECTION,
                "attack_phase": AttackPhase.EXPLOITATION,
                "pattern_regex": r"(?i)(sleep\s*\(|waitfor\s+delay|benchmark\s*\()",
                "confidence_score": 0.8,
                "success_rate": 0.6,
                "detection_difficulty": 0.5,
                "payload_templates": [
                    {"type": "blind", "payload": "'; WAITFOR DELAY '00:00:05' --"},
                    {"type": "blind", "payload": "' OR SLEEP(5) --"},
                    {
                        "type": "blind",
                        "payload": "' AND (SELECT * FROM (SELECT(SLEEP(5)))a) --",
                    },
                ],
                "mitigation_techniques": [
                    "parameterized_queries",
                    "timeout_limits",
                    "input_validation",
                ],
            },
        ]

        # XSS Patterns
        xss_patterns = [
            {
                "pattern_id": "XSS_REFLECTED",
                "name": "Reflected XSS",
                "vulnerability_type": VulnerabilityType.XSS,
                "attack_phase": AttackPhase.EXPLOITATION,
                "pattern_regex": r"(?i)(<script|javascript:|on\w+\s*=)",
                "confidence_score": 0.8,
                "success_rate": 0.6,
                "detection_difficulty": 0.4,
                "payload_templates": [
                    {"type": "script", "payload": "<script>alert('XSS')</script>"},
                    {"type": "event", "payload": "<img src=x onerror=alert('XSS')>"},
                    {"type": "javascript", "payload": "javascript:alert('XSS')"},
                ],
                "mitigation_techniques": [
                    "output_encoding",
                    "csp_headers",
                    "input_validation",
                ],
            }
        ]

        # Combine all patterns
        all_patterns = sql_patterns + xss_patterns

        for pattern_data in all_patterns:
            pattern = AttackPattern(**pattern_data)
            self.attack_patterns[pattern.pattern_id] = pattern

        logger.info(f"✅ Initialized {len(self.attack_patterns)} attack patterns")

    def run_light_security_check(self, repo_root: str = ".") -> dict[str, Any]:
        """
        Chạy security scan nhẹ, trả về dict chuẩn hoá:
        {
          "findings": [ { "id": str, "type": "secret|injection|dangerous_api", "path": str, "line": int, "severity": "LOW|MEDIUM|HIGH" } ],
          "score": float  # 0.0 ~ 1.0
        }
        """
        from stillme_core.utils.io_safe import safe_read_text

        results = {"findings": [], "score": 0.0}

        # Security patterns to check
        security_patterns = [
            (
                r"password\s*=\s*['\"][^'\"]+['\"]",
                "secret",
                "HIGH",
                "Hardcoded password",
            ),
            (r"api_key\s*=\s*['\"][^'\"]+['\"]", "secret", "HIGH", "Hardcoded API key"),
            (r"secret\s*=\s*['\"][^'\"]+['\"]", "secret", "HIGH", "Hardcoded secret"),
            (r"token\s*=\s*['\"][^'\"]+['\"]", "secret", "MEDIUM", "Hardcoded token"),
            (r"eval\s*\(", "dangerous_api", "MEDIUM", "Use of eval()"),
            (r"exec\s*\(", "dangerous_api", "MEDIUM", "Use of exec()"),
            (
                r"subprocess\.call\s*\(",
                "dangerous_api",
                "LOW",
                "Unsafe subprocess call",
            ),
            (r"os\.system\s*\(", "dangerous_api", "MEDIUM", "Unsafe system call"),
            (r"BEGIN PRIVATE KEY", "secret", "HIGH", "Private key in code"),
            (r"AWS_SECRET_ACCESS_KEY", "secret", "HIGH", "AWS secret key"),
            (r"sk-[a-zA-Z0-9]{48}", "secret", "HIGH", "OpenAI API key"),
            (r"ghp_[a-zA-Z0-9]{36}", "secret", "HIGH", "GitHub token"),
        ]

        try:
            # Scan Python files in repo
            project_root = Path(repo_root)
            python_files = list(project_root.glob("**/*.py"))

            # Limit to first 100 files to avoid performance issues
            for file_path in python_files[:100]:
                try:
                    # Skip if not a text file
                    if not file_path.is_file():
                        continue

                    # Read file safely
                    content = safe_read_text(file_path)
                    if not content:
                        continue

                    # Check each pattern
                    for (
                        pattern,
                        finding_type,
                        severity,
                        description,
                    ) in security_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            # Find line number for first match
                            lines = content.split("\n")
                            line_num = 1
                            for i, line in enumerate(lines):
                                if re.search(pattern, line, re.IGNORECASE):
                                    line_num = i + 1
                                    break

                            results["findings"].append(
                                {
                                    "id": f"SEC-{len(results['findings']) + 1}",
                                    "type": finding_type,
                                    "path": str(file_path.relative_to(project_root)),
                                    "line": line_num,
                                    "severity": severity,
                                    "description": description,
                                    "matches": len(matches),
                                }
                            )

                except Exception:
                    # Skip files that can't be processed
                    continue

            # Calculate risk score based on findings
            high_count = sum(1 for f in results["findings"] if f["severity"] == "HIGH")
            medium_count = sum(
                1 for f in results["findings"] if f["severity"] == "MEDIUM"
            )
            low_count = sum(1 for f in results["findings"] if f["severity"] == "LOW")

            # Weighted score: HIGH=1.0, MEDIUM=0.5, LOW=0.2
            results["score"] = min(
                (high_count * 1.0 + medium_count * 0.5 + low_count * 0.2) / 10.0, 1.0
            )

            return results

        except Exception as e:
            logger.error(f"Light security check failed: {e}")
            return {"findings": [], "score": 0.0, "error": str(e)}

    async def generate_adaptive_attacks(
        self, target_analysis: dict[str, Any], context: AttackContext
    ) -> list[GeneratedAttack]:
        """
        Generate adaptive attacks based on target analysis

        Args:
            target_analysis: Analysis of target system
            context: Attack context information

        Returns:
            List of generated attacks
        """
        logger.info("🎯 Generating adaptive attacks...")

        generated_attacks = []

        try:
            # Analyze target for vulnerability patterns
            detected_patterns = await self._analyze_target_patterns(
                target_analysis, context
            )

            # Generate attacks for each detected pattern
            for pattern_id, confidence in detected_patterns.items():
                if confidence >= self.config["pattern_detection"]["min_confidence"]:
                    pattern = self.attack_patterns.get(pattern_id)
                    if pattern:
                        attacks = await self._generate_attacks_for_pattern(
                            pattern, context
                        )
                        generated_attacks.extend(attacks)

            # Apply AI-powered adaptation
            if self.config["ai_attack_generation"]["adaptation_enabled"]:
                adapted_attacks = await self._apply_ai_adaptation(
                    generated_attacks, context
                )
                generated_attacks.extend(adapted_attacks)

            # Store in experience memory
            if self.memory_manager:
                await self._store_attack_generation_experience(
                    generated_attacks, context
                )

            logger.info(f"✅ Generated {len(generated_attacks)} adaptive attacks")

        except Exception as e:
            logger.error(f"❌ Attack generation failed: {e}")

        return generated_attacks

    async def _analyze_target_patterns(
        self, target_analysis: dict[str, Any], context: AttackContext
    ) -> dict[str, float]:
        """Analyze target for vulnerability patterns"""
        detected_patterns = {}

        try:
            # Get target code/configuration
            target_code = target_analysis.get("code", "")
            target_config = target_analysis.get("configuration", {})
            target_headers = target_analysis.get("headers", {})

            # Analyze each attack pattern
            for pattern_id, pattern in self.attack_patterns.items():
                confidence = 0.0

                # Check code patterns
                if target_code:
                    matches = re.findall(pattern.pattern_regex, target_code)
                    if matches:
                        confidence += 0.4 * min(
                            len(matches) / 5, 1.0
                        )  # Max 0.4 for code matches

                # Check configuration patterns
                if target_config:
                    config_text = json.dumps(target_config)
                    matches = re.findall(pattern.pattern_regex, config_text)
                    if matches:
                        confidence += 0.3 * min(
                            len(matches) / 3, 1.0
                        )  # Max 0.3 for config matches

                # Check header patterns
                if target_headers:
                    headers_text = json.dumps(target_headers)
                    matches = re.findall(pattern.pattern_regex, headers_text)
                    if matches:
                        confidence += 0.2 * min(
                            len(matches) / 2, 1.0
                        )  # Max 0.2 for header matches

                # Apply pattern-specific confidence adjustments
                confidence *= pattern.confidence_score

                if confidence >= self.config["pattern_detection"]["min_confidence"]:
                    detected_patterns[pattern_id] = confidence

            logger.info(f"🔍 Detected {len(detected_patterns)} vulnerability patterns")

        except Exception as e:
            logger.error(f"❌ Pattern analysis failed: {e}")

        return detected_patterns

    async def _generate_attacks_for_pattern(
        self, pattern: AttackPattern, context: AttackContext
    ) -> list[GeneratedAttack]:
        """Generate attacks for a specific pattern"""
        attacks = []

        try:
            # Limit number of payloads per pattern
            max_payloads = self.config["ai_attack_generation"][
                "max_payloads_per_pattern"
            ]
            payloads_to_use = pattern.payload_templates[:max_payloads]

            for i, payload_template in enumerate(payloads_to_use):
                attack_id = f"{pattern.pattern_id}_{i}_{int(time.time())}"

                # Generate attack payload
                payload = self._customize_payload(payload_template, context)

                # Determine attack vector
                attack_vector = self._determine_attack_vector(pattern, context)

                # Generate attack
                attack = GeneratedAttack(
                    attack_id=attack_id,
                    pattern_id=pattern.pattern_id,
                    payload=payload,
                    attack_vector=attack_vector,
                    target_parameter=self._determine_target_parameter(pattern, context),
                    expected_response=self._generate_expected_response(pattern),
                    success_indicators=self._generate_success_indicators(pattern),
                    failure_indicators=self._generate_failure_indicators(pattern),
                    risk_level=self._assess_attack_risk(pattern, payload),
                    confidence=pattern.confidence_score * context.success_rate,
                )

                attacks.append(attack)

            logger.info(
                f"✅ Generated {len(attacks)} attacks for pattern {pattern.pattern_id}"
            )

        except Exception as e:
            logger.error(
                f"❌ Attack generation for pattern {pattern.pattern_id} failed: {e}"
            )

        return attacks

    def _customize_payload(
        self, payload_template: dict[str, Any], context: AttackContext
    ) -> str:
        """Customize payload based on context"""
        base_payload = payload_template["payload"]

        # Apply technology-specific customization
        if context.target_technology.lower() == "python":
            # Python-specific payload modifications
            if "sleep" in base_payload.lower():
                base_payload = base_payload.replace("SLEEP", "time.sleep")
        elif context.target_technology.lower() == "nodejs":
            # Node.js-specific payload modifications
            if "sleep" in base_payload.lower():
                base_payload = base_payload.replace("SLEEP", "setTimeout")

        # Apply framework-specific customization
        if context.target_framework.lower() == "django":
            # Django-specific modifications
            base_payload = base_payload.replace("'", "\\'")
        elif context.target_framework.lower() == "flask":
            # Flask-specific modifications
            base_payload = base_payload.replace("'", "\\'")

        return base_payload

    def _determine_attack_vector(
        self, pattern: AttackPattern, context: AttackContext
    ) -> str:
        """Determine the best attack vector for the pattern"""
        # Simple heuristic-based vector selection
        if pattern.vulnerability_type == VulnerabilityType.SQL_INJECTION:
            return "database_query"
        elif pattern.vulnerability_type == VulnerabilityType.XSS:
            return "web_input"
        elif pattern.vulnerability_type == VulnerabilityType.CSRF:
            return "web_form"
        else:
            return "generic_input"

    def _determine_target_parameter(
        self, pattern: AttackPattern, context: AttackContext
    ) -> str:
        """Determine target parameter for the attack"""
        # Simple heuristic-based parameter selection
        if pattern.vulnerability_type == VulnerabilityType.SQL_INJECTION:
            return "query_param"
        elif pattern.vulnerability_type == VulnerabilityType.XSS:
            return "user_input"
        elif pattern.vulnerability_type == VulnerabilityType.CSRF:
            return "form_field"
        else:
            return "input_field"

    def _generate_expected_response(self, pattern: AttackPattern) -> str:
        """Generate expected response for the attack"""
        if pattern.vulnerability_type == VulnerabilityType.SQL_INJECTION:
            return "database_error_or_data_exposure"
        elif pattern.vulnerability_type == VulnerabilityType.XSS:
            return "script_execution_or_encoding_bypass"
        elif pattern.vulnerability_type == VulnerabilityType.CSRF:
            return "unauthorized_action_execution"
        else:
            return "unexpected_behavior"

    def _generate_success_indicators(self, pattern: AttackPattern) -> list[str]:
        """Generate success indicators for the attack"""
        if pattern.vulnerability_type == VulnerabilityType.SQL_INJECTION:
            return ["sql_error", "data_exposure", "time_delay", "union_success"]
        elif pattern.vulnerability_type == VulnerabilityType.XSS:
            return ["script_execution", "alert_triggered", "dom_manipulation"]
        elif pattern.vulnerability_type == VulnerabilityType.CSRF:
            return ["action_executed", "state_changed", "unauthorized_access"]
        else:
            return ["unexpected_response", "error_message", "behavior_change"]

    def _generate_failure_indicators(self, pattern: AttackPattern) -> list[str]:
        """Generate failure indicators for the attack"""
        if pattern.vulnerability_type == VulnerabilityType.SQL_INJECTION:
            return ["input_validation", "parameterized_query", "sql_escaping"]
        elif pattern.vulnerability_type == VulnerabilityType.XSS:
            return ["output_encoding", "csp_header", "input_sanitization"]
        elif pattern.vulnerability_type == VulnerabilityType.CSRF:
            return ["csrf_token", "referer_check", "same_origin_policy"]
        else:
            return ["input_validation", "error_handling", "security_headers"]

    def _assess_attack_risk(self, pattern: AttackPattern, payload: str) -> RiskLevel:
        """Assess risk level of the attack"""
        # Simple risk assessment based on pattern and payload
        if pattern.vulnerability_type in [
            VulnerabilityType.SQL_INJECTION,
            VulnerabilityType.CODE_INJECTION,
        ]:
            return RiskLevel.HIGH
        elif pattern.vulnerability_type in [
            VulnerabilityType.XSS,
            VulnerabilityType.CSRF,
        ]:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    async def _apply_ai_adaptation(
        self, attacks: list[GeneratedAttack], context: AttackContext
    ) -> list[GeneratedAttack]:
        """Apply AI-powered adaptation to attacks"""
        adapted_attacks = []

        try:
            # Simple adaptation based on previous attack results
            for attack in attacks:
                if context.previous_attacks:
                    # Analyze previous attack results
                    similar_attacks = [
                        a
                        for a in context.previous_attacks
                        if a.get("pattern_id") == attack.pattern_id
                    ]

                    if similar_attacks:
                        success_rate = sum(
                            1 for a in similar_attacks if a.get("success", False)
                        ) / len(similar_attacks)

                        if success_rate < 0.3:  # Low success rate, need adaptation
                            # Create adapted version
                            adapted_attack = GeneratedAttack(
                                attack_id=f"{attack.attack_id}_adapted",
                                pattern_id=attack.pattern_id,
                                payload=self._adapt_payload(
                                    attack.payload, similar_attacks
                                ),
                                attack_vector=attack.attack_vector,
                                target_parameter=attack.target_parameter,
                                expected_response=attack.expected_response,
                                success_indicators=attack.success_indicators,
                                failure_indicators=attack.failure_indicators,
                                risk_level=attack.risk_level,
                                confidence=attack.confidence
                                * 0.8,  # Slightly lower confidence
                                adaptation_strategy="payload_modification",
                            )
                            adapted_attacks.append(adapted_attack)

            logger.info(f"✅ Applied AI adaptation to {len(adapted_attacks)} attacks")

        except Exception as e:
            logger.error(f"❌ AI adaptation failed: {e}")

        return adapted_attacks

    def _adapt_payload(
        self, original_payload: str, previous_results: list[dict[str, Any]]
    ) -> str:
        """Adapt payload based on previous results"""
        # Simple payload adaptation logic
        adapted_payload = original_payload

        # Check what defenses were triggered
        triggered_defenses = []
        for result in previous_results:
            triggered_defenses.extend(result.get("defenses_triggered", []))

        # Adapt based on common defenses
        if "input_validation" in triggered_defenses:
            # Try to bypass input validation
            adapted_payload = adapted_payload.replace("'", "\\'")
            adapted_payload = adapted_payload.replace('"', '\\"')

        if "sql_escaping" in triggered_defenses:
            # Try different SQL injection techniques
            adapted_payload = adapted_payload.replace("'", "''")

        return adapted_payload

    async def _store_attack_generation_experience(
        self, attacks: list[GeneratedAttack], context: AttackContext
    ):
        """Store attack generation experience in memory"""
        if not self.memory_manager:
            return

        try:
            # Create experience content
            experience_content = {
                "type": "attack_generation",
                "timestamp": time.time(),
                "context": asdict(context),
                "attacks_generated": len(attacks),
                "patterns_used": list({attack.pattern_id for attack in attacks}),
                "success_indicators": list(
                    {
                        indicator
                        for attack in attacks
                        for indicator in attack.success_indicators
                    }
                ),
            }

            # Store in memory
            memory_id = self.memory_manager.store(
                content=json.dumps(experience_content),
                importance=0.7,  # High importance for security learning
                tags=["red_team", "attack_generation", "security", "learning"],
            )

            logger.info(f"✅ Stored attack generation experience: {memory_id}")

        except Exception as e:
            logger.error(f"❌ Failed to store attack generation experience: {e}")

    async def execute_attack_campaign(
        self, attacks: list[GeneratedAttack], target_config: dict[str, Any]
    ) -> list[AttackResult]:
        """
        Execute a campaign of attacks safely in sandbox

        Args:
            attacks: List of attacks to execute
            target_config: Target configuration

        Returns:
            List of attack results
        """
        logger.info(f"🎯 Executing attack campaign with {len(attacks)} attacks...")

        results = []

        try:
            # Safety checks
            if not self._validate_attack_campaign_safety(attacks, target_config):
                logger.error("❌ Attack campaign failed safety validation")
                return results

            # Execute attacks in sandbox if available
            if self.sandbox_controller:
                results = await self._execute_attacks_in_sandbox(attacks, target_config)
            elif self.attack_simulator:
                results = await self._execute_attacks_with_simulator(
                    attacks, target_config
                )
            else:
                logger.warning(
                    "⚠️ No execution environment available, using mock execution"
                )
                results = await self._execute_attacks_mock(attacks, target_config)

            # Store results in experience memory
            if self.memory_manager:
                await self._store_attack_results(results)

            # Update metrics
            self._update_metrics(results)

            logger.info(f"✅ Attack campaign completed: {len(results)} results")

        except Exception as e:
            logger.error(f"❌ Attack campaign execution failed: {e}")

        return results

    def _validate_attack_campaign_safety(
        self, attacks: list[GeneratedAttack], target_config: dict[str, Any]
    ) -> bool:
        """Validate attack campaign safety"""
        try:
            # Check if sandbox-only mode is enforced
            if self.config["safety"]["sandbox_only"]:
                if not target_config.get("use_sandbox", True):
                    logger.error(
                        "❌ Sandbox-only mode enforced but target not in sandbox"
                    )
                    return False

            # Check for real targets
            if self.config["safety"]["no_real_targets"]:
                if target_config.get("use_real_data", False):
                    logger.error("❌ Real targets not allowed in safety mode")
                    return False

            # Check attack count
            if len(attacks) > self.config["safety"]["max_concurrent_attacks"]:
                logger.error(
                    f"❌ Too many attacks: {len(attacks)} > {self.config['safety']['max_concurrent_attacks']}"
                )
                return False

            # Check attack duration
            max_duration = self.config["safety"]["max_attack_duration"]
            estimated_duration = len(attacks) * 10  # 10 seconds per attack estimate
            if estimated_duration > max_duration:
                logger.error(
                    f"❌ Estimated duration too long: {estimated_duration}s > {max_duration}s"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"❌ Safety validation failed: {e}")
            return False

    async def _execute_attacks_in_sandbox(
        self, attacks: list[GeneratedAttack], target_config: dict[str, Any]
    ) -> list[AttackResult]:
        """Execute attacks in sandbox environment"""
        results = []

        try:
            # Create sandbox for attack execution
            sandbox = await self.sandbox_controller.create_sandbox(
                name="red_team_attack_campaign",
                sandbox_type=SandboxType.SECURITY_TEST,
                image="python:3.9-slim",
            )

            # Execute each attack
            for attack in attacks:
                result = await self._execute_single_attack_in_sandbox(
                    attack, sandbox, target_config
                )
                results.append(result)

            # Clean up sandbox
            await self.sandbox_controller.destroy_sandbox(sandbox.config.sandbox_id)

        except Exception as e:
            logger.error(f"❌ Sandbox attack execution failed: {e}")

        return results

    async def _execute_single_attack_in_sandbox(
        self, attack: GeneratedAttack, sandbox, target_config: dict[str, Any]
    ) -> AttackResult:
        """Execute a single attack in sandbox"""
        start_time = time.time()

        try:
            # Create attack script
            attack_script = self._create_attack_script(attack, target_config)

            # Execute in sandbox
            result = await self.sandbox_controller.execute_in_sandbox(
                sandbox.config.sandbox_id, ["python", "-c", attack_script]
            )

            # Analyze result
            success = self._analyze_attack_result(attack, result)

            # Create attack result
            attack_result = AttackResult(
                attack_id=attack.attack_id,
                success=success,
                response_code=result["exit_code"],
                response_body=result["stdout"],
                response_time=time.time() - start_time,
                vulnerabilities_detected=self._extract_vulnerabilities(attack, result),
                defenses_triggered=self._extract_defenses(attack, result),
                adaptation_applied=attack.adaptation_strategy is not None,
                learning_insights=self._extract_learning_insights(attack, result),
                risk_assessment=self._assess_attack_risk_result(attack, result),
            )

            return attack_result

        except Exception as e:
            logger.error(f"❌ Single attack execution failed: {e}")
            return AttackResult(
                attack_id=attack.attack_id,
                success=False,
                response_code=-1,
                response_body=str(e),
                response_time=time.time() - start_time,
                vulnerabilities_detected=[],
                defenses_triggered=[],
                adaptation_applied=False,
                learning_insights=[f"Execution error: {e}"],
                risk_assessment={"error": str(e)},
            )

    def _create_attack_script(
        self, attack: GeneratedAttack, target_config: dict[str, Any]
    ) -> str:
        """Create attack script for sandbox execution"""
        script = f"""
import requests

# Attack configuration
attack_payload = {json.dumps(attack.payload)}
target_url = {json.dumps(target_config.get('url', 'http://localhost:8080'))}
target_param = {json.dumps(attack.target_parameter)}

# Execute attack
try:
    response = requests.post(
        target_url,
        data={{target_param: attack_payload}},
        timeout=10
    )
    print(f"Response Code: {{response.status_code}}")
    print(f"Response Body: {{response.text[:500]}}")
except Exception as e:
    print(f"Attack failed: {{e}}")
"""
        return script

    def _analyze_attack_result(
        self, attack: GeneratedAttack, result: dict[str, Any]
    ) -> bool:
        """Analyze if attack was successful"""
        if result["exit_code"] != 0:
            return False

        response_body = result["stdout"].lower()

        # Check for success indicators
        for indicator in attack.success_indicators:
            if indicator.lower() in response_body:
                return True

        # Check for failure indicators
        for indicator in attack.failure_indicators:
            if indicator.lower() in response_body:
                return False

        return False

    def _extract_vulnerabilities(
        self, attack: GeneratedAttack, result: dict[str, Any]
    ) -> list[str]:
        """Extract detected vulnerabilities from attack result"""
        vulnerabilities = []
        response_body = result["stdout"].lower()

        for indicator in attack.success_indicators:
            if indicator.lower() in response_body:
                vulnerabilities.append(indicator)

        return vulnerabilities

    def _extract_defenses(
        self, attack: GeneratedAttack, result: dict[str, Any]
    ) -> list[str]:
        """Extract triggered defenses from attack result"""
        defenses = []
        response_body = result["stdout"].lower()

        for indicator in attack.failure_indicators:
            if indicator.lower() in response_body:
                defenses.append(indicator)

        return defenses

    def _extract_learning_insights(
        self, attack: GeneratedAttack, result: dict[str, Any]
    ) -> list[str]:
        """Extract learning insights from attack result"""
        insights = []

        if result["exit_code"] == 0:
            insights.append("Attack executed successfully")
        else:
            insights.append("Attack execution failed")

        if attack.adaptation_strategy:
            insights.append(
                f"Adaptation strategy applied: {attack.adaptation_strategy}"
            )

        return insights

    def _assess_attack_risk_result(
        self, attack: GeneratedAttack, result: dict[str, Any]
    ) -> dict[str, Any]:
        """Assess risk of attack result"""
        return {
            "attack_risk": attack.risk_level.value,
            "execution_success": result["exit_code"] == 0,
            "vulnerabilities_exposed": len(
                self._extract_vulnerabilities(attack, result)
            ),
            "defenses_bypassed": len(self._extract_defenses(attack, result)) == 0,
        }

    async def _execute_attacks_with_simulator(
        self, attacks: list[GeneratedAttack], target_config: dict[str, Any]
    ) -> list[AttackResult]:
        """Execute attacks using attack simulator"""
        results = []

        try:
            for attack in attacks:
                # Convert to simulator format
                scenario_id = self._map_attack_to_scenario(attack)

                # Run simulation
                simulation_result = self.attack_simulator.run_simulation(
                    scenario_id=scenario_id, target_config=target_config
                )

                # Convert to attack result
                attack_result = AttackResult(
                    attack_id=attack.attack_id,
                    success=simulation_result.success,
                    response_code=200 if simulation_result.success else 400,
                    response_body=json.dumps(simulation_result.impact_assessment),
                    response_time=simulation_result.duration,
                    vulnerabilities_detected=[
                        v.get("type", "unknown")
                        for v in simulation_result.vulnerabilities_found
                    ],
                    defenses_triggered=[
                        d.get("type", "unknown")
                        for d in simulation_result.defenses_triggered
                    ],
                    adaptation_applied=attack.adaptation_strategy is not None,
                    learning_insights=simulation_result.recommendations,
                    risk_assessment={"risk_score": simulation_result.risk_score},
                )

                results.append(attack_result)

        except Exception as e:
            logger.error(f"❌ Simulator attack execution failed: {e}")

        return results

    def _map_attack_to_scenario(self, attack: GeneratedAttack) -> str:
        """Map attack to simulator scenario"""
        pattern = self.attack_patterns.get(attack.pattern_id)
        if not pattern:
            return "OWASP_SQL_INJECTION"  # Default

        if pattern.vulnerability_type == VulnerabilityType.SQL_INJECTION:
            return "OWASP_SQL_INJECTION"
        elif pattern.vulnerability_type == VulnerabilityType.XSS:
            return "OWASP_XSS"
        elif pattern.vulnerability_type == VulnerabilityType.CSRF:
            return "OWASP_CSRF"
        else:
            return "OWASP_SQL_INJECTION"  # Default

    async def _execute_attacks_mock(
        self, attacks: list[GeneratedAttack], target_config: dict[str, Any]
    ) -> list[AttackResult]:
        """Execute attacks in mock mode for testing"""
        results = []

        for attack in attacks:
            # Mock execution
            mock_result = AttackResult(
                attack_id=attack.attack_id,
                success=True,  # Mock success
                response_code=200,
                response_body="Mock response",
                response_time=0.1,
                vulnerabilities_detected=["mock_vulnerability"],
                defenses_triggered=[],
                adaptation_applied=attack.adaptation_strategy is not None,
                learning_insights=["Mock execution completed"],
                risk_assessment={"mock": True},
            )
            results.append(mock_result)

        return results

    async def _store_attack_results(self, results: list[AttackResult]):
        """Store attack results in experience memory"""
        if not self.memory_manager:
            return

        try:
            for result in results:
                experience_content = {
                    "type": "attack_result",
                    "timestamp": time.time(),
                    "attack_id": result.attack_id,
                    "success": result.success,
                    "vulnerabilities_detected": result.vulnerabilities_detected,
                    "defenses_triggered": result.defenses_triggered,
                    "learning_insights": result.learning_insights,
                    "risk_assessment": result.risk_assessment,
                }

                self.memory_manager.store(
                    content=json.dumps(experience_content),
                    importance=0.8 if result.success else 0.6,
                    tags=["red_team", "attack_result", "security", "learning"],
                )

            logger.info(f"✅ Stored {len(results)} attack results in memory")

        except Exception as e:
            logger.error(f"❌ Failed to store attack results: {e}")

    def _update_metrics(self, results: list[AttackResult]):
        """Update performance metrics"""
        self.metrics["total_attacks"] += len(results)
        self.metrics["successful_attacks"] += sum(1 for r in results if r.success)
        self.metrics["vulnerabilities_found"] += sum(
            len(r.vulnerabilities_detected) for r in results
        )
        self.metrics["adaptations_made"] += sum(
            1 for r in results if r.adaptation_applied
        )

    def get_attack_statistics(self) -> dict[str, Any]:
        """Get attack statistics and metrics"""
        return {
            "metrics": self.metrics,
            "patterns_available": len(self.attack_patterns),
            "attack_history_count": len(self.attack_history),
            "learning_insights_count": len(self.learning_insights),
            "success_rate": (
                self.metrics["successful_attacks"] / self.metrics["total_attacks"]
                if self.metrics["total_attacks"] > 0
                else 0
            ),
        }

    def get_learning_insights(self) -> list[dict[str, Any]]:
        """Get learning insights from attack campaigns"""
        return self.learning_insights

    def cleanup(self):
        """Clean up resources"""
        try:
            if self.sandbox_controller:
                asyncio.run(self.sandbox_controller.cleanup_all())
            logger.info("✅ RedTeamEngine cleanup completed")
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()
