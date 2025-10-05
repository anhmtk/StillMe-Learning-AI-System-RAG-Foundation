# I18N Inventory - StillMe Desktop App

## Current Chat Input/Output Components

### 1. Main Desktop App (Python Tkinter)
**File:** `stillme_desktop_app.py`
- **Chat Input:** `self.message_input` (Text widget, line 255-272)
- **Message Handler:** `send_message()` method (line 255)
- **Background Thread:** `_send_message_thread()` (line 274)
- **System Prompt:** Hardcoded in `_send_message_thread()` (line 278)
- **Response Handler:** `_handle_success()` method (line 307)

**Current System Prompt:**
```python
system_prompt = "You are StillMe — a personal AI companion. Always introduce and refer to yourself as 'StillMe'. Never claim to be Gemma, OpenAI, DeepSeek, or any underlying provider/model. If the user asks 'bạn là ai?', answer 'Mình là StillMe…' and avoid mentioning engine unless asked explicitly."
```

### 2. Alternative Desktop App (Python Tkinter)
**File:** `desktop_app/stillme_desktop_app.py`
- **Chat Input:** `self.input_var` (StringVar, line 279-290)
- **Message Handler:** `send_message()` method (line 279)
- **Background Thread:** `_send_to_server()` (line 292)
- **System Prompt:** None (uses metadata with language: "vi", line 304)
- **Response Handler:** `add_assistant_message()` method (line 327)

### 3. React Desktop App
**File:** `stillme_platform/desktop/src/App.tsx`
- **Chat Input:** `textarea` with `messageText` state (line 237-244)
- **Message Handler:** `sendMessage()` function (line 144)
- **System Prompt:** None (sends to localhost:8000)
- **Response Handler:** WebSocket/HTTP polling (line 115-142)

### 4. Mobile App (React Native)
**File:** `stillme_platform/mobile/src/screens/ChatScreen.tsx`
- **Chat Input:** `TextInput` with `inputText` state (line 220-229)
- **Message Handler:** WebSocket service
- **System Prompt:** None
- **Response Handler:** WebSocket messages

## Backend System Prompt Handling

### Main Backend (Python)
**File:** `app.py`
- **Chat Endpoint:** `_handle_chat()` method (line 271)
- **System Prompt:** Extracted from request (line 282)
- **Router:** `smart_router.route_message()` (line 291)

## Current Language Support

### Desktop App (Python)
- **Default Language:** Vietnamese (hardcoded in system prompt)
- **No Language Detection:** Currently fixed to Vietnamese
- **No Language Toggle:** No UI for language switching

### Backend
- **Language Parameter:** Accepts `language` parameter (line 281) but not used
- **System Prompt:** Uses provided system prompt or defaults to StillMe persona

## I18N Implementation Plan

### 1. Language Detection
- **Location:** `libs/lang/detect.py` (new file)
- **Method:** Heuristic detection based on Vietnamese characters and common patterns
- **Output:** Locale codes (`vi-VN`, `en-US`, etc.)

### 2. System Prompt Enhancement
- **Location:** `stillme_desktop_app.py` line 278
- **Enhancement:** Dynamic system prompt with language instruction
- **Format:** "Always respond in <detected_language> unless user explicitly asks to switch"

### 3. Language Toggle UI
- **Location:** Settings dialog in `stillme_desktop_app.py`
- **Component:** Toggle button (VI/EN) in input area
- **Behavior:** Override detected language for current session

### 4. Session Language Tracking
- **Location:** `stillme_desktop_app.py` class variables
- **Variables:** `userTurnLocale`, `sessionPreferredLocale`
- **Logic:** Track language changes over multiple turns

## Files to Modify

1. **`stillme_desktop_app.py`** - Main implementation
2. **`libs/lang/detect.py`** - Language detection utility
3. **`config/brand.py`** - Branding configuration
4. **`docs/i18n-inventory.md`** - This file

## Current Status
- ✅ **Audit Complete:** Identified all chat input/output components
- ⏳ **Language Detection:** Not implemented
- ⏳ **System Prompt Enhancement:** Not implemented  
- ⏳ **Language Toggle:** Not implemented
- ⏳ **Session Tracking:** Not implemented
