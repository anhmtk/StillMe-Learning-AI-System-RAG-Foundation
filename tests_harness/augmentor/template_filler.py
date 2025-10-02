#!/usr/bin/env python3
"""
Template Filler Module - Sinh biến thể từ template slots
Tạo nhiều biến thể bằng cách thay thế các placeholder trong template
"""

import asyncio
import json
import logging
import os
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

# Add stillme_core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from stillme_core.modules.api_provider_manager import UnifiedAPIManager
except ImportError:
    print("Warning: UnifiedAPIManager not available, using mock")
    UnifiedAPIManager = None


@dataclass
class TemplateConfig:
    """Cấu hình cho template filler"""

    model: str = "gemma2:2b"  # Local model mặc định
    num_variants_per_template: int = 10  # Số biến thể cho mỗi template
    temperature: float = 0.8  # Độ sáng tạo
    max_tokens: int = 150
    use_ai_generation: bool = True  # Sử dụng AI để tạo variants
    use_predefined_slots: bool = True  # Sử dụng slots có sẵn


@dataclass
class TemplateSlot:
    """Định nghĩa một slot trong template"""

    name: str
    category: str  # role, action, emotion, topic, etc.
    values: list[str]
    description: str = ""


@dataclass
class Template:
    """Template với các slots"""

    name: str
    template: str  # Template string với [SLOT_NAME] placeholders
    slots: list[TemplateSlot]
    description: str = ""
    category: str = "general"


@dataclass
class TemplateResult:
    """Kết quả từ template filling"""

    template_name: str
    original_template: str
    variants: list[str]
    slot_combinations: list[dict[str, str]]
    success: bool
    error: Optional[str] = None
    metadata: dict[str, Any] = None


class TemplateFiller:
    """Template filler sử dụng predefined slots và AI generation"""

    def __init__(self, config: TemplateConfig = None):
        self.config = config or TemplateConfig()
        self.logger = logging.getLogger(__name__)

        # Initialize API manager
        if UnifiedAPIManager:
            try:
                self.api_manager = UnifiedAPIManager()
            except Exception as e:
                self.logger.warning(f"Failed to initialize UnifiedAPIManager: {e}")
                self.api_manager = None
        else:
            self.api_manager = None

        # Predefined slots
        self.predefined_slots = self._create_predefined_slots()

        # Common templates
        self.common_templates = self._create_common_templates()

    def _create_predefined_slots(self) -> dict[str, list[str]]:
        """Tạo các slots có sẵn"""
        return {
            "ROLE": [
                "anh",
                "chị",
                "em",
                "bác",
                "cô",
                "chú",
                "thầy",
                "cô giáo",
                "bạn",
                "mình",
                "tôi",
                "bạn trai",
                "bạn gái",
                "chồng",
                "vợ",
                "con",
                "cha",
                "mẹ",
                "ông",
                "bà",
                "anh trai",
                "chị gái",
            ],
            "ACTION": [
                "làm gì",
                "đi đâu",
                "ăn gì",
                "mặc gì",
                "học gì",
                "làm việc gì",
                "chơi gì",
                "xem gì",
                "nghe gì",
                "đọc gì",
                "viết gì",
                "nói gì",
                "nghĩ gì",
                "cảm thấy thế nào",
                "thích gì",
                "ghét gì",
            ],
            "EMOTION": [
                "vui",
                "buồn",
                "tức giận",
                "lo lắng",
                "hạnh phúc",
                "thất vọng",
                "ngạc nhiên",
                "sợ hãi",
                "tự hào",
                "xấu hổ",
                "ghen tị",
                "biết ơn",
                "yêu thương",
                "ghét bỏ",
                "thích thú",
                "chán nản",
            ],
            "TOPIC": [
                "công việc",
                "học tập",
                "gia đình",
                "bạn bè",
                "tình yêu",
                "sức khỏe",
                "du lịch",
                "ăn uống",
                "thể thao",
                "âm nhạc",
                "phim ảnh",
                "sách vở",
                "công nghệ",
                "thời trang",
                "làm đẹp",
                "đầu tư",
                "kinh doanh",
            ],
            "TIME": [
                "hôm nay",
                "hôm qua",
                "ngày mai",
                "tuần này",
                "tuần trước",
                "tuần sau",
                "tháng này",
                "tháng trước",
                "tháng sau",
                "năm nay",
                "năm trước",
                "năm sau",
                "sáng nay",
                "chiều nay",
                "tối nay",
                "đêm qua",
                "sáng mai",
            ],
            "PLACE": [
                "nhà",
                "trường",
                "công ty",
                "quán cà phê",
                "nhà hàng",
                "bệnh viện",
                "siêu thị",
                "công viên",
                "bãi biển",
                "núi",
                "rừng",
                "thành phố",
                "làng quê",
                "sân bay",
                "ga tàu",
                "bến xe",
                "thư viện",
                "bảo tàng",
            ],
            "GREETING": [
                "xin chào",
                "chào",
                "hi",
                "hello",
                "chào bạn",
                "chào anh",
                "chào chị",
                "chào em",
                "chào bác",
                "chào cô",
                "chào thầy",
                "chào cô giáo",
                "chào buổi sáng",
                "chào buổi chiều",
                "chào buổi tối",
            ],
            "QUESTION": [
                "thế nào",
                "ra sao",
                "có gì mới",
                "có khỏe không",
                "có vui không",
                "có buồn không",
                "có lo lắng gì không",
                "có cần giúp gì không",
                "có muốn gì không",
                "có thích gì không",
                "có ghét gì không",
            ],
        }

    def _create_common_templates(self) -> list[Template]:
        """Tạo các template phổ biến"""
        return [
            Template(
                name="greeting_question",
                template="[GREETING] [ROLE], [TIME] [QUESTION]?",
                slots=[
                    TemplateSlot(
                        "GREETING", "greeting", self.predefined_slots["GREETING"]
                    ),
                    TemplateSlot("ROLE", "role", self.predefined_slots["ROLE"]),
                    TemplateSlot("TIME", "time", self.predefined_slots["TIME"]),
                    TemplateSlot(
                        "QUESTION", "question", self.predefined_slots["QUESTION"]
                    ),
                ],
                description="Template chào hỏi và hỏi thăm",
                category="greeting",
            ),
            Template(
                name="action_inquiry",
                template="[ROLE] [TIME] [ACTION] ở [PLACE]?",
                slots=[
                    TemplateSlot("ROLE", "role", self.predefined_slots["ROLE"]),
                    TemplateSlot("TIME", "time", self.predefined_slots["TIME"]),
                    TemplateSlot("ACTION", "action", self.predefined_slots["ACTION"]),
                    TemplateSlot("PLACE", "place", self.predefined_slots["PLACE"]),
                ],
                description="Template hỏi về hành động",
                category="inquiry",
            ),
            Template(
                name="emotion_sharing",
                template="[TIME] tôi cảm thấy [EMOTION] về [TOPIC].",
                slots=[
                    TemplateSlot("TIME", "time", self.predefined_slots["TIME"]),
                    TemplateSlot(
                        "EMOTION", "emotion", self.predefined_slots["EMOTION"]
                    ),
                    TemplateSlot("TOPIC", "topic", self.predefined_slots["TOPIC"]),
                ],
                description="Template chia sẻ cảm xúc",
                category="emotion",
            ),
            Template(
                name="help_offer",
                template="Tôi có thể giúp [ROLE] [ACTION] về [TOPIC] không?",
                slots=[
                    TemplateSlot("ROLE", "role", self.predefined_slots["ROLE"]),
                    TemplateSlot("ACTION", "action", self.predefined_slots["ACTION"]),
                    TemplateSlot("TOPIC", "topic", self.predefined_slots["TOPIC"]),
                ],
                description="Template đề nghị giúp đỡ",
                category="help",
            ),
            Template(
                name="opinion_request",
                template="[ROLE] nghĩ thế nào về [TOPIC] [TIME]?",
                slots=[
                    TemplateSlot("ROLE", "role", self.predefined_slots["ROLE"]),
                    TemplateSlot("TOPIC", "topic", self.predefined_slots["TOPIC"]),
                    TemplateSlot("TIME", "time", self.predefined_slots["TIME"]),
                ],
                description="Template xin ý kiến",
                category="opinion",
            ),
        ]

    def _extract_slots_from_template(self, template: str) -> list[str]:
        """Trích xuất các slot từ template string"""
        pattern = r"\[([A-Z_]+)\]"
        return re.findall(pattern, template)

    def _generate_slot_combinations(
        self, template: Template, num_combinations: int
    ) -> list[dict[str, str]]:
        """Tạo các combination của slots"""
        combinations = []

        for _ in range(num_combinations):
            combination = {}
            for slot in template.slots:
                if slot.name in self.predefined_slots:
                    combination[slot.name] = random.choice(
                        self.predefined_slots[slot.name]
                    )
                else:
                    combination[slot.name] = random.choice(slot.values)
            combinations.append(combination)

        # Remove duplicates
        unique_combinations = []
        seen = set()
        for combo in combinations:
            combo_str = str(sorted(combo.items()))
            if combo_str not in seen:
                seen.add(combo_str)
                unique_combinations.append(combo)

        return unique_combinations

    async def _generate_ai_variants(
        self, template: Template, num_variants: int
    ) -> list[str]:
        """Sử dụng AI để tạo variants"""
        if not self.api_manager or not self.config.use_ai_generation:
            return []

        try:
            prompt = f"""Tạo {num_variants} biến thể khác nhau cho template sau:

Template: "{template.template}"

Các slot có thể thay thế:
{chr(10).join([f"- {slot.name}: {', '.join(slot.values[:5])}..." for slot in template.slots])}

Yêu cầu:
- Giữ nguyên cấu trúc template
- Thay thế các [SLOT_NAME] bằng giá trị phù hợp
- Tạo ra các biến thể đa dạng và tự nhiên
- Mỗi biến thể trên một dòng riêng

Biến thể:"""

            response = self.api_manager.get_response(
                prompt=prompt, model=self.config.model
            )

            # Parse response
            variants = []
            for line in response.strip().split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    # Remove numbering if present
                    if line.startswith(("1.", "2.", "3.", "4.", "5.", "-", "*")):
                        line = line.split(".", 1)[-1].strip()
                        line = line.lstrip("-* ").strip()

                    if line:
                        variants.append(line)

            return variants[:num_variants]

        except Exception as e:
            self.logger.warning(f"AI variant generation failed: {e}")
            return []

    def _fill_template(self, template: str, combination: dict[str, str]) -> str:
        """Điền template với combination"""
        result = template
        for slot_name, value in combination.items():
            result = result.replace(f"[{slot_name}]", value)
        return result

    async def fill_template(self, template: Template) -> TemplateResult:
        """Điền template và tạo variants"""
        try:
            variants = []
            slot_combinations = []

            # Generate slot combinations
            combinations = self._generate_slot_combinations(
                template, self.config.num_variants_per_template
            )

            # Fill template with combinations
            for combination in combinations:
                variant = self._fill_template(template.template, combination)
                variants.append(variant)
                slot_combinations.append(combination)

            # Generate AI variants if enabled
            if self.config.use_ai_generation:
                ai_variants = await self._generate_ai_variants(
                    template, self.config.num_variants_per_template // 2
                )
                variants.extend(ai_variants)
                # Add empty combinations for AI variants
                slot_combinations.extend([{}] * len(ai_variants))

            # Remove duplicates
            unique_variants = []
            unique_combinations = []
            seen = set()

            for variant, combo in zip(variants, slot_combinations):
                if variant not in seen:
                    seen.add(variant)
                    unique_variants.append(variant)
                    unique_combinations.append(combo)

            return TemplateResult(
                template_name=template.name,
                original_template=template.template,
                variants=unique_variants,
                slot_combinations=unique_combinations,
                success=True,
                metadata={
                    "template_category": template.category,
                    "num_slots": len(template.slots),
                    "ai_generated": self.config.use_ai_generation,
                },
            )

        except Exception as e:
            self.logger.error(f"Template filling failed: {e}")
            return TemplateResult(
                template_name=template.name,
                original_template=template.template,
                variants=[],
                slot_combinations=[],
                success=False,
                error=str(e),
            )

    async def fill_templates_batch(
        self, templates: list[Template]
    ) -> list[TemplateResult]:
        """Điền nhiều templates cùng lúc"""
        tasks = [self.fill_template(template) for template in templates]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    TemplateResult(
                        template_name=templates[i].name,
                        original_template=templates[i].template,
                        variants=[],
                        slot_combinations=[],
                        success=False,
                        error=str(result),
                    )
                )
            else:
                processed_results.append(result)

        return processed_results


class TemplateFillerAugmentor:
    """Augmentor chính cho template filling"""

    def __init__(self, config: TemplateConfig = None):
        self.template_filler = TemplateFiller(config)
        self.logger = logging.getLogger(__name__)

    async def augment_from_templates(
        self, output_file: str, templates: list[Template] = None
    ) -> dict[str, Any]:
        """Augment từ templates"""
        if templates is None:
            templates = self.template_filler.common_templates

        self.logger.info(f"Filling {len(templates)} templates")

        # Fill templates
        results = await self.template_filler.fill_templates_batch(templates)

        # Save results
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for result in results:
                if result.success:
                    for variant in result.variants:
                        output_data = {
                            "variant": variant,
                            "method": "template_fill",
                            "template_name": result.template_name,
                            "original_template": result.original_template,
                            "metadata": result.metadata,
                        }
                        f.write(json.dumps(output_data, ensure_ascii=False) + "\n")

        # Generate statistics
        stats = {
            "total_templates": len(templates),
            "total_outputs": sum(len(r.variants) for r in results if r.success),
            "success_rate": sum(1 for r in results if r.success) / len(results),
            "templates_by_category": {},
            "config": {
                "num_variants_per_template": self.template_filler.config.num_variants_per_template,
                "use_ai_generation": self.template_filler.config.use_ai_generation,
            },
        }

        # Count by category
        for result in results:
            if result.success and result.metadata:
                category = result.metadata.get("template_category", "unknown")
                stats["templates_by_category"][category] = (
                    stats["templates_by_category"].get(category, 0) + 1
                )

        self.logger.info(f"Template filling completed: {stats}")
        return stats

    async def augment_from_custom_templates(
        self, template_file: str, output_file: str
    ) -> dict[str, Any]:
        """Augment từ custom template file"""
        template_path = Path(template_file)
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_file}")

        # Load custom templates
        templates = []
        with open(template_path, encoding="utf-8") as f:
            data = json.load(f)
            for template_data in data.get("templates", []):
                slots = []
                for slot_data in template_data.get("slots", []):
                    slot = TemplateSlot(
                        name=slot_data["name"],
                        category=slot_data.get("category", "general"),
                        values=slot_data["values"],
                        description=slot_data.get("description", ""),
                    )
                    slots.append(slot)

                template = Template(
                    name=template_data["name"],
                    template=template_data["template"],
                    slots=slots,
                    description=template_data.get("description", ""),
                    category=template_data.get("category", "general"),
                )
                templates.append(template)

        return await self.augment_from_templates(output_file, templates)


async def main():
    """Demo function"""
    config = TemplateConfig(num_variants_per_template=5, use_ai_generation=True)

    augmentor = TemplateFillerAugmentor(config)

    # Test with common templates
    results = await augmentor.augment_from_templates("demo_template_output.jsonl")

    print(
        f"Generated {results['total_outputs']} variants from {results['total_templates']} templates"
    )
    print(f"Success rate: {results['success_rate']:.2%}")
    print("Templates by category:", results["templates_by_category"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
