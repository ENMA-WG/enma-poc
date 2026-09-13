# ENMA-WG PoC Windows Development Environment Setup Guide

**Document version:** 0.3\
**Updated:** 2026-09-13\
**Target repository:** `ENMA-WG/enma-poc`

------------------------------------------------------------------------

## Revision History

  ------------------------------------------------------------------------
  Date                                       Version Changes
  --------------------- ---------------------------- ---------------------
  2026-09-11                                     0.1 Initial Windows
                                                     development
                                                     environment setup
                                                     guide.

  2026-09-12                                     0.2 Added support for
                                                     working folders on
                                                     different drives and
                                                     introduced the
                                                     environment
                                                     verification script.

  2026-09-13                                     0.3 Reorganized the setup
                                                     order based on actual
                                                     Windows PC tests.
                                                     Added GitHub
                                                     permission notes,
                                                     PowerShell
                                                     ExecutionPolicy
                                                     setup, initial/final
                                                     environment checks,
                                                     Git Credential
                                                     Manager checks, and
                                                     Git branch
                                                     synchronization
                                                     checks.
  ------------------------------------------------------------------------

------------------------------------------------------------------------

## 1. Overview

This document describes how to prepare a reproducible Windows
development environment for the ENMA-WG PoC project.

The same procedure is intended for company PCs, home PCs, notebook PCs,
and demonstration PCs.

The working drive is **not fixed**. For example, the project may be
placed under:

``` text
C:\ENMA-WG
D:\ENMA-WG
G:\ENMA-WG
```

In this guide, the parent working folder is written as:

``` text
<ENMA-WG>
```

After cloning the repository, commands should normally be executed from
the repository root:

``` text
<ENMA-WG>\enma-poc
```

Once you are in the repository root, use relative paths whenever
possible.

------------------------------------------------------------------------

## 2. Standard Environment

The standard ENMA-WG PoC environment is:

  Item                     Standard
  ------------------------ -------------------------------------------
  OS                       Windows 11
  PowerShell               Windows PowerShell / PowerShell
  Python                   3.11.9 (64-bit)
  Git                      Git for Windows
  Git Credential Manager   Included/recommended with Git for Windows
  IfcOpenShell             0.8.5
  Repository               `ENMA-WG/enma-poc`
  Virtual environment      `.venv`

Other Python versions may coexist on the same PC. The ENMA-WG virtual
environment should use Python 3.11.9.

------------------------------------------------------------------------

## 3. Install Git for Windows

Install Git for Windows if it is not already available.

After installation, open PowerShell and check:

``` powershell
git --version
```

Example:

``` text
git version 2.55.0.windows.5
```

Also check Git Credential Manager:

``` powershell
git credential-manager --version
```

If a version number is displayed, Git Credential Manager is available.

------------------------------------------------------------------------

## 4. Prepare the ENMA-WG Working Folder

Choose a suitable drive and create the parent folder.

Examples:

``` powershell
New-Item -ItemType Directory -Path "C:\ENMA-WG" -Force
Set-Location "C:\ENMA-WG"
```

or:

``` powershell
New-Item -ItemType Directory -Path "D:\ENMA-WG" -Force
Set-Location "D:\ENMA-WG"
```

or:

``` powershell
New-Item -ItemType Directory -Path "G:\ENMA-WG" -Force
Set-Location "G:\ENMA-WG"
```

From this point onward, this guide refers to the selected folder as:

``` text
<ENMA-WG>
```

Do not assume that every developer uses the same drive letter.

------------------------------------------------------------------------

## 5. Confirm GitHub Repository Access

The repository is:

``` text
https://github.com/ENMA-WG/enma-poc.git
```

The repository may be readable because it is public, but **read access
and write access are different**.

To push changes, the GitHub account used on the PC must have appropriate
repository or ENMA-WG organization permissions.

Important distinctions:

-   `git config user.name` and `git config user.email` identify the
    author of commits.
-   GitHub browser login / Git Credential Manager authentication
    identifies the GitHub account.
-   Repository or organization permissions determine whether that
    account can push.

A successful GitHub login does not by itself guarantee push permission.

------------------------------------------------------------------------

## 6. Clone the GitHub Repository

Move to the selected parent folder:

``` powershell
Set-Location "<ENMA-WG>"
```

Replace `<ENMA-WG>` with the actual path, for example:

``` powershell
Set-Location "D:\ENMA-WG"
```

Clone the repository:

``` powershell
git clone https://github.com/ENMA-WG/enma-poc.git
```

Move to the repository root:

``` powershell
Set-Location .\enma-poc
```

Confirm the location:

``` powershell
Get-Location
```

From this point onward, commands in this guide assume that PowerShell is
at:

``` text
<ENMA-WG>\enma-poc
```

For example:

``` text
PS D:\ENMA-WG\enma-poc>
```

Therefore, run the environment checker as:

``` powershell
.\scripts\check_environment.ps1
```

Do **not** add another `.\enma-poc\` when you are already inside the
repository root.

------------------------------------------------------------------------

## 7. Configure PowerShell Execution Policy

PowerShell may prevent `.ps1` scripts from running on a newly configured
PC.

Check the current settings:

``` powershell
Get-ExecutionPolicy -List
```

For a personal or otherwise permitted Windows environment, the
recommended user-level setting for this guide is:

``` powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Confirm the change:

``` powershell
Get-ExecutionPolicy -List
```

Example:

``` text
CurrentUser    RemoteSigned
```

If the PC is managed by an organization, follow the organization's
security policy. Do not override Group Policy or other administrative
security controls.

------------------------------------------------------------------------

## 8. Run the Initial Environment Check

The repository contains:

``` text
scripts\check_environment.ps1
```

From the repository root, run:

``` powershell
.\scripts\check_environment.ps1
```

The checker is designed to work regardless of whether the repository is
on `C:`, `D:`, `G:`, or another drive.

On a newly cloned PC, warnings such as the following are expected before
the Python environment has been created:

``` text
[WARN] Virtual Environment (.venv) not found
[WARN] IfcOpenShell check skipped (.venv not found)
```

`WARN` does not necessarily mean that the setup has failed. At this
stage it identifies items that still need to be configured.

The checker does not test GitHub repository write permission by
performing a push.

------------------------------------------------------------------------

## 9. Install and Confirm Python 3.11.9

Install Python 3.11.9 (64-bit) if necessary.

Check installed Python versions:

``` powershell
py -0p
```

Example:

``` text
-V:3.14 *    C:\...\python.exe
-V:3.11      C:\...\Python311\python.exe
```

Multiple Python versions may coexist.

Confirm Python 3.11:

``` powershell
py -3.11 --version
```

Expected result:

``` text
Python 3.11.9
```

The `py -3.11` form is used intentionally so that Python 3.11 is
selected even when another Python version is the system default.

------------------------------------------------------------------------

## 10. Create the Python Virtual Environment

Make sure PowerShell is in the repository root:

``` text
<ENMA-WG>\enma-poc
```

Create the virtual environment explicitly with Python 3.11:

``` powershell
py -3.11 -m venv .venv
```

Do not copy `.venv` from another PC. Each PC should create its own
virtual environment.

------------------------------------------------------------------------

## 11. Activate the Virtual Environment

Activate `.venv`:

``` powershell
.\.venv\Scripts\Activate.ps1
```

The prompt should now begin with:

``` text
(.venv)
```

For example:

``` text
(.venv) PS D:\ENMA-WG\enma-poc>
```

Confirm Python:

``` powershell
python --version
```

Expected result:

``` text
Python 3.11.9
```

Confirm the executable being used:

``` powershell
where.exe python
```

The first entry should point to:

``` text
<ENMA-WG>\enma-poc\.venv\Scripts\python.exe
```

------------------------------------------------------------------------

## 12. Upgrade pip

With `.venv` activated:

``` powershell
python -m pip install --upgrade pip
```

Check the installed pip version if required:

``` powershell
python -m pip --version
```

------------------------------------------------------------------------

## 13. Install ENMA-WG Python Dependencies

Install the standard dependencies from the repository:

``` powershell
python -m pip install -r requirements.txt
```

The current standard environment includes:

``` text
ifcopenshell==0.8.5
isodate==0.7.2
lark==1.3.1
numpy==2.4.6
python-dateutil==2.9.0.post0
shapely==2.1.2
six==1.17.0
typing_extensions==4.16.0
```

When project dependencies are intentionally added or updated, update
`requirements.txt` accordingly.

------------------------------------------------------------------------

## 14. Verify IfcOpenShell

Confirm that IfcOpenShell can be imported:

``` powershell
python -c "import ifcopenshell; print(ifcopenshell.version)"
```

Expected result:

``` text
0.8.5
```

Additional information can be checked with:

``` powershell
python -m pip show ifcopenshell
```

------------------------------------------------------------------------

## 15. Run the Final Environment Check

From the repository root:

``` powershell
.\scripts\check_environment.ps1
```

A fully configured and synchronized environment should normally show no
`NG` items and, when there are no outstanding warnings, a result similar
to:

``` text
Result: 14 OK / 0 WARN / 0 NG

[READY] ENMA PoC development environment is ready.
```

The exact number of checks may change as the checker is improved.

A result such as:

``` text
[WARN] Local branch is ahead of origin/main by 1 commit(s)
```

does not mean the Python environment is broken. It means that one or
more local commits have not yet been reflected in the locally known
remote-tracking branch.

The checker does not automatically run `git fetch` and does not
automatically run `git push`.

------------------------------------------------------------------------

## 16. Repository Structure

The repository is organized approximately as follows:

``` text
enma-poc/
├─ README.md
├─ LICENSE
├─ .gitignore
├─ requirements.txt
│
├─ src/
│  └─ Python source code
│
├─ tests/
│  └─ automated tests
│
├─ scripts/
│  └─ check_environment.ps1
│
├─ data/
│  └─ README.md
│
├─ output/
│  └─ generated CSV and PoC results
│
├─ docs/
│  └─ setup_windows.md
│
└─ presentation/
   └─ presentation materials
```

The `.venv` directory is local to each PC and must not be committed to
GitHub.

------------------------------------------------------------------------

## 17. Sample BIM Data

The ENMA-WG PoC uses BIM data published by Japan's Ministry of Land,
Infrastructure, Transport and Tourism (MLIT).

The original BIM data is not distributed through this repository.

See:

``` text
data\README.md
```

for information about obtaining and preparing sample BIM data.

Each developer should obtain the original data from the appropriate
official source and prepare the required IFC files locally.

Large BIM/IFC files should not be committed to the repository unless
redistribution and licensing conditions have been confirmed.

------------------------------------------------------------------------

## 18. Basic Git Workflow

Before starting work, move to the repository root:

``` powershell
Set-Location "<ENMA-WG>\enma-poc"
```

Activate the environment:

``` powershell
.\.venv\Scripts\Activate.ps1
```

Check the environment if necessary:

``` powershell
.\scripts\check_environment.ps1
```

Check repository status:

``` powershell
git status
```

Before beginning new work, synchronize with GitHub when appropriate:

``` powershell
git pull
```

After editing files:

``` powershell
git status
git add .
git commit -m "Describe the change"
git push
```

For collaborative development, feature branches and Pull Requests should
normally be used for substantial changes rather than working directly on
`main`.

Example:

``` powershell
git switch -c feature/pipe-extraction
```

After completing the work:

``` powershell
git add .
git commit -m "Add pipe extraction prototype"
git push -u origin feature/pipe-extraction
```

Then create a Pull Request on GitHub.

------------------------------------------------------------------------

## 19. GitHub Authentication on Windows

Git Credential Manager is recommended for HTTPS Git operations on
Windows.

Check it with:

``` powershell
git credential-manager --version
```

When `git push` requires authentication, Git Credential Manager may
display:

``` text
info: please complete authentication in your browser...
```

Complete authentication using the intended GitHub account.

Authentication and authorization are separate:

-   **Authentication**: proves which GitHub account is being used.
-   **Authorization**: determines whether that account may push to
    `ENMA-WG/enma-poc`.

------------------------------------------------------------------------

## 20. Common GitHub / Git Errors

### 20.1 Authentication error

Example:

``` text
remote: Invalid username or token.
Password authentication is not supported for Git operations.
fatal: Authentication failed
```

Confirm Git Credential Manager:

``` powershell
git credential-manager --version
```

Then retry the Git operation and complete browser authentication if
requested.

### 20.2 Permission denied / HTTP 403

Example:

``` text
remote: Permission to ENMA-WG/enma-poc.git denied to <GitHubUser>.
fatal: unable to access 'https://github.com/ENMA-WG/enma-poc.git/': The requested URL returned error: 403
```

This usually means that the GitHub account being used does not currently
have sufficient write permission to the repository.

Check:

1.  Which GitHub account is authenticated.
2.  Whether that account is a member/collaborator with suitable access.
3.  Whether an organization invitation is still pending.
4.  Whether the repository or team grants write access.

Do not confuse these settings with:

``` powershell
git config user.name
git config user.email
```

Those values identify commit authorship; they do not grant GitHub
repository permission.

------------------------------------------------------------------------

## 21. Starting Work on Another PC

For a new home PC, notebook PC, company PC, or demonstration PC:

1.  Install Git for Windows.
2.  Prepare a working folder such as `C:\ENMA-WG`, `D:\ENMA-WG`, or
    `G:\ENMA-WG`.
3.  Confirm GitHub access.
4.  Clone `ENMA-WG/enma-poc`.
5.  Configure PowerShell ExecutionPolicy as permitted.
6.  Run `.\scripts\check_environment.ps1`.
7.  Install/confirm Python 3.11.9.
8.  Create `.venv`.
9.  Activate `.venv`.
10. Install `requirements.txt`.
11. Verify IfcOpenShell.
12. Run `.\scripts\check_environment.ps1` again.

Do not copy `.venv` between PCs.

The Git repository and `requirements.txt` are the reproducible handoff
mechanism; `.venv` is machine-local.

------------------------------------------------------------------------

## 22. Deactivate the Virtual Environment

When finished:

``` powershell
deactivate
```

The `(.venv)` prefix disappears from the PowerShell prompt.

------------------------------------------------------------------------

## 23. Environment Verification Checklist

Before starting ENMA-WG PoC development on a PC, confirm:

-   Git is available.
-   Git Credential Manager is available.
-   The correct repository has been cloned.
-   PowerShell can execute the project scripts.
-   Python 3.11.9 is available.
-   `.venv` uses Python 3.11.9.
-   Dependencies from `requirements.txt` are installed.
-   IfcOpenShell 0.8.5 can be imported.
-   Git remote `origin` points to `ENMA-WG/enma-poc`.
-   Git `user.name` and `user.email` are configured.
-   The current branch and tracking branch are understood.
-   The GitHub account has the required permission before attempting to
    push.

The environment checker provides a quick summary:

``` powershell
.\scripts\check_environment.ps1
```

------------------------------------------------------------------------

## 24. Notes

This guide is intentionally designed to avoid machine-specific drive
assumptions.

Prefer commands relative to the repository root:

``` powershell
.\scripts\check_environment.ps1
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

rather than repeatedly embedding a specific drive such as `G:` in
commands.

The setup procedure should be tested on more than one Windows PC so that
hidden machine-specific assumptions can be found before other ENMA-WG
members use it.

------------------------------------------------------------------------

# 日本語版

# ENMA-WG PoC Windows 開発環境セットアップガイド

**文書バージョン:** 0.3\
**更新日:** 2026-09-13\
**対象リポジトリ:** `ENMA-WG/enma-poc`

------------------------------------------------------------------------

## 改訂履歴

  ------------------------------------------------------------------------------------------------------------------------------
  日付                                            版 主な変更内容
  --------------------- ---------------------------- ---------------------------------------------------------------------------
  2026-09-11                                     0.1 Windows開発環境セットアップ手順の初版を作成。

  2026-09-12                                     0.2 複数ドライブ上の作業フォルダに対応し、環境確認スクリプトを追加。

  2026-09-13                                     0.3 Windows実機試験を反映してセットアップ順序を再構成。GitHub権限、PowerShell
                                                     ExecutionPolicy、初回・最終環境チェック、Git Credential
                                                     Manager、Gitブランチ同期確認を追加。
  ------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------

## 1. 概要

本書は、ENMA-WG
PoCプロジェクトのWindows開発環境を、複数のPCで再現できるようにするためのセットアップ手順です。

会社PC、自宅PC、ノートPC、デモPCなどで、できるだけ同じ手順を利用することを目的としています。

作業ドライブは固定しません。例えば次のいずれでも構いません。

``` text
C:\ENMA-WG
D:\ENMA-WG
G:\ENMA-WG
```

本書では、この親フォルダを次のように表記します。

``` text
<ENMA-WG>
```

GitHubからcloneした後のリポジトリルートは、

``` text
<ENMA-WG>\enma-poc
```

です。

リポジトリルートへ移動した後は、できるだけ相対パスでコマンドを実行します。

------------------------------------------------------------------------

## 2. 標準環境

ENMA-WG PoCの標準環境は次のとおりです。

  項目                     標準
  ------------------------ ---------------------------------
  OS                       Windows 11
  PowerShell               Windows PowerShell / PowerShell
  Python                   3.11.9（64-bit）
  Git                      Git for Windows
  Git Credential Manager   Git for Windows付属・推奨
  IfcOpenShell             0.8.5
  Repository               `ENMA-WG/enma-poc`
  仮想環境                 `.venv`

PC上にPython
3.14など別バージョンが共存していても構いません。ENMA-WGの仮想環境にはPython
3.11.9を使用します。

------------------------------------------------------------------------

## 3. Git for Windows のインストール

Gitが入っていない場合はGit for Windowsをインストールします。

PowerShellで確認します。

``` powershell
git --version
```

例:

``` text
git version 2.55.0.windows.5
```

Git Credential Managerも確認します。

``` powershell
git credential-manager --version
```

バージョン番号が表示されれば利用可能です。

------------------------------------------------------------------------

## 4. ENMA-WG 作業フォルダの準備

使用するドライブを決め、親フォルダを作成します。

C:の場合:

``` powershell
New-Item -ItemType Directory -Path "C:\ENMA-WG" -Force
Set-Location "C:\ENMA-WG"
```

D:の場合:

``` powershell
New-Item -ItemType Directory -Path "D:\ENMA-WG" -Force
Set-Location "D:\ENMA-WG"
```

G:の場合:

``` powershell
New-Item -ItemType Directory -Path "G:\ENMA-WG" -Force
Set-Location "G:\ENMA-WG"
```

以降、本書では選択した親フォルダを、

``` text
<ENMA-WG>
```

と表記します。

全員が同じドライブ文字を使用することを前提にしません。

------------------------------------------------------------------------

## 5. GitHub リポジトリへのアクセス確認

対象リポジトリは次のとおりです。

``` text
https://github.com/ENMA-WG/enma-poc.git
```

Publicリポジトリは閲覧・cloneできても、**読み取り権限と書き込み権限は別です**。

変更をpushするには、そのPCで使用するGitHubアカウントに、リポジトリまたはENMA-WG
Organization上の適切な権限が必要です。

特に次の3点を区別してください。

-   `git config user.name` / `user.email`：commitの作成者情報
-   GitHubブラウザ認証 / Git Credential
    Manager：使用するGitHubアカウントの認証
-   Repository / Organization権限：そのアカウントがpushできるかどうか

GitHubへのログインに成功していても、push権限があるとは限りません。

------------------------------------------------------------------------

## 6. GitHub リポジトリのclone

選択した親フォルダへ移動します。

``` powershell
Set-Location "<ENMA-WG>"
```

`<ENMA-WG>` は実際のパスへ読み替えます。

例:

``` powershell
Set-Location "D:\ENMA-WG"
```

cloneします。

``` powershell
git clone https://github.com/ENMA-WG/enma-poc.git
```

リポジトリルートへ移動します。

``` powershell
Set-Location .\enma-poc
```

現在位置を確認します。

``` powershell
Get-Location
```

以降のコマンドは、

``` text
<ENMA-WG>\enma-poc
```

にいることを前提とします。

例えば、

``` text
PS D:\ENMA-WG\enma-poc>
```

であれば、環境確認スクリプトは、

``` powershell
.\scripts\check_environment.ps1
```

と実行します。

すでに `enma-poc` 内にいる場合は、

``` text
.\enma-poc\scripts\...
```

とはしません。

------------------------------------------------------------------------

## 7. PowerShell ExecutionPolicy の設定

新しいWindows PCでは、PowerShellが `.ps1`
の実行を禁止している場合があります。

現在の設定を確認します。

``` powershell
Get-ExecutionPolicy -List
```

個人PCなど、設定変更が許可されている環境では、本書ではCurrentUserに対して次を使用します。

``` powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

再確認します。

``` powershell
Get-ExecutionPolicy -List
```

例:

``` text
CurrentUser    RemoteSigned
```

会社管理PCの場合は、会社のセキュリティポリシーに従ってください。Group
Policyなど管理者側の設定を無理に回避しないでください。

------------------------------------------------------------------------

## 8. 初回環境チェック

リポジトリには次のスクリプトがあります。

``` text
scripts\check_environment.ps1
```

リポジトリルートから実行します。

``` powershell
.\scripts\check_environment.ps1
```

このスクリプトは、リポジトリが `C:`、`D:`、`G:`
などどのドライブにあっても動作するように設計されています。

clone直後でPython仮想環境をまだ作っていない場合は、例えば次のWARNが表示されても正常です。

``` text
[WARN] Virtual Environment (.venv) not found
[WARN] IfcOpenShell check skipped (.venv not found)
```

`WARN`
は必ずしもエラーを意味しません。この段階では「まだ設定が必要な項目」を示します。

なお、このスクリプトは実際にpushすることでGitHubの書き込み権限を試験することはしません。

------------------------------------------------------------------------

## 9. Python 3.11.9 のインストール・確認

必要に応じてPython 3.11.9（64-bit）をインストールします。

インストール済みPythonを確認します。

``` powershell
py -0p
```

例:

``` text
-V:3.14 *    C:\...\python.exe
-V:3.11      C:\...\Python311\python.exe
```

複数バージョンが共存していても問題ありません。

Python 3.11を確認します。

``` powershell
py -3.11 --version
```

期待値:

``` text
Python 3.11.9
```

システム既定のPythonが別バージョンでも確実に3.11を選択するため、`py -3.11`
を使用します。

------------------------------------------------------------------------

## 10. Python 仮想環境の作成

PowerShellがリポジトリルート、

``` text
<ENMA-WG>\enma-poc
```

にあることを確認します。

Python 3.11を指定して仮想環境を作成します。

``` powershell
py -3.11 -m venv .venv
```

`.venv` を別PCからコピーしないでください。各PCで作成します。

------------------------------------------------------------------------

## 11. 仮想環境の有効化

`.venv` を有効化します。

``` powershell
.\.venv\Scripts\Activate.ps1
```

PowerShellの先頭に、

``` text
(.venv)
```

が表示されます。

例:

``` text
(.venv) PS D:\ENMA-WG\enma-poc>
```

Pythonを確認します。

``` powershell
python --version
```

期待値:

``` text
Python 3.11.9
```

使用中のPython実体を確認します。

``` powershell
where.exe python
```

最初に、

``` text
<ENMA-WG>\enma-poc\.venv\Scripts\python.exe
```

が表示されれば、ENMA-WGの仮想環境内でPythonが動作しています。

------------------------------------------------------------------------

## 12. pip の更新

`.venv` を有効化した状態で実行します。

``` powershell
python -m pip install --upgrade pip
```

必要に応じて確認します。

``` powershell
python -m pip --version
```

------------------------------------------------------------------------

## 13. ENMA-WG Python 依存ライブラリのインストール

リポジトリの `requirements.txt` から標準ライブラリをインストールします。

``` powershell
python -m pip install -r requirements.txt
```

現在の標準環境は次のとおりです。

``` text
ifcopenshell==0.8.5
isodate==0.7.2
lark==1.3.1
numpy==2.4.6
python-dateutil==2.9.0.post0
shapely==2.1.2
six==1.17.0
typing_extensions==4.16.0
```

依存パッケージを意図的に追加・更新した場合は、必要に応じて
`requirements.txt` も更新します。

------------------------------------------------------------------------

## 14. IfcOpenShell の確認

IfcOpenShellがimportできることを確認します。

``` powershell
python -c "import ifcopenshell; print(ifcopenshell.version)"
```

期待値:

``` text
0.8.5
```

詳細は次でも確認できます。

``` powershell
python -m pip show ifcopenshell
```

------------------------------------------------------------------------

## 15. 最終環境チェック

リポジトリルートから再度実行します。

``` powershell
.\scripts\check_environment.ps1
```

環境構築とGit同期が完了し、警告事項がなければ、概ね次のようになります。

``` text
Result: 14 OK / 0 WARN / 0 NG

[READY] ENMA PoC development environment is ready.
```

チェック項目数は今後スクリプトを改良した場合に変わる可能性があります。

例えば、

``` text
[WARN] Local branch is ahead of origin/main by 1 commit(s)
```

はPython環境の異常ではありません。ローカルにremote-tracking
branchへまだ反映されていないcommitがあることを示します。

環境確認スクリプトは、自動で `git fetch` や `git push` を実行しません。

------------------------------------------------------------------------

## 16. リポジトリ構成

概ね次の構成です。

``` text
enma-poc/
├─ README.md
├─ LICENSE
├─ .gitignore
├─ requirements.txt
│
├─ src/
│  └─ Python source code
│
├─ tests/
│  └─ automated tests
│
├─ scripts/
│  └─ check_environment.ps1
│
├─ data/
│  └─ README.md
│
├─ output/
│  └─ generated CSV and PoC results
│
├─ docs/
│  └─ setup_windows.md
│
└─ presentation/
   └─ presentation materials
```

`.venv` は各PC固有のローカル開発環境であり、GitHubへcommitしません。

------------------------------------------------------------------------

## 17. サンプルBIMデータ

ENMA-WG PoCでは、国土交通省（MLIT）が公開しているBIMデータを利用します。

元のBIMデータ自体は、このリポジトリでは配布しません。

取得・準備方法については、

``` text
data\README.md
```

を参照してください。

各開発者が適切な公式配布元から元データを取得し、必要なIFCファイルをローカルで準備します。

大容量のBIM/IFCファイルは、再配布条件・ライセンス条件を確認せずにリポジトリへcommitしないでください。

------------------------------------------------------------------------

## 18. 基本的なGit作業手順

作業開始時にリポジトリルートへ移動します。

``` powershell
Set-Location "<ENMA-WG>\enma-poc"
```

仮想環境を有効化します。

``` powershell
.\.venv\Scripts\Activate.ps1
```

必要に応じて環境を確認します。

``` powershell
.\scripts\check_environment.ps1
```

Git状態を確認します。

``` powershell
git status
```

新しい作業を始める前には、必要に応じてGitHubと同期します。

``` powershell
git pull
```

編集後:

``` powershell
git status
git add .
git commit -m "Describe the change"
git push
```

共同開発で大きな変更を行う場合は、`main`
へ直接大きな変更を加えるより、feature branchとPull
Requestの利用を基本とします。

例:

``` powershell
git switch -c feature/pipe-extraction
```

作業完了後:

``` powershell
git add .
git commit -m "Add pipe extraction prototype"
git push -u origin feature/pipe-extraction
```

その後GitHubでPull Requestを作成します。

------------------------------------------------------------------------

## 19. WindowsでのGitHub認証

WindowsのHTTPS Git操作ではGit Credential Managerの利用を推奨します。

確認:

``` powershell
git credential-manager --version
```

`git push` 時に認証が必要な場合、

``` text
info: please complete authentication in your browser...
```

と表示されることがあります。

使用するGitHubアカウントでブラウザ認証を完了してください。

ここでも「認証」と「権限」は別です。

-   **Authentication（認証）**：どのGitHubアカウントを使用しているか
-   **Authorization（権限）**：そのアカウントが `ENMA-WG/enma-poc`
    へpushできるか

------------------------------------------------------------------------

## 20. よくあるGitHub / Gitエラー

### 20.1 認証エラー

例:

``` text
remote: Invalid username or token.
Password authentication is not supported for Git operations.
fatal: Authentication failed
```

Git Credential Managerを確認します。

``` powershell
git credential-manager --version
```

その後Git操作を再試行し、求められた場合はブラウザ認証を完了します。

### 20.2 Permission denied / HTTP 403

例:

``` text
remote: Permission to ENMA-WG/enma-poc.git denied to <GitHubUser>.
fatal: unable to access 'https://github.com/ENMA-WG/enma-poc.git/': The requested URL returned error: 403
```

これは、現在使用しているGitHubアカウントにリポジトリへの十分な書き込み権限がない場合に発生します。

次を確認します。

1.  どのGitHubアカウントで認証されているか。
2.  そのアカウントが適切な権限を持つmember/collaboratorになっているか。
3.  Organizationからの招待が保留中ではないか。
4.  RepositoryまたはTeamでWrite権限が付与されているか。

次の設定とは別問題です。

``` powershell
git config user.name
git config user.email
```

これらはcommitの作成者情報であり、GitHubへのpush権限を付与するものではありません。

------------------------------------------------------------------------

## 21. 別のPCで作業を開始する場合

新しい自宅PC、ノートPC、会社PC、デモPCでは、次の順序を基本とします。

1.  Git for Windowsをインストールする。
2.  `C:\ENMA-WG`、`D:\ENMA-WG`、`G:\ENMA-WG`
    などの作業フォルダを準備する。
3.  GitHubアクセスを確認する。
4.  `ENMA-WG/enma-poc` をcloneする。
5.  許可された範囲でPowerShell ExecutionPolicyを設定する。
6.  `.\scripts\check_environment.ps1` を初回実行する。
7.  Python 3.11.9をインストール・確認する。
8.  `.venv` を作成する。
9.  `.venv` を有効化する。
10. `requirements.txt` をインストールする。
11. IfcOpenShellを確認する。
12. `.\scripts\check_environment.ps1` を最終実行する。

`.venv` はPC間でコピーしません。

Gitリポジトリと `requirements.txt`
を、再現可能な共同作業環境の受け渡し手段とします。`.venv`
は各PC固有です。

------------------------------------------------------------------------

## 22. 仮想環境の終了

作業終了時:

``` powershell
deactivate
```

PowerShellの `(.venv)` 表示が消えます。

------------------------------------------------------------------------

## 23. 環境確認チェックリスト

ENMA-WG PoCの開発を開始する前に、次を確認します。

-   Gitが利用できる。
-   Git Credential Managerが利用できる。
-   正しいrepositoryがcloneされている。
-   PowerShellからプロジェクトの `.ps1` を実行できる。
-   Python 3.11.9が利用できる。
-   `.venv` がPython 3.11.9を使用している。
-   `requirements.txt` の依存ライブラリがインストールされている。
-   IfcOpenShell 0.8.5をimportできる。
-   Git remote `origin` が `ENMA-WG/enma-poc` を指している。
-   Git `user.name` / `user.email` が設定されている。
-   現在のbranchとtracking branchの状態を把握している。
-   push前に、使用するGitHubアカウントが必要な権限を持っている。

簡易確認には次を使用します。

``` powershell
.\scripts\check_environment.ps1
```

------------------------------------------------------------------------

## 24. 補足

本書は、特定PCや特定ドライブに依存しないことを重視しています。

リポジトリルートへ移動した後は、

``` powershell
.\scripts\check_environment.ps1
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

のような相対パスを優先し、毎回 `G:`
などの特定ドライブをコマンドへ埋め込まないようにします。

また、セットアップ手順は複数のWindows
PCで実機検証し、他のENMA-WGメンバーが利用する前に、PC固有の暗黙条件をできるだけ洗い出します。
