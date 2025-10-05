from typing import NotRequired, TypedDict


class ContainerSecurityContext(TypedDict, total=False):
    runAsUser: int
    runAsGroup: int
    runAsNonRoot: bool
    allowPrivilegeEscalation: bool
    readOnlyRootFilesystem: bool
    capabilities: NotRequired[dict[str, list[str]]]


class ContainerSpec(TypedDict, total=False):
    name: str
    image: str
    securityContext: NotRequired[ContainerSecurityContext]


class PodSpec(TypedDict, total=False):
    containers: list[ContainerSpec]


class PodTemplateSpec(TypedDict, total=False):
    spec: PodSpec


# Runtime Protection Types
class ActionSpec(TypedDict, total=False):
    name: str
    parameters: dict[str, str]


class PolicyRule(TypedDict, total=False):
    id: str
    description: str
    severity: str  # e.g., "low", "medium", "high"
    actions: list[ActionSpec]


class RuntimePolicy(TypedDict, total=False):
    rules: list[PolicyRule]
    enforce: bool


# Threat Intelligence Types
class ThreatIndicator(TypedDict, total=False):
    id: str
    type: str  # e.g., "ip", "domain", "hash"
    value: str
    severity: str  # "low", "medium", "high", "critical"
    source: str  # e.g., "crowdstrike", "internal"
    confidence: int  # 0–100


class ThreatFeed(TypedDict, total=False):
    indicators: list[ThreatIndicator]
    updated_at: str  # ISO datetime string


# Validation System Types
class ErrorDetail(TypedDict, total=False):
    file: str
    line: int
    column: int
    message: str
    rule: str
    severity: str


class ValidationResult(TypedDict, total=False):
    before_errors: int
    after_errors: int
    errors_fixed: int
    critical_errors: int
    warnings: int
    style_suggestions: int
    success: bool
    evidence_files: list[str]


class ValidationData(TypedDict, total=False):
    pyright_errors: int
    ruff_errors: int
    total_files: int
    timestamp: float
