#!/usr/bin/env python3
"""
Cost Calculator - Tính toán token và chi phí cho test harness
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ModelCost:
    """Chi phí cho một model"""
    model_name: str
    input_cost_per_1k: float  # USD per 1K tokens
    output_cost_per_1k: float  # USD per 1K tokens
    max_tokens: int = 4096

@dataclass
class TokenUsage:
    """Token usage cho một request"""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model_used: str
    cost_usd: float

@dataclass
class CostSummary:
    """Tổng kết chi phí"""
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_cost_usd: float
    cost_by_model: dict[str, float]
    cost_by_method: dict[str, float]

class CostCalculator:
    """Calculator cho token và chi phí"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Model costs (USD per 1K tokens)
        self.model_costs = {
            "gpt-3.5-turbo": ModelCost("gpt-3.5-turbo", 0.0015, 0.002, 4096),
            "gpt-4": ModelCost("gpt-4", 0.03, 0.06, 8192),
            "gpt-4-turbo": ModelCost("gpt-4-turbo", 0.01, 0.03, 128000),
            "claude-3-sonnet": ModelCost("claude-3-sonnet", 0.003, 0.015, 200000),
            "claude-3-opus": ModelCost("claude-3-opus", 0.015, 0.075, 200000),
            "gemini-pro": ModelCost("gemini-pro", 0.0005, 0.0015, 30720),
            "deepseek-chat": ModelCost("deepseek-chat", 0.0014, 0.0028, 4096),
            "gemma2:2b": ModelCost("gemma2:2b", 0.0, 0.0, 8192),  # Local model
            "deepseek-coder:6.7b": ModelCost("deepseek-coder:6.7b", 0.0, 0.0, 8192),  # Local model
        }

    def estimate_tokens(self, text: str) -> int:
        """Ước tính số token từ text"""
        # Simple estimation: ~4 characters per token for English, ~2 for Vietnamese
        if any(ord(char) > 127 for char in text):
            # Vietnamese or other non-ASCII
            return len(text) // 2
        else:
            # English
            return len(text) // 4

    def calculate_cost(self, input_text: str, output_text: str, model: str) -> TokenUsage:
        """Tính chi phí cho một request"""

        input_tokens = self.estimate_tokens(input_text)
        output_tokens = self.estimate_tokens(output_text)
        total_tokens = input_tokens + output_tokens

        # Get model cost
        model_cost = self.model_costs.get(model)
        if not model_cost:
            self.logger.warning(f"Unknown model: {model}, using default cost")
            model_cost = ModelCost(model, 0.001, 0.002, 4096)

        # Calculate cost
        input_cost = (input_tokens / 1000) * model_cost.input_cost_per_1k
        output_cost = (output_tokens / 1000) * model_cost.output_cost_per_1k
        total_cost = input_cost + output_cost

        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            model_used=model,
            cost_usd=total_cost
        )

    def analyze_augmentation_file(self, file_path: str) -> CostSummary:
        """Phân tích chi phí từ file augmentation"""

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        total_requests = 0
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost_usd = 0.0
        cost_by_model = {}
        cost_by_method = {}

        with open(file_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)

                    # Extract information
                    original = data.get('original', '')
                    variant = data.get('variant', '')
                    method = data.get('method', 'unknown')
                    metadata = data.get('metadata', {})
                    model = metadata.get('generated_by', 'unknown')

                    if original and variant:
                        # Calculate cost for this augmentation
                        usage = self.calculate_cost(original, variant, model)

                        total_requests += 1
                        total_input_tokens += usage.input_tokens
                        total_output_tokens += usage.output_tokens
                        total_cost_usd += usage.cost_usd

                        # Track by model
                        cost_by_model[model] = cost_by_model.get(model, 0.0) + usage.cost_usd

                        # Track by method
                        cost_by_method[method] = cost_by_method.get(method, 0.0) + usage.cost_usd

                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON line: {line}")
                    continue

        return CostSummary(
            total_requests=total_requests,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_tokens=total_input_tokens + total_output_tokens,
            total_cost_usd=total_cost_usd,
            cost_by_model=cost_by_model,
            cost_by_method=cost_by_method
        )

    def analyze_seed_generation(self, seed_file: str) -> CostSummary:
        """Phân tích chi phí từ seed generation"""

        seed_path = Path(seed_file)
        if not seed_path.exists():
            raise FileNotFoundError(f"Seed file not found: {seed_file}")

        total_requests = 0
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost_usd = 0.0
        cost_by_model = {}
        cost_by_method = {"seed_generation": 0.0}

        with open(seed_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)

                    # Extract information
                    text = data.get('text', '')
                    metadata = data.get('metadata', {})
                    model = metadata.get('generated_by', 'unknown')

                    if text:
                        # Estimate prompt length (assume 200 tokens for generation prompt)
                        prompt_tokens = 200
                        output_tokens = self.estimate_tokens(text)

                        # Calculate cost
                        usage = self.calculate_cost("", text, model)
                        usage.input_tokens = prompt_tokens
                        usage.total_tokens = prompt_tokens + output_tokens

                        # Recalculate cost with correct input tokens
                        model_cost = self.model_costs.get(model)
                        if model_cost:
                            input_cost = (prompt_tokens / 1000) * model_cost.input_cost_per_1k
                            output_cost = (output_tokens / 1000) * model_cost.output_cost_per_1k
                            usage.cost_usd = input_cost + output_cost

                        total_requests += 1
                        total_input_tokens += prompt_tokens
                        total_output_tokens += output_tokens
                        total_cost_usd += usage.cost_usd

                        # Track by model
                        cost_by_model[model] = cost_by_model.get(model, 0.0) + usage.cost_usd
                        cost_by_method["seed_generation"] += usage.cost_usd

                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON line: {line}")
                    continue

        return CostSummary(
            total_requests=total_requests,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_tokens=total_input_tokens + total_output_tokens,
            total_cost_usd=total_cost_usd,
            cost_by_model=cost_by_model,
            cost_by_method=cost_by_method
        )

    def generate_cost_report(self, summary: CostSummary, title: str = "Cost Analysis") -> str:
        """Tạo báo cáo chi phí"""

        report = f"""
{'='*60}
{title}
{'='*60}

📊 OVERALL STATISTICS:
  Total Requests: {summary.total_requests:,}
  Total Input Tokens: {summary.total_input_tokens:,}
  Total Output Tokens: {summary.total_output_tokens:,}
  Total Tokens: {summary.total_tokens:,}
  Total Cost: ${summary.total_cost_usd:.4f}

💰 COST BREAKDOWN BY MODEL:
"""

        for model, cost in sorted(summary.cost_by_model.items(), key=lambda x: x[1], reverse=True):
            percentage = (cost / summary.total_cost_usd * 100) if summary.total_cost_usd > 0 else 0
            report += f"  {model}: ${cost:.4f} ({percentage:.1f}%)\n"

        report += "\n🔧 COST BREAKDOWN BY METHOD:\n"
        for method, cost in sorted(summary.cost_by_method.items(), key=lambda x: x[1], reverse=True):
            percentage = (cost / summary.total_cost_usd * 100) if summary.total_cost_usd > 0 else 0
            report += f"  {method}: ${cost:.4f} ({percentage:.1f}%)\n"

        report += f"""
📈 EFFICIENCY METRICS:
  Average Cost per Request: ${summary.total_cost_usd/summary.total_requests:.4f}
  Average Tokens per Request: {summary.total_tokens/summary.total_requests:.1f}
  Cost per 1K Tokens: ${(summary.total_cost_usd/summary.total_tokens*1000):.4f}

💡 OPTIMIZATION SUGGESTIONS:
"""

        if summary.total_cost_usd > 10:
            report += "  - Consider using local models (Gemma, DeepSeek) for augmentation\n"
            report += "  - Reduce number of variants per seed\n"
            report += "  - Use cheaper models for simple tasks\n"

        if any("gpt-4" in model for model in summary.cost_by_model.keys()):
            report += "  - GPT-4 is expensive, consider GPT-3.5-turbo for most tasks\n"

        if summary.total_requests > 1000:
            report += "  - Large dataset detected, consider batch processing\n"

        report += "="*60

        return report

    def save_cost_report(self, summary: CostSummary, output_file: str, title: str = "Cost Analysis"):
        """Lưu báo cáo chi phí"""

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate report
        report = self.generate_cost_report(summary, title)

        # Save text report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

        # Save JSON data
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total_requests": summary.total_requests,
                    "total_input_tokens": summary.total_input_tokens,
                    "total_output_tokens": summary.total_output_tokens,
                    "total_tokens": summary.total_tokens,
                    "total_cost_usd": summary.total_cost_usd,
                    "cost_by_model": summary.cost_by_model,
                    "cost_by_method": summary.cost_by_method
                },
                "model_costs": {name: {
                    "input_cost_per_1k": cost.input_cost_per_1k,
                    "output_cost_per_1k": cost.output_cost_per_1k,
                    "max_tokens": cost.max_tokens
                } for name, cost in self.model_costs.items()}
            }, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Cost report saved to {output_path}")
        self.logger.info(f"Cost data saved to {json_path}")

def main():
    """Main function để test cost calculator"""

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    calculator = CostCalculator()

    # Test với mock data
    mock_file = "datasets/augmented/mock_augmented_combined.jsonl"
    if Path(mock_file).exists():
        print("🔍 Analyzing mock augmentation costs...")
        summary = calculator.analyze_augmentation_file(mock_file)

        # Generate and save report
        calculator.save_cost_report(summary, "reports/mock_cost_analysis.txt", "Mock Augmentation Cost Analysis")

        # Print summary
        print(calculator.generate_cost_report(summary, "Mock Augmentation Cost Analysis"))

    # Test seed generation cost
    seed_file = "datasets/seed/mock_seeds.jsonl"
    if Path(seed_file).exists():
        print("\n🔍 Analyzing seed generation costs...")
        summary = calculator.analyze_seed_generation(seed_file)

        # Generate and save report
        calculator.save_cost_report(summary, "reports/seed_cost_analysis.txt", "Seed Generation Cost Analysis")

        # Print summary
        print(calculator.generate_cost_report(summary, "Seed Generation Cost Analysis"))

if __name__ == "__main__":
    main()
