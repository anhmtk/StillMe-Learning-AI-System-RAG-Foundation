"""EmotionSense V1 for StillMe Framework"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

class EmotionType(Enum):
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    NEUTRAL = "neutral"

class ErrorCode(Enum):
    SUCCESS = 0
    INVALID_INPUT = 1
    PROCESSING_ERROR = 2
    MODEL_ERROR = 3
    TIMEOUT = 4

@dataclass
class EmotionResult:
    """Emotion detection result"""
    emotion: EmotionType
    confidence: float
    timestamp: datetime
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class EmotionSenseV1:
    """EmotionSense V1 - Basic emotion detection"""

    def __init__(self):
        self.logger = logger
        self.detection_history: list[EmotionResult] = []
        self.logger.info("✅ EmotionSenseV1 initialized")

    def detect_emotion(self, text: str) -> EmotionResult:
        """Detect emotion from text"""
        try:
            # Simple emotion detection based on keywords
            text_lower = text.lower()

            # Happy keywords
            happy_keywords = ["happy", "joy", "excited", "great", "wonderful", "amazing"]
            if any(keyword in text_lower for keyword in happy_keywords):
                emotion = EmotionType.HAPPY
                confidence = 0.8
            # Sad keywords
            elif any(keyword in text_lower for keyword in ["sad", "depressed", "unhappy", "terrible", "awful"]):
                emotion = EmotionType.SAD
                confidence = 0.8
            # Angry keywords
            elif any(keyword in text_lower for keyword in ["angry", "mad", "furious", "rage", "hate"]):
                emotion = EmotionType.ANGRY
                confidence = 0.8
            # Fear keywords
            elif any(keyword in text_lower for keyword in ["scared", "afraid", "fear", "worried", "anxious"]):
                emotion = EmotionType.FEAR
                confidence = 0.8
            # Surprise keywords
            elif any(keyword in text_lower for keyword in ["surprised", "shocked", "amazed", "wow", "incredible"]):
                emotion = EmotionType.SURPRISE
                confidence = 0.8
            # Disgust keywords
            elif any(keyword in text_lower for keyword in ["disgusted", "gross", "nasty", "revolting"]):
                emotion = EmotionType.DISGUST
                confidence = 0.8
            else:
                emotion = EmotionType.NEUTRAL
                confidence = 0.5

            result = EmotionResult(
                emotion=emotion,
                confidence=confidence,
                timestamp=datetime.now()
            )

            self.detection_history.append(result)
            self.logger.info(f"😊 Emotion detected: {emotion.value} (confidence: {confidence})")
            return result

        except Exception as e:
            self.logger.error(f"❌ Emotion detection failed: {e}")
            return EmotionResult(
                emotion=EmotionType.NEUTRAL,
                confidence=0.0,
                timestamp=datetime.now()
            )

    def get_emotion_summary(self) -> dict[str, Any]:
        """Get emotion detection summary"""
        try:
            total_detections = len(self.detection_history)
            emotions_by_type = {}

            for result in self.detection_history:
                emotion_key = result.emotion.value
                emotions_by_type[emotion_key] = emotions_by_type.get(emotion_key, 0) + 1

            return {
                "total_detections": total_detections,
                "emotions_by_type": emotions_by_type,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to get emotion summary: {e}")
            return {"error": str(e)}

    def clear_history(self):
        """Clear detection history"""
        self.detection_history.clear()
        self.logger.info("🧹 Emotion detection history cleared")

# Error codes for compatibility
ERROR_CODES = {
    "SUCCESS": ErrorCode.SUCCESS,
    "INVALID_INPUT": ErrorCode.INVALID_INPUT,
    "PROCESSING_ERROR": ErrorCode.PROCESSING_ERROR,
    "MODEL_ERROR": ErrorCode.MODEL_ERROR,
    "TIMEOUT": ErrorCode.TIMEOUT
}
