<#
    Register the staging agent to start silently at logon.

    Runs it under pythonw.exe, which has no console window at all — nothing
    appears on screen, nothing takes focus, and the screenshots it takes are
    rendered offscreen by headless Chrome. You keep working; it sits on
    127.0.0.1:8787 waiting for the tracker to hand it a batch.

    Usage (from the repo root, in an ordinary PowerShell window — no admin):
        powershell -ExecutionPolicy Bypass -File agent\install-task.ps1
        powershell -ExecutionPolicy Bypass -File agent\install-task.ps1 -Remove
#>

[CmdletBinding()]
param(
    [switch]$Remove,
    [string]$TaskName = "Internship staging agent"
)

$ErrorActionPreference = "Stop"

if ($Remove) {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Removed the scheduled task '$TaskName'."
    } else {
        Write-Host "No scheduled task named '$TaskName' — nothing to remove."
    }
    return
}

# --- locate pythonw.exe -----------------------------------------------------
# pythonw is the point of this: python.exe would flash a console window at
# logon and leave one in the taskbar.
$pythonw = $null
$pyCmd = Get-Command pythonw.exe -ErrorAction SilentlyContinue
if ($pyCmd) {
    $pythonw = $pyCmd.Source
} else {
    $pyCmd = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($pyCmd) {
        $candidate = Join-Path (Split-Path $pyCmd.Source -Parent) "pythonw.exe"
        if (Test-Path $candidate) { $pythonw = $candidate }
    }
}
if (-not $pythonw) {
    throw "Could not find pythonw.exe on PATH. Install Python, or edit this script with its full path."
}

# --- locate the agent -------------------------------------------------------
$repoRoot  = Split-Path $PSScriptRoot -Parent
$agentPath = Join-Path $PSScriptRoot "stage_agent.py"
if (-not (Test-Path $agentPath)) {
    throw "Could not find $agentPath — run this from the repo it lives in."
}

Write-Host "pythonw : $pythonw"
Write-Host "agent   : $agentPath"

$action = New-ScheduledTaskAction -Execute $pythonw `
    -Argument ('"{0}"' -f $agentPath) -WorkingDirectory $repoRoot

$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

# Interactive/limited: it only ever binds loopback and reads one public file,
# so there is nothing here that wants elevation.
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive -RunLevel Limited

# No idle/battery conditions: the whole point is that it is there whenever you
# are. RestartCount covers it dying on a transient port clash.
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Replaced the existing task."
}

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings `
    -Description "Stages outreach drafts from the internship tracker on 127.0.0.1:8787. Sends nothing." | Out-Null

Write-Host ""
Write-Host "Registered '$TaskName' — it will start at every logon."
Write-Host "Start it now without logging out:"
Write-Host "    Start-ScheduledTask -TaskName '$TaskName'"
Write-Host ""
Write-Host "The agent writes its review-page link to:"
Write-Host "    $env:LOCALAPPDATA\internship-agent\agent.log"
