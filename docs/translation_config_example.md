# Translation Configuration Example

## Environment Variables

Add these to your `.env` file:

```bash
# Translation Configuration
TRANSLATION_CORE_LANG=en
TRANSLATOR_PRIORITY=gemma,nllb
NLLB_MODEL_NAME=facebook/nllb-200-distilled-600M
```

## Configuration Options

- **TRANSLATION_CORE_LANG**: Core language for AI processing (default: "en")
- **TRANSLATOR_PRIORITY**: Priority order for translation engines (default: "gemma,nllb")
- **NLLB_MODEL_NAME**: NLLB model to use (default: "facebook/nllb-200-distilled-600M")

## Usage

Set the `X-User-Lang` header in your requests:

```bash
curl -X POST http://localhost:21568/send-message \
  -H "Content-Type: application/json" \
  -H "X-User-Lang: ja" \
  -d '{"message":"Xin chào, hôm nay thế nào?", "language":"vi"}'
```
