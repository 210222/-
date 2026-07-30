<#
.SYNOPSIS
    Complete 360 Security Guard Removal Script
.DESCRIPTION
    Systematically removes ALL traces of 360 Total Security / 360 Safe Guard
    across 8 phases:
      1. Terminate running processes
      2. Stop and delete services
      3. Unregister DLL/OCX components
      4. Run official uninstaller (if present)
      5. Delete program files, appdata, sandbox directories
      6. Remove kernel driver residuals (System32\drivers\*.removed/*.old/*.sys.NNN)
      7. Clean scheduled tasks and Windows Firewall rules
      8. Remove shortcuts and registry entries
    Covers the "卸载后残留" problem — driver backups, locked files, and
    hidden system artifacts that ordinary uninstallers leave behind.
.NOTES
    Requires Administrator privileges. Run as Administrator in PowerShell.
    Recommend restarting PC after completion.
    Tested on Windows 10/11 with 360 Total Security / 360 Safe Guard.
#>

#Requires -RunAsAdministrator

$ErrorActionPreference = "Continue"
$host.UI.RawUI.WindowTitle = "360 Removal Tool"

# ============================================================
# CONFIGURATION
# ============================================================
$TARGET_DIRS = @(
    "C:\Program Files (x86)\360",
    "C:\Program Files\360",
    "C:\360SANDBOX",
    "C:\ProgramData\360safe",
    "C:\ProgramData\360SD"
)

$TARGET_APPDATA = @(
    "$env:LOCALAPPDATA\360safe",
    "$env:LOCALAPPDATA\360WD",
    "$env:APPDATA\360safe",
    "$env:APPDATA\360Quarant",
    "$env:USERPROFILE\AppData\LocalLow\360WD"
)

$TARGET_SHORTCUTS = @(
    "$env:PUBLIC\Desktop\360*",
    "$env:USERPROFILE\Desktop\360*",
    "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\360*",
    "$env:ALLUSERSPROFILE\Microsoft\Windows\Start Menu\Programs\360*"
)

$TARGET_SERVICES = @(
    "360rp", "360sd", "Q360AMPPL", "ZhuDongFangYu", "360EntClientSvc"
)

$TARGET_PROCESSES = @(
    "360tray", "360Safe", "360rp", "360sd", "zhudongfangyu",
    "360AppLoader", "360DeskAna", "360leakfixer", "LiveUpdate360",
    "360netman", "360boxmain", "360EvtMgr", "360PatchMgr",
    "360ShellPro", "360SafeNotify", "ZhuDongFangYu"
)

$TARGET_REGISTRY = @(
    "HKLM:\SOFTWARE\360Safe",
    "HKLM:\SOFTWARE\360",
    "HKLM:\SOFTWARE\360WD",
    "HKLM:\SOFTWARE\WOW6432Node\360Safe",
    "HKLM:\SOFTWARE\WOW6432Node\360",
    "HKLM:\SOFTWARE\WOW6432Node\360WD",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\360safe",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\360zip",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\360safe",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\360zip",
    "HKCU:\SOFTWARE\360Safe",
    "HKCU:\SOFTWARE\360WD",
    "HKCU:\SOFTWARE\360"
)

# Driver residuals — 360 ships kernel drivers (.sys) that often leave
# renamed backups (.removed, .old, .sys.NNN) after uninstall. These sit
# in System32\drivers and are protected by TrustedInstaller — they need
# takeown + icacls before deletion.
$TARGET_DRIVER_RESIDUALS = @(
    "C:\Windows\System32\drivers\360AntiHacker64.removed",
    "C:\Windows\System32\drivers\360AntiHijack64.removed",
    "C:\Windows\System32\drivers\360AntiSteal64.removed",
    "C:\Windows\System32\drivers\360Box64.sys.736",
    "C:\Windows\System32\drivers\360FsFlt.sys.753",
    "C:\Windows\System32\drivers\360Hvm64.removed",
    "C:\Windows\System32\drivers\360netmon.old",
    "C:\Windows\System32\drivers\360qpesv64.sys.194",
    "C:\Windows\SysWOW64\360SoftMgr.cpl"
)

# Wildcard patterns to catch any unnamed 360 driver leftovers
# (e.g. versioned backups like *.sys.999, *.removed, *.old)
$TARGET_DRIVER_WILDCARDS = @(
    "C:\Windows\System32\drivers\360*.removed",
    "C:\Windows\System32\drivers\360*.old",
    "C:\Windows\System32\drivers\360*.sys.*",
    "C:\Windows\System32\drivers\360*.sys.bak",
    "C:\Windows\SysWOW64\drivers\360*.*",
    "C:\Windows\SysWOW64\360*.cpl",
    "C:\Windows\SysWOW64\360*.dll",
    "C:\Windows\System32\360*.cpl",
    "C:\Windows\System32\360*.dll"
)

# Scheduled tasks often left behind by 360 auto-update and maintenance
$TARGET_SCHEDULED_TASKS = @(
    "\360Safe",
    "\360WD",
    "\360TotalSecurity",
    "\360Speedup",
    "\360SoftMgr"
)

# Win32 API for MoveFileEx (reboot-delete)
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Win32File {
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern bool MoveFileEx(string lpExistingFileName, string lpNewFileName, int dwFlags);
}
"@ -ErrorAction SilentlyContinue

$MOVEFILE_DELAY_UNTIL_REBOOT = 0x4

# ============================================================
# HELPER FUNCTIONS
# ============================================================

function Write-Step {
    param([string]$Text, [string]$Color = "Cyan")
    Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] $Text" -ForegroundColor $Color
}

function Write-Ok {
    param([string]$Text)
    Write-Host "  + $Text" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Text)
    Write-Host "  ! $Text" -ForegroundColor Yellow
}

function Write-Fail {
    param([string]$Text)
    Write-Host "  - $Text" -ForegroundColor Red
}

function Write-Skip {
    param([string]$Text)
    Write-Host "  - $Text" -ForegroundColor DarkGray
}

function Invoke-ForceDelete {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $true }

    # Strip readonly/hidden/system attributes
    Get-ChildItem -Path $Path -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
        try { $_.Attributes = 'Normal' } catch { }
    }

    try {
        Remove-Item -Path $Path -Recurse -Force -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

function Invoke-RebootDelete {
    param([string]$Path)
    try {
        [Win32File]::MoveFileEx($Path, $null, $MOVEFILE_DELAY_UNTIL_REBOOT) | Out-Null
        # Check error
        $err = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()
        return ($err -eq 0)
    } catch {
        return $false
    }
}

# ============================================================
# PHASE 1: TERMINATE PROCESSES
# ============================================================
Write-Host "=" * 60 -ForegroundColor Yellow
Write-Host "  360 Security Guard - Complete Removal Tool" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Yellow

Write-Step "PHASE 1/8: Terminating 360 processes..."

$killed = 0
foreach ($name in $TARGET_PROCESSES) {
    $proc = Get-Process -Name $name -ErrorAction SilentlyContinue
    if ($proc) {
        try {
            Stop-Process -Name $name -Force -ErrorAction Stop
            Write-Ok "Killed: $name"
            $killed++
        } catch {
            Write-Fail "Cannot kill: $name (will retry after service stop)"
        }
    }
}

# Also catch any remaining processes with "360" in name
Get-Process | Where-Object { $_.ProcessName -like "*360*" -or $_.ProcessName -like "*zhudong*" } | ForEach-Object {
    try {
        Stop-Process -Id $_.Id -Force -ErrorAction Stop
        Write-Ok "Killed: $($_.ProcessName) (PID $($_.Id))"
        $killed++
    } catch { }
}

if ($killed -eq 0) { Write-Skip "No 360 processes running" }
else { Write-Ok "Terminated $killed process(es)" }
Start-Sleep -Seconds 2

# ============================================================
# PHASE 2: SERVICES
# ============================================================
Write-Step "PHASE 2/8: Stopping and deleting 360 services..."

$svcDone = 0
# Find all 360-related services
$foundServices = Get-Service | Where-Object { $_.Name -like "*360*" -or $_.DisplayName -like "*360*" -or $_.Name -like "*ZhuDong*" }

foreach ($svc in $foundServices) {
    # Stop
    if ($svc.Status -ne 'Stopped') {
        try {
            Stop-Service -Name $svc.Name -Force -ErrorAction Stop
            Write-Ok "Stopped service: $($svc.Name)"
        } catch {
            Write-Warn "Failed to stop: $($svc.Name)"
        }
    }
    # Delete
    try {
        $result = sc.exe delete $svc.Name 2>&1
        if ($LASTEXITCODE -eq 0 -or $result -match "success") {
            Write-Ok "Deleted service: $($svc.Name)"
            $svcDone++
        } else {
            Write-Warn "Service delete pending: $($svc.Name)"
        }
    } catch {
        Write-Warn "Service delete failed: $($svc.Name)"
    }
}

# Also try named services explicitly
foreach ($name in $TARGET_SERVICES) {
    $svc = Get-Service -Name $name -ErrorAction SilentlyContinue
    if ($svc) {
        Stop-Service -Name $name -Force -ErrorAction SilentlyContinue
        sc.exe delete $name 2>$null | Out-Null
        Write-Ok "Deleted service: $name"
        $svcDone++
    }
}

if ($svcDone -eq 0) { Write-Skip "No 360 services found" }
else { Write-Ok "Handled $svcDone service(s)" }

Start-Sleep -Seconds 1

# Retry killing processes after service stop
Get-Process | Where-Object { $_.ProcessName -like "*360*" -or $_.ProcessName -like "*zhudong*" } | ForEach-Object {
    try {
        Stop-Process -Id $_.Id -Force -ErrorAction Stop
        Write-Ok "Killed (retry): $($_.ProcessName)"
    } catch { }
}

# ============================================================
# PHASE 3: UNREGISTER DLLs
# ============================================================
Write-Step "PHASE 3/8: Unregistering 360 DLLs..."

$dllCount = 0
$dllPaths = @()
if (Test-Path "C:\Program Files (x86)\360") {
    $dllPaths = Get-ChildItem -Path "C:\Program Files (x86)\360" -Recurse -Filter "*.dll" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
    $dllPaths += Get-ChildItem -Path "C:\Program Files (x86)\360" -Recurse -Filter "*.ocx" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
}

foreach ($dll in $dllPaths) {
    try {
        regsvr32.exe /s /u $dll 2>$null
        $dllCount++
    } catch { }
}

if ($dllCount -gt 0) {
    Write-Ok "Unregistered $dllCount DLL(s)"
} else {
    Write-Skip "No DLLs to unregister"
}

Start-Sleep -Seconds 1

# ============================================================
# PHASE 4: RUN OFFICIAL UNINSTALLER
# ============================================================
Write-Step "PHASE 4/8: Running official uninstaller..."

$uninstPath = "C:\Program Files (x86)\360\360Safe\uninst.exe"
if (Test-Path $uninstPath) {
    Write-Ok "Found: $uninstPath"
    try {
        $proc = Start-Process -FilePath $uninstPath -ArgumentList "/S" -Wait -NoNewWindow -PassThru
        Write-Ok "Uninstaller completed (exit code: $($proc.ExitCode))"
    } catch {
        Write-Warn "Uninstaller failed: $_"
    }
} else {
    Write-Skip "Official uninstaller not found, skipping"
}

Start-Sleep -Seconds 3

# ============================================================
# PHASE 5: DELETE FILES & DIRECTORIES
# ============================================================
Write-Step "PHASE 5/8: Deleting 360 files..."

$deletedCount = 0
$lockedCount = 0
$allTargetPaths = $TARGET_DIRS + $TARGET_APPDATA

foreach ($p in $allTargetPaths) {
    try {
        $expPath = [Environment]::ExpandEnvironmentVariables($p)
    } catch {
        $expPath = $p
    }

    if (-not (Test-Path $expPath)) {
        Write-Skip "Already gone: $expPath"
        continue
    }

    # Try direct delete first
    if (Invoke-ForceDelete -Path $expPath) {
        Write-Ok "Deleted: $expPath"
        $deletedCount++
    } else {
        # Direct delete failed — some files are locked.
        # Strategy: strip attributes first, then bulk-delete with cmd (which
        # skips locked files and keeps going), then schedule only the leftovers
        # for reboot-delete. This avoids the O(n) MoveFileEx registry flood
        # that made the old per-file loop hang for minutes on large installs.

        # 1) Strip all attributes so nothing is read-only/hidden/system
        Get-ChildItem -Path $expPath -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
            try { $_.Attributes = 'Normal' } catch { }
        }

        # 2) Bulk delete via cmd — continues past locked files
        $null = cmd /c "rmdir /s /q `"$expPath`"" 2>&1

        if (-not (Test-Path $expPath)) {
            # All gone after bulk pass
            Write-Ok "Deleted (bulk): $expPath"
            $deletedCount++
        } else {
            # 3) Only locked files remain — schedule them + the directory
            $leftovers = @(Get-ChildItem -Path $expPath -Recurse -Force -ErrorAction SilentlyContinue)
            Write-Warn "Locked, reboot-delete: $expPath ($($leftovers.Count) items)"

            foreach ($f in $leftovers) {
                # One last try; if still locked, schedule for reboot
                try { Remove-Item -Path $f.FullName -Force -ErrorAction Stop } catch {
                    Invoke-RebootDelete -Path $f.FullName | Out-Null
                }
            }
            Invoke-RebootDelete -Path $expPath | Out-Null
            $lockedCount++
        }
    }
}

# ============================================================
# PHASE 6: DRIVER RESIDUALS (System32\drivers)
# ============================================================
Write-Step "PHASE 6/8: Removing driver residuals (System32\\drivers)..."

$driverCleaned = 0
$driverLocked = 0

# --- A) Known driver residual files ---
foreach ($f in $TARGET_DRIVER_RESIDUALS) {
    if (-not (Test-Path $f)) {
        Write-Skip "Already gone: $f"
        continue
    }
    try {
        # Strip attributes
        $item = Get-Item -Path $f -Force -ErrorAction Stop
        $item.Attributes = 'Normal'
        # Attempt direct delete
        Remove-Item -Path $f -Force -ErrorAction Stop
        Write-Ok "Deleted: $f"
        $driverCleaned++
    } catch {
        # TrustedInstaller protection — take ownership, grant rights, retry
        try {
            $null = takeown.exe /f $f 2>&1
            $null = icacls.exe $f /grant "Administrators:F" 2>&1
            Remove-Item -Path $f -Force -ErrorAction Stop
            Write-Ok "Deleted (elevated): $f"
            $driverCleaned++
        } catch {
            # Still locked — schedule for reboot
            if (Invoke-RebootDelete -Path $f) {
                Write-Warn "Reboot-required: $f"
                $driverLocked++
            } else {
                Write-Fail "Cannot delete: $f"
            }
        }
    }
}

# --- B) Wildcard sweep: catch any unnamed 360 driver leftovers ---
foreach ($pattern in $TARGET_DRIVER_WILDCARDS) {
    $matches = Get-Item -Path $pattern -ErrorAction SilentlyContinue
    if (-not $matches) { continue }
    foreach ($item in $matches) {
        try {
            $null = takeown.exe /f $item.FullName 2>&1
            $null = icacls.exe $item.FullName /grant "Administrators:F" 2>&1
            Remove-Item -Path $item.FullName -Force -ErrorAction Stop
            Write-Ok "Deleted (wildcard): $($item.FullName)"
            $driverCleaned++
        } catch {
            if (Invoke-RebootDelete -Path $item.FullName) {
                Write-Warn "Reboot-required: $($item.FullName)"
                $driverLocked++
            } else {
                Write-Fail "Cannot delete: $($item.FullName)"
            }
        }
    }
}

if ($driverCleaned -eq 0 -and $driverLocked -eq 0) { Write-Skip "No 360 driver residuals found" }
else {
    if ($driverCleaned -gt 0) { Write-Ok "Deleted $driverCleaned driver residual(s)" }
    if ($driverLocked -gt 0) { Write-Warn "$driverLocked driver file(s) scheduled for reboot-delete" }
}

# ============================================================
# PHASE 7: SCHEDULED TASKS & FIREWALL RULES
# ============================================================
Write-Step "PHASE 7/8: Removing scheduled tasks and firewall rules..."

# --- Scheduled Tasks ---
$taskCleaned = 0
# By folder
foreach ($taskPath in $TARGET_SCHEDULED_TASKS) {
    try {
        $null = schtasks.exe /delete /tn $taskPath /f 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Ok "Deleted task: $taskPath"
            $taskCleaned++
        }
    } catch { }
}
# By name wildcard (catch any task with 360 in the path)
$taskList = schtasks.exe /query /fo csv /v 2>$null | ConvertFrom-Csv -ErrorAction SilentlyContinue
if ($taskList) {
    $taskList | Where-Object { $_.TaskName -like "*360*" -or $_.TaskName -like "*ZhuDong*" } | ForEach-Object {
        $tn = $_.TaskName
        try {
            $null = schtasks.exe /delete /tn $tn /f 2>&1
            Write-Ok "Deleted task: $tn"
            $taskCleaned++
        } catch { }
    }
}
if ($taskCleaned -eq 0) { Write-Skip "No 360 scheduled tasks found" }
else { Write-Ok "Cleaned $taskCleaned scheduled task(s)" }

# --- Firewall Rules ---
$fwCleaned = 0
$fwRules = netsh.exe advfirewall firewall show rule name=all dir=in 2>$null |
    Select-String -Pattern "360" -SimpleMatch
$fwRules += netsh.exe advfirewall firewall show rule name=all dir=out 2>$null |
    Select-String -Pattern "360" -SimpleMatch

if ($fwRules) {
    # Extract rule names and delete them
    $ruleNames = $fwRules | ForEach-Object {
        if ($_ -match 'Rule Name:\s*(.+)') { $matches[1].Trim() }
    } | Where-Object { $_ } | Sort-Object -Unique

    foreach ($rule in $ruleNames) {
        try {
            $null = netsh.exe advfirewall firewall delete rule name="$rule" 2>&1
            Write-Ok "Deleted firewall rule: $rule"
            $fwCleaned++
        } catch {
            Write-Fail "Cannot delete firewall rule: $rule"
        }
    }
}
if ($fwCleaned -eq 0) { Write-Skip "No 360 firewall rules found" }
else { Write-Ok "Cleaned $fwCleaned firewall rule(s)" }

# ============================================================
# PHASE 8: CLEAN SHORTCUTS & REGISTRY
# ============================================================
Write-Step "PHASE 8/8: Cleaning shortcuts and registry..."

# Shortcuts
$shortcutCleaned = 0
foreach ($sp in $TARGET_SHORTCUTS) {
    try {
        $expSP = [Environment]::ExpandEnvironmentVariables($sp)
    } catch {
        $expSP = $sp
    }
    Get-Item -Path $expSP -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction Stop
            Write-Ok "Deleted shortcut: $($_.FullName)"
            $shortcutCleaned++
        } catch {
            Write-Fail "Cannot delete: $($_.FullName)"
        }
    }
}
if ($shortcutCleaned -eq 0) { Write-Skip "No 360 shortcuts found" }

# Registry
$regCleaned = 0
foreach ($rp in $TARGET_REGISTRY) {
    if (Test-Path $rp) {
        try {
            Remove-Item -Path $rp -Recurse -Force -ErrorAction Stop
            Write-Ok "Deleted registry: $rp"
            $regCleaned++
        } catch {
            Write-Fail "Registry delete failed: $rp"
        }
    }
}
if ($regCleaned -eq 0) { Write-Skip "No 360 registry entries found" }
else { Write-Ok "Cleaned $regCleaned registry entries" }

# ============================================================
# SUMMARY REPORT
# ============================================================
Write-Host "`n" -NoNewline
Write-Host "=" * 60 -ForegroundColor Yellow
Write-Host "  REMOVAL COMPLETE" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Yellow

# Final verification
$pfRemaining = 0
if (Test-Path "C:\Program Files (x86)\360") {
    $pfRemaining = (Get-ChildItem -Path "C:\Program Files (x86)\360" -Recurse -Force -ErrorAction SilentlyContinue).Count
}

$pdRemaining = @()
foreach ($d in $TARGET_DIRS) {
    if (Test-Path $d) { $pdRemaining += $d }
}
foreach ($d in $TARGET_APPDATA) {
    $exp = $d
    try { $exp = [Environment]::ExpandEnvironmentVariables($d) } catch { }
    if (Test-Path $exp) { $pdRemaining += $exp }
}

$svcRemaining = (Get-Service | Where-Object { $_.Name -like "*360*" -or $_.DisplayName -like "*360*" }).Count

# Check driver residuals
$driverRemaining = @()
foreach ($f in $TARGET_DRIVER_RESIDUALS) {
    if (Test-Path $f) { $driverRemaining += $f }
}
foreach ($w in $TARGET_DRIVER_WILDCARDS) {
    $found = Get-Item -Path $w -ErrorAction SilentlyContinue
    if ($found) { $driverRemaining += $found.FullName }
}

# Check scheduled tasks
$taskRemaining = (schtasks.exe /query /fo csv 2>$null | Select-String "360" -SimpleMatch).Count

Write-Host ""
Write-Host "  Status after cleanup:" -ForegroundColor White
Write-Host "  ----------------------------------------" -ForegroundColor DarkGray

if ($pfRemaining -eq 0 -and $pdRemaining.Count -eq 0) {
    Write-Host "  [OK] All 360 directories removed" -ForegroundColor Green
} else {
    if ($pfRemaining -gt 0) {
        Write-Host "  [..] $pfRemaining files in Program Files (reboot-pending)" -ForegroundColor Yellow
    }
    foreach ($d in $pdRemaining) {
        Write-Host "  [..] $d (reboot-pending)" -ForegroundColor Yellow
    }
}

if ($svcRemaining -eq 0) {
    Write-Host "  [OK] All 360 services removed" -ForegroundColor Green
} else {
    Write-Host "  [..] $svcRemaining service(s) remain (reboot-pending)" -ForegroundColor Yellow
}

if ($driverRemaining.Count -eq 0) {
    Write-Host "  [OK] All 360 driver residuals removed" -ForegroundColor Green
} else {
    Write-Host "  [..] $($driverRemaining.Count) driver residual(s) remain (reboot-pending)" -ForegroundColor Yellow
    foreach ($d in $driverRemaining) {
        Write-Host "       $d" -ForegroundColor DarkGray
    }
}

if ($taskRemaining -eq 0) {
    Write-Host "  [OK] No 360 scheduled tasks found" -ForegroundColor Green
} else {
    Write-Host "  [..] $taskRemaining scheduled task(s) may remain" -ForegroundColor Yellow
}

$procRemaining = (Get-Process | Where-Object { $_.ProcessName -like "*360*" }).Count
if ($procRemaining -eq 0) {
    Write-Host "  [OK] No 360 processes running" -ForegroundColor Green
} else {
    Write-Host "  [!!] $procRemaining process(es) still running!" -ForegroundColor Red
}

# Check PendingFileRenameOperations
try {
    $regVal = Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager" -Name "PendingFileRenameOperations" -ErrorAction SilentlyContinue
    if ($regVal) {
        $pendingCount = ($regVal.'PendingFileRenameOperations' | ForEach-Object { [char]$_ }) -join '' -split "`0" | Where-Object { $_ -like "*360*" } | Measure-Object | Select-Object -ExpandProperty Count
        if ($pendingCount -gt 0) {
            Write-Host "  [..] $pendingCount file(s) scheduled for reboot-delete" -ForegroundColor Yellow
        }
    }
} catch { }

Write-Host "  ----------------------------------------" -ForegroundColor DarkGray

if ($pfRemaining -gt 0 -or $lockedCount -gt 0 -or $pdRemaining.Count -gt 0 -or $svcRemaining -gt 0 -or $driverRemaining.Count -gt 0) {
    Write-Host "`n  ACTION REQUIRED: Restart your computer to complete removal." -ForegroundColor Cyan
    Write-Host "  Locked files, driver residuals, and services will be cleaned during reboot." -ForegroundColor Cyan
} else {
    Write-Host "`n  360 Security Guard has been completely removed!" -ForegroundColor Green
}

Write-Host ""
Read-Host "Press Enter to exit"
