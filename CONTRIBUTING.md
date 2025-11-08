# Contributing to StillMe

Thank you for your interest in contributing to StillMe! This guide will help you get started.

## 🤝 How to Contribute

### Reporting Bugs
- Open an issue on GitHub with a clear description
- Include steps to reproduce
- Provide error logs if available

### Suggesting Features
- Open a discussion or issue
- Explain the use case and benefits
- Be open to feedback and iteration

### Code Contributions
- Fork the repository
- Create a feature branch
- Make your changes
- Add tests if applicable
- Submit a pull request

## 🚀 Adding Support for New AI Models

StillMe supports multiple AI providers (DeepSeek, OpenAI, etc.). To add support for a new model:

### Step 1: Create the API Function

Create a new function in `backend/api/main.py`:

```python
async def call_[model]_api(prompt: str, api_key: str, detected_lang: str = 'en') -> str:
    """
    Call [Model Name] API
    
    IMPORTANT: Use build_system_prompt_with_language() to ensure
    output language matches input language.
    
    Args:
        prompt: User prompt
        api_key: API key or endpoint URL
        detected_lang: Detected language code
        
    Returns:
        AI-generated response string
    """
    try:
        # ✅ Use centralized system prompt builder
        system_content = build_system_prompt_with_language(detected_lang)
        
        # Make API call with your model's specific format
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "[YOUR_API_ENDPOINT]",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "[model-name]",
                    "system": system_content,  # ✅ Use system prompt
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7
                }
            )
            data = response.json()
            # Parse response according to your API's format
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"[Model] API error: {e}")
        return f"[Model] API error: {str(e)}"
```

### Step 2: Add to Model Router

In `generate_ai_response()` function, add your model check:

```python
# Check for API keys (priority order)
[model]_key = os.getenv("[MODEL]_API_KEY")
if [model]_key:
    return await call_[model]_api(prompt, [model]_key, detected_lang=detected_lang)
```

### Step 3: Update Documentation

- Add your model to `README.md` under supported models
- Update `env.example` with your API key variable
- Add any model-specific configuration notes

### Step 4: Test

- Test with different languages (English, Vietnamese, etc.)
- Verify language matching works correctly
- Test error handling

### Example: Adding Claude (Anthropic)

```python
# 1. Create function
async def call_claude_api(prompt: str, api_key: str, detected_lang: str = 'en') -> str:
    system_content = build_system_prompt_with_language(detected_lang)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            json={
                "model": "claude-3-opus-20240229",
                "max_tokens": 2000,
                "system": system_content,
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        data = response.json()
        return data["content"][0]["text"]

# 2. Add to router
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
if anthropic_key:
    return await call_claude_api(prompt, anthropic_key, detected_lang=detected_lang)
```

## ✅ Why This Approach?

- **Consistency**: All models use the same language matching logic
- **Maintainability**: One place to update language instructions
- **Community-Friendly**: Clear, simple steps for contributors
- **Future-Proof**: Easy to extend without breaking existing code

## 📝 Code Style

- Follow PEP 8 Python style guide
- Use type hints
- Add docstrings to functions
- Write clear, descriptive variable names

## 🧪 Testing

- Add unit tests for new features
- Test error handling
- Verify language matching works
- Test with different input languages

## 📚 Questions?

- Open a discussion on GitHub
- Check existing issues
- Review the codebase

Thank you for contributing to StillMe! 🎉

