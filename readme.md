# PyQt6 GitHub Sync Manager

A Windows desktop GitHub sync tool built with Python and PyQt6.

This application helps Windows users manage GitHub repositories with a simple graphical interface. It uses Git for Windows and GitHub CLI under the hood, so the app does not store GitHub passwords, tokens, or credentials.

## Features

### Repository List

* List GitHub repositories by owner
* Search repository by name
* Open repository in browser
* Copy repository URL
* Use selected repository as upload target
* Load all repository files
* Display repository source files in a Windows File Explorer style tree
* Display releases, release assets, and release body download links
* Display GitHub Packages manifest
* Right click support:

  * Open in GitHub
  * Check This Item
  * Uncheck This Item
  * Expand
  * Collapse
  * Save
* Save selected file
* Save selected folder as ZIP
* Download full repository source, releases, release body links, and package manifest as ZIP

### Upload New Repository

* Select local project folder
* Auto-generate repository name from folder name
* Set GitHub owner
* Choose public or private repository
* Set commit message
* Check Git and GitHub CLI tools
* Check GitHub login status
* Open GitHub CLI login
* Generate safe `.gitignore`
* Display local folder as a Windows File Explorer style tree
* Select individual files or whole folders for upload
* Automatically detect files ignored by `.gitignore`
* Automatically skip ignored files during `git add`
* Safety scan before upload
* One Click First Upload
* One Click Update Push

### Download Progress

* Popup download status dialog
* Shows download speed
* Shows downloaded MB / total MB
* Shows percentage
* Shows progress bar

### Setup Guide

* Built-in Windows setup instructions for:

  * Python
  * Git for Windows
  * GitHub CLI
  * GitHub login
  * Git basic workflow

### Standard GitHub Prompt

* Built-in prompt for generating:

  * GitHub upload guide
  * Project summary
  * README
  * `.gitignore`
  * Upload checklist

## Requirements

* Windows 10 or Windows 11
* Python 3.10 or above
* PyQt6
* Git for Windows
* GitHub CLI
* Git Credential Manager

## Installation

### 1. Clone or download this project

```bash
git clone https://github.com/karuvanan/github-sync-manager.git
cd github-sync-manager
```

### 2. Create virtual environment

```bash
python -m venv .venv
```

### 3. Activate virtual environment

```bash
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` is not available:

```bash
pip install PyQt6
```

### 5. Check Git

```bash
git --version
```

### 6. Check GitHub CLI

```bash
gh --version
```

### 7. Login to GitHub

```bash
gh auth login
```

Recommended options:

```text
GitHub.com
HTTPS
Login with browser
```

Check login status:

```bash
gh auth status
```

### 8. Run the app

```bash
python main.py
```

## Build EXE with PyInstaller

Install PyInstaller:

```bash
pip install pyinstaller
```

Build:

```bash
pyinstaller --onefile --windowed --name GitHubSyncManager main.py
```

Output:

```text
dist/GitHubSyncManager.exe
```

## First Upload to GitHub

If using command line manually:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
gh repo create karuvanan/github-sync-manager --public
git remote add origin https://github.com/karuvanan/github-sync-manager.git
git push -u origin main
```

For private repository:

```bash
gh repo create karuvanan/github-sync-manager --private
```

## Update Existing Repository

```bash
git status
git add .
git commit -m "Update"
git push
```

## Safe Files to Upload

Recommended files:

```text
main.py
README.md
requirements.txt
.gitignore
LICENSE
```

Optional:

```text
docs/
screenshots/
database/schema.sql
```

## Files Not Recommended for Upload

Do not upload:

```text
.env
.env.local
*.sqlite
*.sqlite3
*.db
app.sqlite
logs/
backup/
backups/
cache/
tmp/
temp/
vendor/
node_modules/
dist/
build/
*.spec
.venv/
real customer data
real financial data
API keys
password files
token files
credential files
```

## Notes

This application does not store your GitHub password or token. Authentication is handled by:

```text
GitHub CLI
Git Credential Manager
Browser login
```

All Git and GitHub operations are executed through `subprocess.run()`.
