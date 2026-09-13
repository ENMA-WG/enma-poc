# ENMA PoC Environment Checker
# scripts\check_environment.ps1
#
# Version : 0.2
# Updated : 2026-09-13
#
# This script checks the local Windows development environment
# for the ENMA-WG PoC project.
#
# The script is designed to work regardless of drive letter:
#   C:\ENMA-WG\enma-poc
#   D:\ENMA-WG\enma-poc
#   G:\ENMA-WG\enma-poc
#
# Run from the repository root:
#   .\scripts\check_environment.ps1

$ErrorActionPreference = "SilentlyContinue"

# --------------------------------------------------
# Expected environment
# --------------------------------------------------

$scriptVersion = "0.2"
$lastUpdated = "2026-09-13"

$expectedPythonVersion = "3.11.9"
$expectedIfcOpenShellVersion = "0.8.5"
$expectedRepositoryUrl = "https://github.com/ENMA-WG/enma-poc.git"

# --------------------------------------------------
# Counters
# --------------------------------------------------

$okCount = 0
$warnCount = 0
$ngCount = 0

# --------------------------------------------------
# Helper functions
# --------------------------------------------------

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


function Convert-ToSingleLine {
    param(
        $Value
    )

    if ($null -eq $Value) {
        return ""
    }

    return (($Value | Out-String).Trim())
}

# --------------------------------------------------
# Header
# --------------------------------------------------

Write-Host ""
Write-Host "=================================================="
Write-Host " ENMA PoC Environment Check"
Write-Host " Version $scriptVersion ($lastUpdated)"
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

Write-Host ""
Write-Host "--- System / Tools ---"
Write-Host ""

$gitCommand = Get-Command git -ErrorAction SilentlyContinue
$gitAvailable = $false

if ($gitCommand) {

    $gitVersion = git --version 2>&1
    $gitVersion = Convert-ToSingleLine $gitVersion

    if ($LASTEXITCODE -eq 0) {
        Write-CheckResult "OK" $gitVersion
        $gitAvailable = $true
    }
    else {
        Write-CheckResult "NG" "Git command was found but could not be executed"
    }

}
else {
    Write-CheckResult "NG" "Git is not available in PATH"
}

# --------------------------------------------------
# Git Credential Manager
# --------------------------------------------------

if ($gitAvailable) {

    $gcmVersion = git credential-manager --version 2>&1
    $gcmExitCode = $LASTEXITCODE
    $gcmVersion = Convert-ToSingleLine $gcmVersion

    if ($gcmExitCode -eq 0 -and $gcmVersion) {
        Write-CheckResult "OK" "Git Credential Manager $gcmVersion"
    }
    else {
        Write-CheckResult "WARN" "Git Credential Manager was not confirmed"
    }

}
else {
    Write-CheckResult "INFO" "Git Credential Manager check skipped (Git not available)"
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
# Python 3.11 / expected Python version
# --------------------------------------------------

if ($pyCommand) {

    $python311Version = py -3.11 --version 2>&1
    $python311ExitCode = $LASTEXITCODE
    $python311Version = Convert-ToSingleLine $python311Version

    if ($python311ExitCode -eq 0) {

        if ($python311Version -eq "Python $expectedPythonVersion") {
            Write-CheckResult "OK" $python311Version
        }
        elseif ($python311Version -match "^Python 3\.11\.") {
            Write-CheckResult "WARN" "$python311Version found; expected Python $expectedPythonVersion"
        }
        else {
            Write-CheckResult "NG" "Unexpected Python version: $python311Version"
        }

    }
    else {
        Write-CheckResult "NG" "Python 3.11 is not installed"
    }

}
else {

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue

    if ($pythonCommand) {

        $pythonVersion = python --version 2>&1
        $pythonExitCode = $LASTEXITCODE
        $pythonVersion = Convert-ToSingleLine $pythonVersion

        if ($pythonExitCode -eq 0) {

            if ($pythonVersion -eq "Python $expectedPythonVersion") {
                Write-CheckResult "OK" $pythonVersion
            }
            elseif ($pythonVersion -match "^Python 3\.11\.") {
                Write-CheckResult "WARN" "$pythonVersion found; expected Python $expectedPythonVersion"
            }
            else {
                Write-CheckResult "WARN" "Python found, but Python 3.11 was not confirmed: $pythonVersion"
            }

        }
        else {
            Write-CheckResult "NG" "Python command could not be executed"
        }

    }
    else {
        Write-CheckResult "NG" "Python is not available"
    }
}

# --------------------------------------------------
# PowerShell Execution Policy
# --------------------------------------------------

$effectiveExecutionPolicy = Get-ExecutionPolicy
$currentUserExecutionPolicy = Get-ExecutionPolicy -Scope CurrentUser

if ($effectiveExecutionPolicy -in @("RemoteSigned", "Unrestricted", "Bypass")) {

    Write-CheckResult "OK" "ExecutionPolicy: $effectiveExecutionPolicy (CurrentUser: $currentUserExecutionPolicy)"

}
else {

    Write-CheckResult "WARN" "ExecutionPolicy: $effectiveExecutionPolicy (CurrentUser: $currentUserExecutionPolicy)"

}

# --------------------------------------------------
# Python virtual environment
# --------------------------------------------------

Write-Host ""
Write-Host "--- Python Environment ---"
Write-Host ""

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$venvExists = Test-Path $venvPython

if ($venvExists) {

    $venvVersion = & $venvPython --version 2>&1
    $venvExitCode = $LASTEXITCODE
    $venvVersion = Convert-ToSingleLine $venvVersion

    if ($venvExitCode -eq 0) {

        if ($venvVersion -eq "Python $expectedPythonVersion") {
            Write-CheckResult "OK" "Virtual Environment (.venv) - $venvVersion"
        }
        elseif ($venvVersion -match "^Python 3\.11\.") {
            Write-CheckResult "WARN" "Virtual Environment (.venv) - $venvVersion; expected Python $expectedPythonVersion"
        }
        else {
            Write-CheckResult "NG" "Virtual Environment (.venv) uses unexpected version: $venvVersion"
        }

    }
    else {
        Write-CheckResult "NG" "Virtual Environment (.venv) Python could not be executed"
    }

}
else {
    Write-CheckResult "WARN" "Virtual Environment (.venv) not found"
}

# --------------------------------------------------
# IfcOpenShell
# --------------------------------------------------

if ($venvExists) {

    $ifcVersion = & $venvPython -c "import ifcopenshell; print(ifcopenshell.version)" 2>$null
    $ifcExitCode = $LASTEXITCODE
    $ifcVersion = Convert-ToSingleLine $ifcVersion

    if ($ifcExitCode -eq 0 -and $ifcVersion) {

        if ($ifcVersion -eq $expectedIfcOpenShellVersion) {
            Write-CheckResult "OK" "IfcOpenShell $ifcVersion"
        }
        else {
            Write-CheckResult "WARN" "IfcOpenShell $ifcVersion found; expected $expectedIfcOpenShellVersion"
        }

    }
    else {
        Write-CheckResult "WARN" "IfcOpenShell is not installed in .venv"
    }

}
else {
    Write-CheckResult "WARN" "IfcOpenShell check skipped (.venv not found)"
}

# --------------------------------------------------
# Git repository
# --------------------------------------------------

Write-Host ""
Write-Host "--- Git Repository ---"
Write-Host ""

if ($gitAvailable) {

    Push-Location $projectRoot

    try {

        $insideGitRepository = git rev-parse --is-inside-work-tree 2>$null
        $insideGitRepository = Convert-ToSingleLine $insideGitRepository

        if ($insideGitRepository -eq "true") {

            Write-CheckResult "OK" "Git Repository"

            # --------------------------------------------------
            # Remote origin
            # --------------------------------------------------

            $origin = git remote get-url origin 2>$null
            $origin = Convert-ToSingleLine $origin

            if ($origin) {

                if ($origin -eq $expectedRepositoryUrl) {
                    Write-CheckResult "OK" "GitHub Remote: $origin"
                }
                else {
                    Write-CheckResult "WARN" "Git remote origin is $origin; expected $expectedRepositoryUrl"
                }

            }
            else {
                Write-CheckResult "WARN" "Git remote 'origin' is not configured"
            }

            # --------------------------------------------------
            # Current branch
            # --------------------------------------------------

            $currentBranch = git rev-parse --abbrev-ref HEAD 2>$null
            $currentBranch = Convert-ToSingleLine $currentBranch

            if ($currentBranch) {
                Write-CheckResult "OK" "Current branch: $currentBranch"
            }
            else {
                Write-CheckResult "WARN" "Current Git branch could not be determined"
            }

            # --------------------------------------------------
            # Tracking branch
            # --------------------------------------------------

            $upstream = git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null
            $upstreamExitCode = $LASTEXITCODE
            $upstream = Convert-ToSingleLine $upstream

            if ($upstreamExitCode -eq 0 -and $upstream) {

                Write-CheckResult "OK" "Tracking branch: $upstream"

                # --------------------------------------------------
                # Ahead / behind
                #
                # NOTE:
                # This compares the local repository with the locally
                # stored remote-tracking branch.
                # It does NOT perform "git fetch".
                # --------------------------------------------------

                $syncStatus = git rev-list --left-right --count "$upstream...HEAD" 2>$null
                $syncExitCode = $LASTEXITCODE
                $syncStatus = Convert-ToSingleLine $syncStatus

                if ($syncExitCode -eq 0 -and $syncStatus) {

                    $parts = $syncStatus -split '\s+'

                    if ($parts.Count -ge 2) {

                        $behindCount = [int]$parts[0]
                        $aheadCount = [int]$parts[1]

                        if ($behindCount -eq 0 -and $aheadCount -eq 0) {

                            Write-CheckResult "OK" "Local branch matches $upstream"

                        }
                        elseif ($behindCount -eq 0 -and $aheadCount -gt 0) {

                            Write-CheckResult "WARN" "Local branch is ahead of $upstream by $aheadCount commit(s)"

                        }
                        elseif ($behindCount -gt 0 -and $aheadCount -eq 0) {

                            Write-CheckResult "WARN" "Local branch is behind $upstream by $behindCount commit(s)"

                        }
                        else {

                            Write-CheckResult "WARN" "Local branch differs from ${upstream}: ahead $aheadCount / behind $behindCount commit(s)"

                        }

                    }
                    else {
                        Write-CheckResult "WARN" "Could not interpret Git branch synchronization status"
                    }

                }
                else {
                    Write-CheckResult "WARN" "Could not determine Git branch synchronization status"
                }

            }
            else {
                Write-CheckResult "WARN" "No tracking branch is configured for $currentBranch"
            }

            # --------------------------------------------------
            # Git user.name
            # --------------------------------------------------

            $gitUserName = git config user.name 2>$null
            $gitUserName = Convert-ToSingleLine $gitUserName

            if ($gitUserName) {
                Write-CheckResult "OK" "Git user.name: $gitUserName"
            }
            else {
                Write-CheckResult "WARN" "Git user.name is not configured"
            }

            # --------------------------------------------------
            # Git user.email
            # --------------------------------------------------

            $gitUserEmail = git config user.email 2>$null
            $gitUserEmail = Convert-ToSingleLine $gitUserEmail

            if ($gitUserEmail) {
                Write-CheckResult "OK" "Git user.email: $gitUserEmail"
            }
            else {
                Write-CheckResult "WARN" "Git user.email is not configured"
            }

            Write-CheckResult "INFO" "GitHub repository write permission is not tested by this script."

        }
        else {
            Write-CheckResult "NG" "This directory is not a Git repository"
        }

    }
    finally {
        Pop-Location
    }

}
else {
    Write-CheckResult "INFO" "Git repository checks skipped (Git not available)"
}

# --------------------------------------------------
# Summary
# --------------------------------------------------

Write-Host ""
Write-Host "--------------------------------------------------"
Write-Host "Result: $okCount OK / $warnCount WARN / $ngCount NG"
Write-Host "--------------------------------------------------"

if ($ngCount -eq 0 -and $warnCount -eq 0) {

    Write-Host ""
    Write-Host "[READY] ENMA PoC development environment is ready." -ForegroundColor Green

}
elseif ($ngCount -eq 0) {

    Write-Host ""
    Write-Host "[READY WITH WARNINGS] Core environment checks passed." -ForegroundColor Yellow
    Write-Host "Review the WARN items above." -ForegroundColor Yellow

}
else {

    Write-Host ""
    Write-Host "[NOT READY] Environment setup requires attention." -ForegroundColor Red
    Write-Host "Resolve the NG items above and run this script again." -ForegroundColor Red

}

Write-Host ""