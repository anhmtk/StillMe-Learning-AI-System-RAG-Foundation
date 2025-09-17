#!/usr/bin/env python3
"""
Paraphraser Module - Tạo biến thể câu bằng local AI models
Sử dụng Gemma, Llama3, DeepSeek để viết lại câu thành nhiều biến thể
"""

import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import sys
import os

# Add stillme_core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from stillme_core.modules.api_provider_manager import UnifiedAPIManager
except ImportError:
    print("Warning: UnifiedAPIManager not available, using mock")
    UnifiedAPIManager = None

@dataclass
class ParaphraseConfig:
    """Cấu hình cho paraphraser"""
    model: str = "gemma2:2b"  # Local model mặc định
    num_variants: int = 5  # Số biến thể tạo ra
    temperature: float = 0.8  # Độ sáng tạo
    max_tokens: int = 200
    preserve_meaning: bool = True  # Giữ nguyên ý nghĩa
    preserve_tone: bool = True  # Giữ nguyên giọng điệu
    preserve_language: bool = True  # Giữ nguyên ngôn ngữ

@dataclass
class ParaphraseResult:
    """Kết quả paraphrase"""
    original: str
    variants: List[str]
    model_used: str
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

class Paraphraser:
    """Paraphraser sử dụng local AI models"""
    
    def __init__(self, config: ParaphraseConfig = None):
        self.config = config or ParaphraseConfig()
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
    
    def _create_paraphrase_prompt(self, text: str) -> str:
        """Tạo prompt cho paraphrase"""
        language = "tiếng Việt" if any(ord(char) > 127 for char in text) else "English"
        
        prompt = f"""Hãy viết lại câu sau thành {self.config.num_variants} biến thể khác nhau trong {language}:

Câu gốc: "{text}"

Yêu cầu:
- Giữ nguyên ý nghĩa chính
- Giữ nguyên giọng điệu và phong cách
- Sử dụng từ ngữ khác nhau
- Mỗi biến thể trên một dòng riêng
- Không thêm thông tin mới

Biến thể:"""
        
        return prompt
    
    def paraphrase_text(self, text: str) -> ParaphraseResult:
        """Paraphrase một câu thành nhiều biến thể"""
        try:
            if not self.api_manager:
                # Mock response for testing
                variants = [
                    f"Biến thể 1 của: {text}",
                    f"Biến thể 2 của: {text}",
                    f"Biến thể 3 của: {text}",
                    f"Biến thể 4 của: {text}",
                    f"Biến thể 5 của: {text}"
                ]
                return ParaphraseResult(
                    original=text,
                    variants=variants,
                    model_used="mock",
                    success=True,
                    metadata={"method": "mock"}
                )
            
            # Create prompt
            prompt = self._create_paraphrase_prompt(text)
            
            # Call local model
            response = self.api_manager.get_response(
                prompt=prompt,
                model=self.config.model
            )
            
            # Parse response
            variants = self._parse_paraphrase_response(response)
            
            return ParaphraseResult(
                original=text,
                variants=variants,
                model_used=self.config.model,
                success=True,
                metadata={
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                    "num_variants": len(variants)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Paraphrase failed: {e}")
            return ParaphraseResult(
                original=text,
                variants=[],
                model_used=self.config.model,
                success=False,
                error=str(e)
            )
    
    def _parse_paraphrase_response(self, response: str) -> List[str]:
        """Parse response từ model thành list variants"""
        lines = response.strip().split('\n')
        variants = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Remove numbering if present
                if line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '*')):
                    line = line.split('.', 1)[-1].strip()
                    line = line.lstrip('-* ').strip()
                
                if line:
                    variants.append(line)
        
        # Ensure we have the right number of variants
        if len(variants) < self.config.num_variants:
            # Pad with simple variations
            for i in range(len(variants), self.config.num_variants):
                variants.append(f"{variants[0]} (biến thể {i+1})")
        
        return variants[:self.config.num_variants]
    
    def paraphrase_batch(self, texts: List[str]) -> List[ParaphraseResult]:
        """Paraphrase nhiều câu cùng lúc"""
        results = []
        for text in texts:
            try:
                result = self.paraphrase_text(text)
                results.append(result)
            except Exception as e:
                results.append(ParaphraseResult(
                    original=text,
                    variants=[],
                    model_used=self.config.model,
                    success=False,
                    error=str(e)
                ))
        
        return results

class ParaphraseAugmentor:
    """Augmentor chính cho paraphrase"""
    
    def __init__(self, config: ParaphraseConfig = None):
        self.paraphraser = Paraphraser(config)
        self.logger = logging.getLogger(__name__)
    
    def augment_dataset(self, input_file: str, output_file: str) -> Dict[str, Any]:
        """Augment dataset từ file input"""
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Load input data
        texts = []
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        if 'text' in data:
                            texts.append(data['text'])
                        elif 'message' in data:
                            texts.append(data['message'])
                        else:
                            texts.append(str(data))
                    except json.JSONDecodeError:
                        texts.append(line)
        
        self.logger.info(f"Loaded {len(texts)} texts for paraphrasing")
        
        # Paraphrase in batches
        batch_size = 10
        all_results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            self.logger.info(f"Processing batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            
            results = self.paraphraser.paraphrase_batch(batch)
            all_results.extend(results)
        
        # Save results
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for result in all_results:
                if result.success:
                    for variant in result.variants:
                        output_data = {
                            "original": result.original,
                            "variant": variant,
                            "method": "paraphrase",
                            "model": result.model_used,
                            "metadata": result.metadata
                        }
                        f.write(json.dumps(output_data, ensure_ascii=False) + '\n')
        
        # Generate statistics
        stats = {
            "total_inputs": len(texts),
            "total_outputs": sum(len(r.variants) for r in all_results if r.success),
            "success_rate": sum(1 for r in all_results if r.success) / len(all_results),
            "model_used": self.paraphraser.config.model,
            "config": {
                "num_variants": self.paraphraser.config.num_variants,
                "temperature": self.paraphraser.config.temperature
            }
        }
        
        self.logger.info(f"Paraphrase augmentation completed: {stats}")
        return stats

async def main():
    """Demo function"""
    config = ParaphraseConfig(
        model="gemma2:2b",
        num_variants=3,
        temperature=0.7
    )
    
    augmentor = ParaphraseAugmentor(config)
    
    # Test single text
    result = await augmentor.paraphraser.paraphrase_text("Xin chào, hôm nay thế nào?")
    print(f"Original: {result.original}")
    print("Variants:")
    for i, variant in enumerate(result.variants, 1):
        print(f"  {i}. {variant}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
