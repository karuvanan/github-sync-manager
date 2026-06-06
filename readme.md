# PyQt6 GitHub Sync Manager

A Windows-friendly PyQt6 GUI tool for listing GitHub repositories and uploading / updating local projects to GitHub.

This tool uses:

- Python
- PyQt6
- Git for Windows
- Git Credential Manager
- GitHub CLI `gh`
- `subprocess.run`

It does not save GitHub passwords or tokens.  
GitHub login is handled by Git Credential Manager and GitHub CLI.

---

## Features

### Page 1: Repository List

- Enter GitHub owner
- Refresh repository list using GitHub CLI
- Search repositories by repo name
- Open selected repo in browser
- Copy selected repo URL
- Use selected repo as upload target

Command used:

```bash
gh repo list OWNER --limit 100 --json name,visibility,url,updatedAt