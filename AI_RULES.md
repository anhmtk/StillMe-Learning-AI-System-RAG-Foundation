# AI_RULES – StillMe AI Project

This file describes the technology stack, project structure, and clear rules for library usage for the **StillMe AI** application.

---

## **Tech Stack Overview**
1. **Backend:** Python 3.10+  
   - Core modules: `agent_dev.py`, `framework.py`, `agent_planner.py`
   - Testing framework: `pytest`
   - Logging: `logging` module, log files in `*.log`
2. **Frontend:** React 18 + Vite 5  
   - Entry: `index.html`
   - Main components: `src/App.jsx`, `src/main.jsx`
   - UI state management (optional): React hooks (`useState`, `useEffect`)
3. **Package Management:**
   - Backend: `pip` + `requirements.txt`
   - Frontend: `npm` + `package.json`
4. **Containerization:** Docker (using `Dockerfile`)
5. **Version Control:** Git (branch strategy: `main` and `agent-fix-*`)

---

## **Library Usage Rules**
- **Backend (Python):**
  - Use `pytest` for testing. Command:
    ```bash
    pytest tests/ -v
    ```
  - Use `logging` for debug and error tracking (no print statements in production).
  - Keep all configuration variables in `.env`.

- **Frontend (React):**
  - Use only React 18.x APIs (`useState`, `useEffect`, `useContext`).
  - Avoid adding heavy UI libraries unless approved.
  - Use Vite for fast builds and hot reload (`npm run dev`).

- **Common Guidelines:**
  - Separate logic and UI.
  - Write tests for any new backend module.
  - Follow modular architecture – no direct cross-module imports unless necessary.

---

## **Testing Guidelines**
1. **Backend Tests:**
   - All Python tests should be placed in the `tests/` folder.
   - Run:
     ```bash
     pytest tests/ -v
     ```
   - If any test fails, log details to `agent_dev_patch.log`.

2. **Frontend Tests:**
   - Basic tests (if needed) with React Testing Library or Jest.

---

## **Important Notes**
- All AI-generated code (via Dyad or external tools) must follow these library usage rules.
- Do not mix frontend and backend code in the same folder.
- Always document major changes in `README.md` or `AI_RULES.md`.

---

_Last updated: 2025-07-28_
