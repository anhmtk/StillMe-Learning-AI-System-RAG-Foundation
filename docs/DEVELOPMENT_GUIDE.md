# StillMe AI Framework - Development Guide

## 🚀 Quick Start (VS Code Tasks)

### Start All Services
```bash
# In VS Code: Ctrl+Shift+P → "Tasks: Run Task" → "start:all"
# Hoặc chạy từng service riêng lẻ:
```

### Individual Services
- **Start AI Server**: `Tasks: Run Task` → `dev:ai-server` (Port 12015)
- **Start Gateway**: `Tasks: Run Task` → `dev:gateway` (Port 8000)  
- **Start Desktop**: `Tasks: Run Task` → `dev:desktop` (Port 3000)

### Stop Services
- **Stop AI Server**: `Tasks: Run Task` → `stop:ai-server`
- **Stop Gateway**: `Tasks: Run Task` → `stop:gateway`
- **Stop Desktop**: `Tasks: Run Task` → `stop:desktop`
- **Stop All**: `Tasks: Run Task` → `stop:all`

## 🔧 Manual Commands (Backup)

### AI Server
```bash
# Start AI Server
python stable_ai_server.py

# Test health
curl http://127.0.0.1:12015/health/ai
```

### Gateway Server
```bash
# Start Gateway
cd stillme_platform/gateway
python simple_main.py

# Test health
curl http://127.0.0.1:8000/health/ai
```

### Desktop App
```bash
# Start Desktop
cd stillme_platform/desktop
npm start

# Test health
curl http://127.0.0.1:3000
```

### Mobile App
```bash
# Start Metro Bundler
cd stillme_platform/StillMeSimple
npx react-native start

# Run on Android
npx react-native run-android
```

## 🏥 Health Check Endpoints

| Service | Health Endpoint | AI Health Endpoint |
|---------|----------------|-------------------|
| AI Server | `http://127.0.0.1:12015/health` | `http://127.0.0.1:12015/health/ai` |
| Gateway | `http://127.0.0.1:8000/health` | `http://127.0.0.1:8000/health/ai` |
| Desktop | `http://127.0.0.1:3000` | N/A |

## 🛠️ Troubleshooting

### Port Already in Use
```bash
# Kill process on specific port
powershell -ExecutionPolicy Bypass -File scripts/kill-by-port.ps1 8000
```

### Dependencies Missing
```bash
# Python dependencies
pip install fastapi uvicorn httpx

# Node dependencies
npm install
```

### VS Code Tasks Not Working
1. Check PowerShell execution policy: `Get-ExecutionPolicy`
2. Set execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
3. Restart VS Code

## 📁 Project Structure

```
stillme_ai/
├── scripts/                    # PowerShell automation scripts
│   ├── start_api.ps1          # Start API servers with healthcheck
│   ├── start_web.ps1          # Start web dev servers
│   └── kill-by-port.ps1       # Kill processes by port
├── .vscode/
│   └── tasks.json             # VS Code background tasks
├── stable_ai_server.py        # Stable AI Server (Port 12015)
├── stillme_platform/
│   ├── gateway/
│   │   └── simple_main.py     # Gateway Server (Port 8000)
│   ├── desktop/               # Desktop App (Port 3000)
│   └── StillMeSimple/         # Mobile App (Port 8081)
└── DEVELOPMENT_GUIDE.md       # This file
```

## 🎯 Best Practices

### ✅ DO
- **Always use VS Code Tasks** for server management
- **Wait for healthcheck** before running dependent services
- **Use background tasks** to avoid terminal blocking
- **Check logs** in VS Code terminal panels

### ❌ DON'T
- **Don't run servers directly** in terminal (causes blocking)
- **Don't open multiple terminals** for the same service
- **Don't ignore healthcheck failures**
- **Don't use Ctrl+C** unless absolutely necessary

## 🔄 Development Workflow

1. **Start Services**: Use VS Code Tasks (`start:all`)
2. **Wait for Health**: Check terminal for "READY" messages
3. **Test Endpoints**: Verify health endpoints respond
4. **Develop**: Make changes to code
5. **Test**: Use Mobile/Desktop apps to test
6. **Stop Services**: Use VS Code Tasks (`stop:all`)

## 🚨 Emergency Commands

### Kill All StillMe Processes
```bash
# Kill all StillMe-related processes
powershell -ExecutionPolicy Bypass -Command "
& { 
  .\scripts\kill-by-port.ps1 12015; 
  .\scripts\kill-by-port.ps1 8000; 
  .\scripts\kill-by-port.ps1 3000; 
  .\scripts\kill-by-port.ps1 8081 
}"
```

### Reset Everything
```bash
# Stop all services
Tasks: Run Task → stop:all

# Clear any stuck processes
taskkill /F /IM python.exe
taskkill /F /IM node.exe

# Restart all services
Tasks: Run Task → start:all
```

---

**💡 Tip**: Bookmark this guide and use VS Code Tasks for all server management to avoid terminal blocking issues!
