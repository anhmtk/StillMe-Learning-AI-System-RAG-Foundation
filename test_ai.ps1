# Test AI Server
Write-Host "Testing AI Server health..."
$health = Invoke-WebRequest -Uri "http://127.0.0.1:11624/health/ai" -Method GET
Write-Host "Health Response: $($health.Content)"

Write-Host "`nTesting AI Server inference..."
$body = @{
    message = "chào stillme"
    locale = "vi"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://127.0.0.1:11624/inference" -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
Write-Host "Inference Response: $($response.Content)"

Write-Host "`nTest completed!"
