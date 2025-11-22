# Phân Tích Khả Năng Tự Động Hóa Quy Trình Test

## 📋 Quy Trình Hiện Tại (Manual)

```
1. Phân tích kết quả test → Fix code
2. Tạo commit
3. Chạy script push (nhập token)
4. Đợi Railway deploy xong (manual check)
5. Chạy test script
6. Xem kết quả → Báo cáo → Lặp lại
```

**Vấn đề:**
- Phải đợi deploy xong (không biết khi nào xong)
- Phải chạy test thủ công
- Phải check kết quả thủ công
- Không có feedback loop tự động

---

## ✅ Giải Pháp 1: Railway API + Polling (Khả Thi 100%)

### Cách Hoạt Động:

1. **Railway API** để check deployment status
2. **Polling** mỗi 30s-60s cho đến khi deploy xong
3. **Tự động chạy test** sau khi deploy xong
4. **Tự động báo cáo** kết quả

### Implementation:

```powershell
# scripts/auto_test_after_deploy.ps1

# 1. Push code (existing script)
.\scripts\push_main_with_token.ps1

# 2. Wait for Railway deployment
$deploymentStatus = "building"
while ($deploymentStatus -ne "success") {
    Start-Sleep -Seconds 30
    $deploymentStatus = Get-RailwayDeploymentStatus
    Write-Host "Deployment status: $deploymentStatus"
}

# 3. Run test
python scripts/test_transparency_and_evidence.py

# 4. Parse results and report
$results = Get-Content test_results_transparency_*.json | ConvertFrom-Json
Write-Host "Test Results: $($results.passed)/$($results.total_questions) passed"
```

### Railway API Endpoints:

```bash
# Get deployment status
GET https://api.railway.app/v1/deployments/{deployment_id}
Authorization: Bearer {RAILWAY_API_TOKEN}

# Response:
{
  "status": "success" | "building" | "failed",
  "createdAt": "2025-01-01T00:00:00Z",
  "updatedAt": "2025-01-01T00:05:00Z"
}
```

### Pros:
- ✅ 100% tự động
- ✅ Không cần manual check
- ✅ Có thể chạy local hoặc CI/CD

### Cons:
- ⚠️ Cần Railway API token
- ⚠️ Polling có thể tốn thời gian (30s-60s mỗi lần check)

---

## ✅ Giải Pháp 2: Railway Webhook + GitHub Actions (Khả Thi 100%)

### Cách Hoạt Động:

1. **Railway Webhook** gửi notification khi deploy xong
2. **GitHub Actions** nhận webhook → trigger test
3. **Test chạy tự động** trên GitHub runner
4. **Kết quả** được comment vào PR hoặc commit

### Implementation:

```yaml
# .github/workflows/auto-test-on-deploy.yml
name: Auto Test After Railway Deploy

on:
  repository_dispatch:
    types: [railway-deploy-success]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        env:
          STILLME_API_BASE: ${{ secrets.RAILWAY_API_URL }}
        run: |
          python scripts/test_transparency_and_evidence.py
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test_results_*.json
      
      - name: Comment on commit
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync('test_results_*.json'));
            github.rest.repos.createCommitComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              commit_sha: context.sha,
              body: `## Test Results\n\n✅ Passed: ${results.passed}/${results.total_questions}\n❌ Failed: ${results.failed}`
            });
```

### Railway Webhook Setup:

1. Vào Railway Dashboard → Project Settings → Webhooks
2. Add webhook: `https://api.github.com/repos/{owner}/{repo}/dispatches`
3. Payload:
```json
{
  "event_type": "railway-deploy-success",
  "client_payload": {
    "deployment_id": "{deployment_id}",
    "status": "success"
  }
}
```

### Pros:
- ✅ 100% tự động
- ✅ Không cần local machine
- ✅ Có thể chạy trên nhiều environments
- ✅ Kết quả được lưu trong GitHub

### Cons:
- ⚠️ Cần setup webhook (one-time)
- ⚠️ Cần GitHub Actions runner (free tier có 2000 phút/tháng)

---

## ✅ Giải Pháp 3: Local Script với Railway CLI (Khả Thi 100%)

### Cách Hoạt Động:

1. **Railway CLI** để check deployment status
2. **Local script** polling cho đến khi deploy xong
3. **Tự động chạy test** sau khi deploy xong
4. **Tự động mở kết quả** trong browser/editor

### Implementation:

```powershell
# scripts/auto_test_workflow.ps1

# 1. Commit and push
git add .
git commit -m "Fix: ..."
.\scripts\push_main_with_token.ps1

# 2. Wait for deployment using Railway CLI
Write-Host "Waiting for Railway deployment..."
$maxWait = 600  # 10 minutes max
$elapsed = 0
while ($elapsed -lt $maxWait) {
    $status = railway status --json | ConvertFrom-Json
    if ($status.status -eq "success") {
        Write-Host "✅ Deployment successful!"
        break
    }
    Start-Sleep -Seconds 30
    $elapsed += 30
    Write-Host "Still deploying... ($elapsed seconds)"
}

# 3. Run test
Write-Host "Running tests..."
python scripts/test_transparency_and_evidence.py
$testExitCode = $LASTEXITCODE

# 4. Open results
$latestResult = Get-ChildItem test_results_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($testExitCode -eq 0) {
    Write-Host "✅ Tests passed! Opening results..."
    code $latestResult.FullName  # VS Code
} else {
    Write-Host "❌ Tests failed! Opening results..."
    code $latestResult.FullName
}
```

### Pros:
- ✅ 100% tự động
- ✅ Chạy local, không cần external services
- ✅ Có thể customize theo nhu cầu

### Cons:
- ⚠️ Cần Railway CLI installed
- ⚠️ Phải chạy trên local machine

---

## ✅ Giải Pháp 4: Hybrid - Local Script + Railway API (Khả Thi 100%, Recommended)

### Cách Hoạt Động:

Kết hợp **Railway API** với **local script** để:
1. Push code
2. Poll Railway API cho deployment status
3. Tự động chạy test khi deploy xong
4. Tự động parse và báo cáo kết quả

### Implementation:

```powershell
# scripts/auto_test_workflow.ps1

param(
    [string]$RailwayApiToken = $env:RAILWAY_API_TOKEN,
    [string]$ServiceId = $env:RAILWAY_SERVICE_ID
)

# 1. Push code
.\scripts\push_main_with_token.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Push failed!" -ForegroundColor Red
    exit 1
}

# 2. Get latest deployment
Write-Host "🔍 Checking Railway deployment status..." -ForegroundColor Cyan
$headers = @{
    "Authorization" = "Bearer $RailwayApiToken"
}
$deployment = Invoke-RestMethod -Uri "https://api.railway.app/v1/deployments?serviceId=$ServiceId&limit=1" -Headers $headers
$deploymentId = $deployment.deployments[0].id

# 3. Poll until deployment is done
Write-Host "⏳ Waiting for deployment to complete..." -ForegroundColor Yellow
$maxWait = 600  # 10 minutes
$elapsed = 0
while ($elapsed -lt $maxWait) {
    $status = Invoke-RestMethod -Uri "https://api.railway.app/v1/deployments/$deploymentId" -Headers $headers
    
    if ($status.status -eq "success") {
        Write-Host "✅ Deployment successful!" -ForegroundColor Green
        break
    } elseif ($status.status -eq "failed") {
        Write-Host "❌ Deployment failed!" -ForegroundColor Red
        exit 1
    }
    
    Start-Sleep -Seconds 30
    $elapsed += 30
    Write-Host "   Still deploying... ($elapsed seconds)" -ForegroundColor Gray
}

if ($elapsed -ge $maxWait) {
    Write-Host "⏰ Timeout waiting for deployment!" -ForegroundColor Red
    exit 1
}

# 4. Wait a bit more for service to be ready
Write-Host "⏳ Waiting for service to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 5. Run test
Write-Host "🧪 Running tests..." -ForegroundColor Cyan
$env:STILLME_API_BASE = "https://stillme-backend-production.up.railway.app"
python scripts/test_transparency_and_evidence.py
$testExitCode = $LASTEXITCODE

# 6. Parse and report results
$latestResult = Get-ChildItem test_results_transparency_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latestResult) {
    $results = Get-Content $latestResult.FullName | ConvertFrom-Json
    
    Write-Host ""
    Write-Host "📊 Test Results Summary" -ForegroundColor Cyan
    Write-Host "   Total Questions: $($results.total_questions)" -ForegroundColor White
    Write-Host "   ✅ Passed: $($results.passed)" -ForegroundColor Green
    Write-Host "   ❌ Failed: $($results.failed)" -ForegroundColor Red
    Write-Host "   ⚠️  Errors: $($results.errors)" -ForegroundColor Yellow
    Write-Host "   📈 Pass Rate: $([math]::Round($results.pass_rate, 2))%" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📄 Full results: $($latestResult.FullName)" -ForegroundColor Gray
    
    # Open results in VS Code
    code $latestResult.FullName
}

exit $testExitCode
```

### Setup:

1. **Get Railway API Token:**
   - Vào Railway Dashboard → Account Settings → Tokens
   - Tạo token mới
   - Export: `$env:RAILWAY_API_TOKEN = "your_token"`

2. **Get Service ID:**
   - Vào Railway Dashboard → Service → Settings
   - Copy Service ID
   - Export: `$env:RAILWAY_SERVICE_ID = "your_service_id"`

3. **Run:**
   ```powershell
   .\scripts\auto_test_workflow.ps1
   ```

### Pros:
- ✅ 100% tự động
- ✅ Không cần external services (GitHub Actions, webhooks)
- ✅ Chạy local, full control
- ✅ Có thể customize theo nhu cầu
- ✅ Báo cáo chi tiết

### Cons:
- ⚠️ Cần Railway API token (free, dễ lấy)
- ⚠️ Phải chạy trên local machine

---

## 📊 So Sánh Các Giải Pháp

| Giải Pháp | Tự Động | Setup | Chi Phí | Khuyến Nghị |
|-----------|---------|-------|---------|-------------|
| **1. Railway API + Polling** | ✅ 100% | ⭐⭐ Medium | Free | ⭐⭐⭐ Good |
| **2. Webhook + GitHub Actions** | ✅ 100% | ⭐⭐⭐ Hard | Free (limited) | ⭐⭐⭐⭐ Great |
| **3. Railway CLI** | ✅ 100% | ⭐ Easy | Free | ⭐⭐⭐ Good |
| **4. Hybrid (API + Local)** | ✅ 100% | ⭐⭐ Medium | Free | ⭐⭐⭐⭐⭐ **Best** |

---

## 🎯 Khuyến Nghị: Giải Pháp 4 (Hybrid)

**Lý do:**
1. ✅ **100% tự động** - không cần manual check
2. ✅ **Dễ setup** - chỉ cần Railway API token
3. ✅ **Full control** - chạy local, customize được
4. ✅ **Không phụ thuộc** external services
5. ✅ **Báo cáo chi tiết** - tự động parse và hiển thị

**Next Steps:**
1. Tạo Railway API token
2. Implement script `auto_test_workflow.ps1`
3. Test với 1 commit nhỏ
4. Tích hợp vào workflow hàng ngày

---

## 🚀 Quick Start

```powershell
# 1. Setup environment variables
$env:RAILWAY_API_TOKEN = "your_token_here"
$env:RAILWAY_SERVICE_ID = "your_service_id_here"

# 2. Run automated workflow
.\scripts\auto_test_workflow.ps1

# Script sẽ tự động:
# - Push code
# - Wait for Railway deployment
# - Run tests
# - Report results
```

---

## 📝 Notes

- **Railway API Rate Limits:** 100 requests/minute (đủ cho polling mỗi 30s)
- **Test Timeout:** Có thể set timeout cho test (default 60s/question)
- **Error Handling:** Script sẽ exit với code != 0 nếu test fail
- **Results Storage:** Kết quả được lưu vào `test_results_transparency_*.json`

---

## ❓ FAQ

**Q: Làm sao biết Railway đã deploy xong?**
A: Poll Railway API endpoint `/v1/deployments/{id}` mỗi 30s, check `status == "success"`

**Q: Làm sao biết test đã chạy xong?**
A: Test script return exit code (0 = success, != 0 = failed). Script check `$LASTEXITCODE`

**Q: Có thể chạy nhiều test scripts không?**
A: Có, có thể chạy nhiều test scripts sau khi deploy xong:
```powershell
python scripts/test_transparency_and_evidence.py
python scripts/test_curiosity.py
python tests/stillme_chat_test_suite.py
```

**Q: Có thể tự động commit và push không?**
A: Có, nhưng không khuyến nghị vì mất control. Nên giữ manual commit để review code trước khi push.

