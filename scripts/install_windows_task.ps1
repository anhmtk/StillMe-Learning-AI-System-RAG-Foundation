# AgentDev Operations Service - Windows Task Scheduler Setup
# =========================================================
# 
# This script sets up AgentDev Operations Service to run automatically on Windows 11
# as a scheduled task that starts at logon and runs every 15 minutes.

param(
    [string]$ProjectPath = "D:\stillme_ai",
    [string]$PythonPath = "python",
    [switch]$Remove = $false
)

$TaskName = "AgentDevOpsService"
$ScriptPath = Join-Path $ProjectPath "scripts\start_agentdev_monitor.py"
$LogPath = Join-Path $ProjectPath "logs"

# Create logs directory if it doesn't exist
if (!(Test-Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath -Force
    Write-Host "✅ Created logs directory: $LogPath"
}

if ($Remove) {
    # Remove existing task
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "✅ Removed existing task: $TaskName"
    } catch {
        Write-Host "ℹ️  No existing task to remove"
    }
    exit 0
}

# Check if task already exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "⚠️  Task '$TaskName' already exists. Use -Remove to remove it first."
    exit 1
}

# Verify script exists
if (!(Test-Path $ScriptPath)) {
    Write-Host "❌ Script not found: $ScriptPath"
    exit 1
}

try {
    # Create the action
    $Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$ScriptPath`" --daemon" -WorkingDirectory $ProjectPath
    
    # Create the trigger (at logon and every 15 minutes)
    $Trigger1 = New-ScheduledTaskTrigger -AtLogOn
    $Trigger2 = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 365)
    
    # Create the principal (run as current user)
    $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType InteractiveToken
    
    # Create the settings
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable
    
    # Register the task
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger @($Trigger1, $Trigger2) -Principal $Principal -Settings $Settings -Description "AgentDev Operations Service - 24/7 Technical Manager"
    
    Write-Host "✅ Successfully created scheduled task: $TaskName"
    Write-Host "📋 Task Details:"
    Write-Host "   - Name: $TaskName"
    Write-Host "   - Script: $ScriptPath"
    Write-Host "   - Working Directory: $ProjectPath"
    Write-Host "   - Triggers: At logon + Every 15 minutes"
    Write-Host "   - User: $env:USERNAME"
    Write-Host ""
    Write-Host "🔧 Management Commands:"
    Write-Host "   - View task: Get-ScheduledTask -TaskName '$TaskName'"
    Write-Host "   - Start task: Start-ScheduledTask -TaskName '$TaskName'"
    Write-Host "   - Stop task: Stop-ScheduledTask -TaskName '$TaskName'"
    Write-Host "   - Remove task: .\install_windows_task.ps1 -Remove"
    Write-Host ""
    Write-Host "📊 Monitor logs: Get-Content '$LogPath\agentdev_ops.log' -Tail 20 -Wait"
    
} catch {
    Write-Host "❌ Failed to create scheduled task: $($_.Exception.Message)"
    exit 1
}
