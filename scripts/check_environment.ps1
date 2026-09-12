# ENMA PoC Environment Checker
# scripts\check_environment.ps1

$ErrorActionPreference = "SilentlyContinue"

$okCount = 0
$warnCount = 0
$ngCount = 0

function Write-CheckResult {
    param(
        [string]$Status,
        [string]$Message
    )

    switch ($Status) {
        "OK" {
            $script:okCount++
            Write-Host "[OK]   $Message" -ForegroundColor Green
        }
        "WARN" {
            $script:warnCount++
            Write-Host "[WARN] $Message" -ForegroundColor Yellow
        }
        "NG" {
            $script:ngCount++
            Write-Host "[NG]   $Message" -ForegroundColor Red
        }
        "INFO" {
            Write-Host "[INFO] $Message" -ForegroundColor Cyan
        }
    }
}

Write-Host ""
Write-Host "=================================================="
Write-Host " ENMA PoC Environment Check"
Write-Host "=================================================="
Write-Host ""

# --------------------------------------------------
# Project root
# --------------------------------------------------

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

Write-CheckResult "INFO" "Project Root: $projectRoot"

# --------------------------------------------------
# Git
# --------------------------------------------------

$gitCommand = Get-Command git -ErrorAction SilentlyContinue

if ($gitCommand) {
    $gitVersion = git --version
    Write-CheckResult "OK" $gitVersion
}
else {
    Write-CheckResult "NG" "Git is not available in PATH"
}

# --------------------------------------------------
# Python Launcher
# --------------------------------------------------

$pyCommand = Get-Command py -ErrorAction SilentlyContinue

if ($pyCommand) {

    Write-CheckResult "OK" "Python Launcher (py.exe)"

    $installedVersions = py -0p 2>&1

    Write-Host ""
    Write-Host "Installed Python versions:"
    $installedVersions | ForEach-Object {
        Write-Host "  $_"
    }
    Write-Host ""

}
else {
    Write-CheckResult "WARN" "Python Launcher (py.exe) is not available"
}

# --------------------------------------------------
# Python 3.11
# --------------------------------------------------

if ($pyCommand) {

    $python311Version = py -3.11 --version 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-CheckResult "OK" $python311Version
    }
    else {
        Write-CheckResult "NG" "Python 3.11 is not installed"
    }

}
else {

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue

    if ($pythonCommand) {

        $pythonVersion = python --version 2>&1

        if ($pythonVersion -match "Python 3\.11") {
            Write-CheckResult "OK" $pythonVersion
        }
        else {
            Write-CheckResult "WARN" "Python found, but Python 3.11 was not confirmed: $pythonVersion"
        }

    }
    else {
        Write-CheckResult "NG" "Python is not available"
    }
}

# --------------------------------------------------
# ExecutionPolicy
# --------------------------------------------------

$executionPolicy = Get-ExecutionPolicy -Scope CurrentUser

if ($executionPolicy -in @("RemoteSigned", "Unrestricted", "Bypass")) {
    Write-CheckResult "OK" "ExecutionPolicy (CurrentUser): $executionPolicy"
}
else {
    Write-CheckResult "WARN" "ExecutionPolicy (CurrentUser): $executionPolicy"
}

# --------------------------------------------------
# Virtual Environment
# --------------------------------------------------

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (Test-Path $venvPython) {

    $venvVersion = & $venvPython --version 2>&1
    Write-CheckResult "OK" "Virtual Environment (.venv) - $venvVersion"

}
else {
    Write-CheckResult "WARN" "Virtual Environment (.venv) not found"
}

# --------------------------------------------------
# IfcOpenShell
# --------------------------------------------------

if (Test-Path $venvPython) {

    $ifcVersion = & $venvPython -c "import ifcopenshell; print(ifcopenshell.version)" 2>$null

    if ($LASTEXITCODE -eq 0 -and $ifcVersion) {
        Write-CheckResult "OK" "IfcOpenShell $ifcVersion"
    }
    else {
        Write-CheckResult "WARN" "IfcOpenShell is not installed in .venv"
    }

}
else {
    Write-CheckResult "WARN" "IfcOpenShell check skipped (.venv not found)"
}

# --------------------------------------------------
# Git repository / remote / user settings
# --------------------------------------------------

Push-Location $projectRoot

$insideGitRepository = git rev-parse --is-inside-work-tree 2>$null

if ($insideGitRepository -eq "true") {

    Write-CheckResult "OK" "Git Repository"

    $origin = git remote get-url origin 2>$null

    if ($origin) {
        Write-CheckResult "OK" "GitHub Remote: $origin"
    }
    else {
        Write-CheckResult "WARN" "Git remote 'origin' is not configured"
    }

    $gitUserName = git config user.name 2>$null

    if ($gitUserName) {
        Write-CheckResult "OK" "Git user.name: $gitUserName"
    }
    else {
        Write-CheckResult "WARN" "Git user.name is not configured"
    }

    $gitUserEmail = git config user.email 2>$null

    if ($gitUserEmail) {
        Write-CheckResult "OK" "Git user.email: $gitUserEmail"
    }
    else {
        Write-CheckResult "WARN" "Git user.email is not configured"
    }

}
else {
    Write-CheckResult "NG" "This directory is not a Git repository"
}

Pop-Location

# --------------------------------------------------
# Summary
# --------------------------------------------------

Write-Host ""
Write-Host "--------------------------------------------------"
Write-Host "Result: $okCount OK / $warnCount WARN / $ngCount NG"
Write-Host "--------------------------------------------------"
Write-Host ""