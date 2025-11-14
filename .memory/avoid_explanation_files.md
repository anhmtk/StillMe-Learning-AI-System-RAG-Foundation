# Memory: Avoid Creating Files Just for Explanation

## Rule
**DO NOT create documentation files just to explain concepts during conversation.**

Instead:
- Explain directly in the chat session
- Only create files if:
  1. User explicitly requests documentation
  2. File is needed for code reference (e.g., config files, actual implementation)
  3. File is part of the project structure (e.g., README, API docs)

## Examples of what NOT to do:
- ❌ Creating `docs/EXPLANATION.md` just to explain a concept
- ❌ Creating `docs/ANALYSIS.md` for one-time analysis
- ❌ Creating temporary files for explanations

## Examples of what TO do:
- ✅ Explain in chat: "Architecture là..."
- ✅ Create files only when user requests or for actual code/config
- ✅ Use existing files if they exist

## Context
User noted that I've improved in:
- Checking codebase before creating files
- Not creating/deleting files randomly
- Not using # type: ignore or commenting out code
- Testing for syntax errors
- Reducing problems from 200+ to manageable

But still have one issue:
- Creating files just for explanation instead of explaining in session

