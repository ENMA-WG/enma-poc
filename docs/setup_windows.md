# ENMA-WG PoC Windows Development Environment Setup

## 1. Overview

This document describes how to set up the Windows development
environment for the ENMA-WG proof-of-concept project.

The objective is to create a reproducible development environment that
can be used on company PCs, home PCs, and demonstration PCs.

The ENMA-WG PoC uses Python and IfcOpenShell to process IFC data for MEP
quantity takeoff and related openBIM experiments.

------------------------------------------------------------------------

## 2. Standard Environment

The initial ENMA-WG development environment is based on:

  Component      Version
  -------------- ------------------
  OS             Windows 11
  Python         3.11.9 (64-bit)
  Git            Git for Windows
  IfcOpenShell   0.8.5
  Repository     ENMA-WG/enma-poc

Python libraries used by the project are managed with a Python virtual
environment (`.venv`) and `requirements.txt`.

------------------------------------------------------------------------

## 3. Install Git for Windows

Install Git for Windows if Git is not already installed.

Official website:

https://git-scm.com/download/win

After installation, open PowerShell and confirm that Git is available.

``` powershell
git --version
```

Example:

``` text
git version 2.39.0.windows.2
```

The exact Git version does not need to match this example.

------------------------------------------------------------------------

## 4. Install Python 3.11.9

The standard Python version for the initial ENMA-WG PoC is:

``` text
Python 3.11.9 (64-bit)
```

Download Python from the official Python website:

https://www.python.org/downloads/release/python-3119/

Select the Windows 64-bit installer.

During installation, enable:

``` text
Add python.exe to PATH
```

After installation, close and reopen PowerShell.

Check the installed Python version:

``` powershell
python --version
```

Expected result:

``` text
Python 3.11.9
```

Check the Python installations recognized by the Windows Python
Launcher:

``` powershell
py -0p
```

Example:

``` text
-V:3.11 * C:\Users\<username>\AppData\Local\Programs\Python\Python311\python.exe
```

> **Note:** Multiple versions of Python may be installed on the same PC.
> ENMA-WG therefore specifies Python 3.11 explicitly when creating the
> virtual environment.

------------------------------------------------------------------------

## 5. Create the ENMA-WG Working Folder

The recommended Windows folder structure is:

``` text
G:\
└─ ENMA-WG\
   └─ enma-poc\
```

Create the parent folder:

``` powershell
New-Item -ItemType Directory -Path "G:\ENMA-WG" -Force
Set-Location "G:\ENMA-WG"
```

If the PC does not have a `G:` drive, another local drive may be used.

For example:

``` text
C:\ENMA-WG
```

or:

``` text
D:\ENMA-WG
```

The repository folder itself should remain named:

``` text
enma-poc
```

------------------------------------------------------------------------

## 6. Clone the GitHub Repository

Clone the ENMA-WG repository:

``` powershell
git clone https://github.com/ENMA-WG/enma-poc.git
```

Move into the repository:

``` powershell
Set-Location "G:\ENMA-WG\enma-poc"
```

Check the repository status:

``` powershell
git status
```

Expected result:

``` text
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

Check the remote repository:

``` powershell
git remote -v
```

Expected result:

``` text
origin  https://github.com/ENMA-WG/enma-poc.git (fetch)
origin  https://github.com/ENMA-WG/enma-poc.git (push)
```

------------------------------------------------------------------------

## 7. Create the Python Virtual Environment

From the repository root:

``` text
G:\ENMA-WG\enma-poc
```

create a Python 3.11 virtual environment:

``` powershell
py -3.11 -m venv .venv
```

Activate it:

``` powershell
.\.venv\Scripts\Activate.ps1
```

After activation, the PowerShell prompt should begin with:

``` text
(.venv)
```

For example:

``` text
(.venv) PS G:\ENMA-WG\enma-poc>
```

Check the Python version:

``` powershell
python --version
```

Expected result:

``` text
Python 3.11.9
```

Check which Python executable is being used:

``` powershell
where.exe python
```

The first entry should be:

``` text
G:\ENMA-WG\enma-poc\.venv\Scripts\python.exe
```

This confirms that Python is running inside the ENMA-WG virtual
environment.

------------------------------------------------------------------------

## 8. PowerShell Execution Policy

On some Windows PCs, PowerShell may prevent `Activate.ps1` from running.

If an execution policy error occurs, check the current policy:

``` powershell
Get-ExecutionPolicy -List
```

A temporary solution for the current PowerShell session is:

``` powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the virtual environment again:

``` powershell
.\.venv\Scripts\Activate.ps1
```

This changes the policy only for the current PowerShell process.

Follow your organization's security policy when using a company-managed
PC.

------------------------------------------------------------------------

## 9. Upgrade pip

With `.venv` activated:

``` powershell
python -m pip install --upgrade pip
```

Check the version if required:

``` powershell
python -m pip --version
```

------------------------------------------------------------------------

## 10. Install ENMA-WG Python Dependencies

The standard method for ENMA-WG members is to install the libraries from
`requirements.txt`.

``` powershell
python -m pip install -r requirements.txt
```

The initial environment contains:

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

Developers adding or updating Python packages should update
`requirements.txt` as appropriate.

------------------------------------------------------------------------

## 11. Verify IfcOpenShell

Confirm that IfcOpenShell can be imported:

``` powershell
python -c "import ifcopenshell; print(ifcopenshell.version)"
```

Expected result:

``` text
0.8.5
```

Additional package information can be checked with:

``` powershell
python -m pip show ifcopenshell
```

If the version number is displayed without an error, the basic ENMA-WG
Python/IFC environment is ready.

------------------------------------------------------------------------

## 12. Repository Structure

The initial repository structure is:

``` text
enma-poc/
├─ README.md
├─ LICENSE
├─ .gitignore
├─ requirements.txt
│
├─ src/
│   └─ Python source code
│
├─ tests/
│   └─ automated tests
│
├─ data/
│   └─ README.md
│
├─ output/
│   └─ generated CSV and PoC results
│
├─ docs/
│   └─ project documentation
│
└─ presentation/
    └─ presentation materials
```

The `.venv` directory is a local development environment and must not be
committed to GitHub.

------------------------------------------------------------------------

## 13. Sample BIM Data

The ENMA-WG PoC uses BIM data published by the Ministry of Land,
Infrastructure, Transport and Tourism (MLIT), Japan.

The original BIM data is not distributed through this repository.

See `data/README.md` for information about obtaining and preparing the
sample BIM data.

Each developer should obtain the original BIM data from the official
source and prepare the IFC file locally.

Large BIM/IFC files should not be committed to the repository unless
their redistribution and licensing conditions have been confirmed.

------------------------------------------------------------------------

## 14. Basic Git Workflow

Before starting work, move to the repository:

``` powershell
Set-Location "G:\ENMA-WG\enma-poc"
```

Activate the Python environment:

``` powershell
.\.venv\Scripts\Activate.ps1
```

Check the Git status:

``` powershell
git status
```

Before beginning new work, synchronize with GitHub:

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
normally be used instead of making substantial changes directly on
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

## 15. GitHub Authentication on Windows

GitHub does not support account-password authentication for Git
operations over HTTPS.

Git Credential Manager is recommended for Windows.

Check whether it is installed:

``` powershell
git credential-manager --version
```

Configure Git to use it:

``` powershell
git config --global credential.helper manager
```

When the following command is executed:

``` powershell
git push
```

Git Credential Manager may display:

``` text
info: please complete authentication in your browser...
```

Complete the GitHub authentication in the web browser.

After successful authentication, Git Credential Manager stores the
credentials securely for subsequent Git operations.

------------------------------------------------------------------------

## 16. Common Authentication Error

If the following error appears:

``` text
remote: Invalid username or token.
Password authentication is not supported for Git operations.
fatal: Authentication failed
```

confirm that Git Credential Manager is installed:

``` powershell
git credential-manager --version
```

Then configure it:

``` powershell
git config --global credential.helper manager
```

and retry:

``` powershell
git push
```

Complete authentication in the browser when requested.

------------------------------------------------------------------------

## 17. Starting Work on Another PC

When using another PC, such as a home PC or demonstration PC, do not
copy the `.venv` directory from another machine.

Instead:

1.  Install Git.
2.  Install Python 3.11.9.
3.  Clone the repository.
4.  Create a new `.venv`.
5.  Activate `.venv`.
6.  Install `requirements.txt`.

Example:

``` powershell
git clone https://github.com/ENMA-WG/enma-poc.git
cd enma-poc

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -c "import ifcopenshell; print(ifcopenshell.version)"
```

Expected final result:

``` text
0.8.5
```

------------------------------------------------------------------------

## 18. Deactivate the Virtual Environment

When development work is finished:

``` powershell
deactivate
```

The `(.venv)` prefix will disappear from the PowerShell prompt.

------------------------------------------------------------------------

## 19. Environment Verification Checklist

The setup is complete when all of the following are confirmed:

-   Git commands can be executed.
-   The `ENMA-WG/enma-poc` repository has been cloned.
-   Python 3.11.9 is installed.
-   `.venv` has been created with Python 3.11.
-   `.venv` is active.
-   `python --version` reports Python 3.11.9.
-   `requirements.txt` installs successfully.
-   IfcOpenShell imports successfully.
-   `ifcopenshell.version` reports 0.8.5.
-   `git status` works inside the repository.
-   GitHub authentication works for authorized ENMA-WG contributors.

At this point the PC is ready for ENMA-WG PoC development.

------------------------------------------------------------------------

## 20. Notes

This document describes the initial Windows development environment for
the ENMA-WG PoC.

The environment may change as the project evolves. When dependencies or
setup procedures change, this document and `requirements.txt` should be
updated together.

Last verified environment:

``` text
Windows 11
Python 3.11.9
IfcOpenShell 0.8.5
```

------------------------------------------------------------------------

# 日本語版：ENMA-WG PoC Windows 開発環境セットアップ

## 1. 概要 (Overview)

このドキュメントでは、ENMA-WGの概念実証（PoC）プロジェクト向けのWindows開発環境の設定方法について説明します。

目的は、会社PC、自宅PC、およびデモ用PCで利用可能な、再現性のある開発環境を構築することです。

ENMA-WGのPoCでは、PythonとIfcOpenShellを使用してIFCデータを処理し、MEP数量算出および関連するopenBIM実験を行います。

------------------------------------------------------------------------

## 2. 標準環境 (Standard Environment)

ENMA-WGの初期開発環境は、以下を標準とします。

  コンポーネント   バージョン
  ---------------- ------------------
  OS               Windows 11
  Python           3.11.9 (64-bit)
  Git              Git for Windows
  IfcOpenShell     0.8.5
  リポジトリ       ENMA-WG/enma-poc

このプロジェクトで使用するPythonライブラリは、Pythonの仮想環境（`.venv`）と`requirements.txt`によって管理します。

------------------------------------------------------------------------

## 3. Git for Windowsのインストール (Install Git for Windows)

Gitがまだインストールされていない場合は、Git for
Windowsをインストールしてください。

公式サイト：

https://git-scm.com/download/win

インストールが完了したら、PowerShellを起動し、Gitが利用可能であることを確認します。

``` powershell
git --version
```

実行例：

``` text
git version 2.39.0.windows.2
```

Gitのバージョンは、この例と完全に一致する必要はありません。

------------------------------------------------------------------------

## 4. Python 3.11.9のインストール (Install Python 3.11.9)

ENMA-WGの初期PoCにおける標準Pythonバージョンは以下のとおりです。

``` text
Python 3.11.9 (64-bit)
```

Pythonの公式サイトからダウンロードしてください。

https://www.python.org/downloads/release/python-3119/

Windows 64ビット版インストーラーを選択します。

インストール時に、以下の設定を有効にしてください。

``` text
Add python.exe to PATH
```

インストール完了後、PowerShellを一度閉じてから再度起動します。

インストールされたPythonのバージョンを確認します。

``` powershell
python --version
```

期待される結果：

``` text
Python 3.11.9
```

Windows Python
Launcherが認識しているPythonのインストール状況を確認します。

``` powershell
py -0p
```

実行例：

``` text
-V:3.11 * C:\Users\<username>\AppData\Local\Programs\Python\Python311\python.exe
```

> **注記：**
> 1台のPCに複数バージョンのPythonがインストールされている場合があります。そのため、ENMA-WGでは仮想環境を作成する際にPython
> 3.11を明示的に指定します。

------------------------------------------------------------------------

## 5. ENMA-WG作業フォルダの作成 (Create the ENMA-WG Working Folder)

Windowsでの推奨フォルダ構造は次のとおりです。

``` text
G:\
└─ ENMA-WG\
   └─ enma-poc\
```

親フォルダを作成します。

``` powershell
New-Item -ItemType Directory -Path "G:\ENMA-WG" -Force
Set-Location "G:\ENMA-WG"
```

PCに`G:`ドライブがない場合は、別のローカルドライブを使用できます。

例：

``` text
C:\ENMA-WG
```

または：

``` text
D:\ENMA-WG
```

リポジトリフォルダ自体の名前は、次のままとします。

``` text
enma-poc
```

------------------------------------------------------------------------

## 6. GitHubリポジトリのクローン (Clone the GitHub Repository)

ENMA-WGのGitHubリポジトリをクローンします。

``` powershell
git clone https://github.com/ENMA-WG/enma-poc.git
```

リポジトリへ移動します。

``` powershell
Set-Location "G:\ENMA-WG\enma-poc"
```

リポジトリの状態を確認します。

``` powershell
git status
```

期待される結果：

``` text
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

リモートリポジトリを確認します。

``` powershell
git remote -v
```

期待される結果：

``` text
origin  https://github.com/ENMA-WG/enma-poc.git (fetch)
origin  https://github.com/ENMA-WG/enma-poc.git (push)
```

------------------------------------------------------------------------

## 7. Python仮想環境の作成 (Create the Python Virtual Environment)

リポジトリのルートディレクトリから作業します。

``` text
G:\ENMA-WG\enma-poc
```

Python 3.11の仮想環境を作成します。

``` powershell
py -3.11 -m venv .venv
```

仮想環境を有効化します。

``` powershell
.\.venv\Scripts\Activate.ps1
```

有効化後、PowerShellプロンプトの先頭に次のように表示されます。

``` text
(.venv)
```

例：

``` text
(.venv) PS G:\ENMA-WG\enma-poc>
```

Pythonのバージョンを確認します。

``` powershell
python --version
```

期待される結果：

``` text
Python 3.11.9
```

どのPython実行ファイルが使用されているか確認します。

``` powershell
where.exe python
```

最初のエントリは次のようになります。

``` text
G:\ENMA-WG\enma-poc\.venv\Scripts\python.exe
```

これにより、PythonがENMA-WGの仮想環境内で実行されていることを確認できます。

------------------------------------------------------------------------

## 8. PowerShellの実行ポリシー (PowerShell Execution Policy)

一部のWindows
PCでは、PowerShellによって`Activate.ps1`の実行が妨げられる場合があります。

実行ポリシーのエラーが発生した場合は、現在のポリシーを確認します。

``` powershell
Get-ExecutionPolicy -List
```

現在のPowerShellセッションだけに適用する一時的な対応は次のとおりです。

``` powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

その後、仮想環境を再度有効化します。

``` powershell
.\.venv\Scripts\Activate.ps1
```

この設定は、現在のPowerShellプロセスに対してのみ適用されます。

会社が管理するPCを使用する場合は、所属組織のセキュリティポリシーに従ってください。

------------------------------------------------------------------------

## 9. pipのアップグレード (Upgrade pip)

`.venv`を有効にした状態で実行します。

``` powershell
python -m pip install --upgrade pip
```

必要に応じてバージョンを確認します。

``` powershell
python -m pip --version
```

------------------------------------------------------------------------

## 10. ENMA-WGのPython依存関係のインストール (Install ENMA-WG Python Dependencies)

ENMA-WGメンバーの標準的な方法は、`requirements.txt`に基づいてライブラリをインストールすることです。

``` powershell
python -m pip install -r requirements.txt
```

初期環境には以下のパッケージが含まれています。

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

Pythonパッケージを追加または更新した開発者は、必要に応じて`requirements.txt`も更新してください。

------------------------------------------------------------------------

## 11. IfcOpenShellの確認 (Verify IfcOpenShell)

IfcOpenShellをインポートできることを確認します。

``` powershell
python -c "import ifcopenshell; print(ifcopenshell.version)"
```

期待される結果：

``` text
0.8.5
```

パッケージの追加情報は、以下のコマンドで確認できます。

``` powershell
python -m pip show ifcopenshell
```

バージョン番号がエラーなしで表示されれば、基本的なENMA-WG
Python/IFC環境の準備は完了です。

------------------------------------------------------------------------

## 12. リポジトリ構造 (Repository Structure)

初期のリポジトリ構造は次のとおりです。

``` text
enma-poc/
├─ README.md
├─ LICENSE
├─ .gitignore
├─ requirements.txt
│
├─ src/
│   └─ Python source code
│
├─ tests/
│   └─ automated tests
│
├─ data/
│   └─ README.md
│
├─ output/
│   └─ generated CSV and PoC results
│
├─ docs/
│   └─ project documentation
│
└─ presentation/
    └─ presentation materials
```

`.venv`ディレクトリはローカルの開発環境であり、GitHubにコミットしてはいけません。

------------------------------------------------------------------------

## 13. サンプルBIMデータ (Sample BIM Data)

ENMA-WGのPoCでは、日本の国土交通省（MLIT）が公開しているBIMデータを使用しています。

元のBIMデータは、このリポジトリでは配布しません。

サンプルBIMデータの入手および準備方法については、`data/README.md`を参照してください。

各開発者は公式の情報源から元のBIMデータを入手し、ローカル環境でIFCファイルを準備してください。

大規模なBIM/IFCファイルは、再配布およびライセンス条件が確認されていない限り、リポジトリにコミットしないでください。

------------------------------------------------------------------------

## 14. Gitの基本ワークフロー (Basic Git Workflow)

作業を開始する前に、リポジトリへ移動します。

``` powershell
Set-Location "G:\ENMA-WG\enma-poc"
```

Python仮想環境を有効化します。

``` powershell
.\.venv\Scripts\Activate.ps1
```

Gitの状態を確認します。

``` powershell
git status
```

新しい作業を始める前にGitHubと同期します。

``` powershell
git pull
```

ファイルを編集した後は、次のように操作します。

``` powershell
git status
git add .
git commit -m "Describe the change"
git push
```

共同開発では、`main`ブランチへ直接大幅な変更を加えるのではなく、通常は機能ブランチとPull
Requestを使用します。

例：

``` powershell
git switch -c feature/pipe-extraction
```

作業完了後：

``` powershell
git add .
git commit -m "Add pipe extraction prototype"
git push -u origin feature/pipe-extraction
```

その後、GitHub上でPull Requestを作成します。

------------------------------------------------------------------------

## 15. WindowsでのGitHub認証 (GitHub Authentication on Windows)

GitHubでは、HTTPS経由のGit操作において、アカウントのパスワードによる認証はサポートされていません。

WindowsではGit Credential Managerの使用を推奨します。

インストールされているか確認します。

``` powershell
git credential-manager --version
```

GitでGit Credential Managerを使用するよう設定します。

``` powershell
git config --global credential.helper manager
```

次のコマンドを実行すると、

``` powershell
git push
```

Git Credential
Managerから次のようなメッセージが表示される場合があります。

``` text
info: please complete authentication in your browser...
```

ブラウザでGitHub認証を完了してください。

認証が成功すると、Git Credential
Managerはその後のGit操作に使用する認証情報を安全に保存します。

------------------------------------------------------------------------

## 16. よくある認証エラー (Common Authentication Error)

以下のエラーが表示された場合：

``` text
remote: Invalid username or token.
Password authentication is not supported for Git operations.
fatal: Authentication failed
```

Git Credential Managerがインストールされていることを確認します。

``` powershell
git credential-manager --version
```

次に設定します。

``` powershell
git config --global credential.helper manager
```

再試行します。

``` powershell
git push
```

要求された場合は、ブラウザで認証を完了してください。

------------------------------------------------------------------------

## 17. 別のPCでの作業開始 (Starting Work on Another PC)

自宅PCやデモ用PCなど、別のPCを使用する場合は、他のマシンから`.venv`ディレクトリをコピーしないでください。

代わりに、次の手順で環境を再構築します。

1.  Gitをインストールする。
2.  Python 3.11.9をインストールする。
3.  リポジトリをクローンする。
4.  新しい`.venv`を作成する。
5.  `.venv`を有効化する。
6.  `requirements.txt`から依存パッケージをインストールする。

実行例：

``` powershell
git clone https://github.com/ENMA-WG/enma-poc.git
cd enma-poc

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -c "import ifcopenshell; print(ifcopenshell.version)"
```

最終的に期待される結果：

``` text
0.8.5
```

------------------------------------------------------------------------

## 18. 仮想環境の無効化 (Deactivate the Virtual Environment)

開発作業が完了したら、次を実行します。

``` powershell
deactivate
```

PowerShellのプロンプトから`(.venv)`というプレフィックスが消えます。

------------------------------------------------------------------------

## 19. 環境確認チェックリスト (Environment Verification Checklist)

以下のすべてが確認できたら、セットアップは完了です。

-   Gitコマンドを実行できる。
-   `ENMA-WG/enma-poc`リポジトリをクローンできている。
-   Python 3.11.9がインストールされている。
-   Python 3.11で`.venv`が作成されている。
-   `.venv`が有効になっている。
-   `python --version`でPython 3.11.9が表示される。
-   `requirements.txt`から依存パッケージを正常にインストールできる。
-   IfcOpenShellを正常にインポートできる。
-   `ifcopenshell.version`で0.8.5が表示される。
-   リポジトリ内で`git status`を実行できる。
-   ENMA-WGの権限を持つ開発者はGitHub認証を正常に行える。

以上が確認できれば、そのPCでENMA-WG PoCの開発を開始できます。

------------------------------------------------------------------------

## 20. 注記 (Notes)

このドキュメントでは、ENMA-WG
PoCの初期Windows開発環境について説明しています。

プロジェクトの進展に伴い、この環境は変更される可能性があります。依存関係やセットアップ手順に変更があった場合は、このドキュメントと`requirements.txt`を同時に更新してください。

最終確認環境：

``` text
Windows 11
Python 3.11.9
IfcOpenShell 0.8.5
```
