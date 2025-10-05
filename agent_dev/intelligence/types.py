from typing import Literal, NotRequired, TypedDict


class Insight(TypedDict, total=False):
    id: str
    text: str
    source: str
    confidence: float   # 0.0 - 1.0
    tags: list[str]

class ReasoningStep(TypedDict, total=False):
    step_id: str
    description: str
    input_data: dict[str, str]
    output_data: dict[str, str]
    confidence: float

class ScoreResult(TypedDict, total=False):
    metric: str
    value: float
    threshold: float
    status: Literal["pass", "fail", "warn"]
    details: NotRequired[dict[str, str]]

class ASTNode(TypedDict, total=False):
    node_type: str
    line_number: int
    complexity: int
    children: list[str]

class FileAnalysis(TypedDict, total=False):
    file_path: str
    file_hash: str
    file_size: int
    ast_nodes: list[ASTNode]
    complexity_score: float
    insights: list[Insight]
