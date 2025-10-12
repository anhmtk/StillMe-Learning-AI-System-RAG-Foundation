#!/usr/bin/env python3
"""
StillMe System Prompt Manager
Handles session-based intro control and comprehensive response generation
"""


class SystemPromptManager:
    """Manages system prompts with session control and response depth"""

    def __init__(self):
        self.session_introduced = False
        self.session_id = None

    def get_system_prompt(
        self,
        language_name: str,
        locale: str,
        session_id: str,
        is_first_message: bool = False,
    ) -> str:
        """Generate system prompt based on session state and language"""

        # Update session tracking
        if self.session_id != session_id:
            self.session_id = session_id
            self.session_introduced = False

        # Base StillMe identity
        base_identity = """You are StillMe — an Intelligent Personal Companion (IPC). You are a personal AI companion that goes beyond being just an "assistant" to be a true companion — humble, learning from the user, and combining multi-agent systems (MAS) with personalized (Adaptive) and ethical (Ethical) AI."""

        # Language instruction
        language_instruction = f"""IMPORTANT: Always respond in {language_name} ({locale}) unless the user explicitly asks to switch language."""

        # Session intro control
        if is_first_message and not self.session_introduced:
            intro_instruction = """For this first message in the session, introduce yourself as "StillMe – Intelligent Personal Companion (IPC)" and briefly explain your capabilities. Keep the introduction concise but warm."""
            self.session_introduced = True
        else:
            intro_instruction = """Do NOT repeat your introduction. Respond directly to the user's question or request without reintroducing yourself."""

        # Response depth and quality
        response_quality = """Provide comprehensive, thoughtful responses with:
- Depth: Explain concepts thoroughly with examples and context
- Structure: Use bullet points, numbered lists, or clear sections when appropriate
- Examples: Include relevant examples, analogies, or comparisons
- Clarity: If a question is ambiguous, break it down into 2-3 different interpretations and address each
- Practicality: Offer actionable insights when possible
- Empathy: Show understanding of the user's perspective and needs"""

        # Identity enforcement
        identity_enforcement = """Never claim to be Gemma, OpenAI, DeepSeek, GPT, ChatGPT, Claude, or any underlying provider/model. Always refer to yourself as "StillMe" or "Mình là StillMe" (in Vietnamese)."""

        # Combine all components
        system_prompt = f"""{base_identity}

{language_instruction}

{intro_instruction}

{response_quality}

{identity_enforcement}

Current user message language: {language_name} ({locale})"""

        return system_prompt

    def should_show_intro(self, session_id: str) -> bool:
        """Check if intro should be shown for this session"""
        if self.session_id != session_id:
            self.session_id = session_id
            self.session_introduced = False
        return not self.session_introduced

    def mark_intro_shown(self):
        """Mark that intro has been shown for current session"""
        self.session_introduced = True


# Global instance
system_prompt_manager = SystemPromptManager()
