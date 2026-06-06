import os
import re
import json
import fnmatch
import shutil
import tempfile
import webbrowser
import subprocess
import urllib.request
import time
from urllib.parse import urlparse, unquote
from pathlib import Path

from PyQt6.QtCore import Qt, QFileInfo
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QComboBox,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
    QGroupBox,
    QTreeWidget,
    QTreeWidgetItem,
    QSplitter,
    QMenu,
    QProgressBar,
    QDialog,
    QFileIconProvider,
)


DEFAULT_OWNER = "karuvanan"

ROLE_PATH = Qt.ItemDataRole.UserRole
ROLE_KIND = Qt.ItemDataRole.UserRole + 1
ROLE_RISKY = Qt.ItemDataRole.UserRole + 2
ROLE_URL = Qt.ItemDataRole.UserRole + 3
ROLE_TYPE = Qt.ItemDataRole.UserRole + 4
ROLE_DOWNLOADABLE = Qt.ItemDataRole.UserRole + 5
ROLE_IGNORED = Qt.ItemDataRole.UserRole + 6


SAFE_GITIGNORE_ITEMS = [
    ".env",
    ".env.local",
    "*.sqlite",
    "*.sqlite3",
    "*.db",
    "app.sqlite",
    "logs/",
    "backup/",
    "backups/",
    "cache/",
    "tmp/",
    "temp/",
    "vendor/",
    "node_modules/",
    ".vscode/",
    ".idea/",
    "__pycache__/",
    "*.pyc",
    "dist/",
    "build/",
    "*.spec",
    ".DS_Store",
    "Thumbs.db",
]


IMPORTANT_UPLOAD_FILES = [
    "README.md",
    ".gitignore",
    "LICENSE",
    "requirements.txt",
]


MAIN_CODE_CANDIDATES = [
    "main.py",
    "app.py",
    "index.py",
    "index.php",
    "app.php",
    "server.py",
    "manage.py",
    "package.json",
    "composer.json",
]


SENSITIVE_DIR_NAMES = {
    ".git",
    "logs",
    "backup",
    "backups",
    "vendor",
    "node_modules",
    "cache",
    "tmp",
    "temp",
    "dist",
    "build",
    "__pycache__",
}


SENSITIVE_FILE_PATTERNS = [
    ".env",
    ".env.local",
    "*.sqlite",
    "*.sqlite3",
    "*.db",
    "app.sqlite",
]


SENSITIVE_NAME_KEYWORDS = [
    "password",
    "secret",
    "token",
    "credential",
    "privatekey",
    "private-key",
]


STANDARD_CODEX_PROMPT = """请你根据当前这个项目文件夹，帮我整理一份适合上传到 GitHub 的完整说明。

请先扫描当前项目结构，然后输出以下内容：

1. 项目名称建议
2. GitHub repository 名称建议
3. 项目简介，适合放在 README.md
4. 当前项目主要功能列表
5. 当前项目主要文件和文件夹说明
6. 安装环境需求
   - Python / PHP / Node.js 版本
   - MySQL / SQLite 是否需要
   - Composer 是否需要
   - npm 是否需要
   - XAMPP 是否需要
   - 其他第三方 CLI 工具
7. 安装步骤 step by step
8. 第一次上传到 GitHub 的 Git 命令
9. 以后每次更新项目到 GitHub 的 Git 命令
10. .gitignore 建议内容
11. 哪些文件不应该上传 GitHub
    例如：
    - .env
    - app.sqlite
    - database backup
    - logs
    - vendor
    - node_modules
    - 真实客户资料
    - 真实财务资料
    - API key / token / password
12. README.md 完整版本
13. 如果 GitHub 仓库已经存在，要怎样同步
14. 如果出现 remote origin already exists，要怎样处理
15. 如果出现 push rejected / non-fast-forward，要怎样处理
16. 如果本地项目已经有 .git folder，要怎样安全同步
17. 如果 GitHub repo 是空的，要怎样第一次 push
18. 如果 GitHub repo 已经有 README.md，要怎样 pull 再 push

请用 Windows + XAMPP + VS Code 使用者容易明白的方式写。
请所有命令都用完整 command block 显示。
请不要假设我已经懂 GitHub。

另外，请根据当前项目结构，帮我生成最安全的 .gitignore。

.gitignore 重点：

1. 不上传真实数据库
2. 不上传 .env / 密码 / config local
3. 不上传 log / cache / temp
4. 不上传 vendor / node_modules
5. 保留 database/schema.sql
6. 保留 README.md
7. 保留 public source code
8. 保留 composer.json / package.json
9. 保留 requirements.txt
10. 不保留 composer.lock / package-lock.json，除非你判断这个项目需要固定版本

请直接输出完整 .gitignore 内容。

最后，请帮我生成一个 GitHub 上传前检查清单：

- 是否已经生成 README.md
- 是否已经生成 .gitignore
- 是否已经删除真实客户资料
- 是否已经删除真实财务资料
- 是否已经删除数据库备份
- 是否已经确认 .env 没有上传
- 是否已经确认 GitHub repo visibility 是 public 还是 private
"""


SETUP_GUIDE = """# GitHub Sync Manager Setup Guide

这个页面是给 Windows 新手使用的设置说明。

==================================================
1. 安装 Python
==================================================

下载 Python：

https://www.python.org/downloads/

安装时一定要勾选：

Add Python to PATH

检查 Python：

python --version

==================================================
2. 安装 Git for Windows
==================================================

下载 Git for Windows：

https://git-scm.com/download/win

安装后检查：

git --version

Git for Windows 通常会一起安装 Git Credential Manager。

==================================================
3. 安装 GitHub CLI gh
==================================================

下载 GitHub CLI：

https://cli.github.com/

安装后检查：

gh --version

==================================================
4. GitHub 登录
==================================================

执行：

gh auth login

建议选择：

GitHub.com
HTTPS
Login with browser

如果出现 device code，就按照 browser 里的步骤完成。

检查登录状态：

gh auth status

==================================================
5. 设置 Git 用户名称和 Email
==================================================

第一次使用 Git 建议设置：

git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"

查看设置：

git config --global --list

==================================================
6. 第一次上传项目基本流程
==================================================

进入项目 folder 后：

git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/OWNER/REPO.git
git push -u origin main

本软件会自动帮你执行这些步骤。

==================================================
7. 以后每次更新项目
==================================================

git status
git add .
git commit -m "Update"
git push

本软件也会自动帮你执行。

==================================================
8. 如果 remote origin already exists
==================================================

不要 remove origin。

安全做法：

git remote get-url origin
git remote set-url origin https://github.com/OWNER/REPO.git

本软件使用 set-url，不使用 remove origin。

==================================================
9. 如果 push rejected / non-fast-forward
==================================================

原因通常是 GitHub repo 上已经有 README.md 或其他 commit。

可以先执行：

git pull --rebase origin main

然后再：

git push

如果你是新手，不确定是否要覆盖 GitHub 内容，建议先 backup 项目 folder。

==================================================
10. 不应该上传 GitHub 的文件
==================================================

.env
.env.local
*.sqlite
*.sqlite3
*.db
app.sqlite
logs/
backup/
cache/
tmp/
vendor/
node_modules/
真实客户资料
真实财务资料
password / secret / token 文件

==================================================
11. 建议保留上传的文件
==================================================

README.md
.gitignore
LICENSE
requirements.txt
composer.json
package.json
database/schema.sql
public source code
main code files

==================================================
12. 本软件不会保存 GitHub 密码或 token
==================================================

登录交给：

Git Credential Manager
GitHub CLI
Browser login

本软件只通过 subprocess 执行 git / gh command。
"""


def slugify_repo_name(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = re.sub(r"-+", "-", name)
    name = name.strip("-")
    return name or "new-repository"


def safe_filename(name: str) -> str:
    name = str(name).strip()
    name = re.sub(r'[<>:"/\\|?*]+', "-", name)
    name = re.sub(r"-+", "-", name)
    name = name.strip("- ")
    return name or "file"


def format_bytes(byte_count) -> str:
    if byte_count in ("", None):
        return ""
    try:
        byte_count = int(byte_count)
    except Exception:
        return ""
    if byte_count < 1024:
        return f"{byte_count} B"
    if byte_count < 1024 * 1024:
        return f"{byte_count / 1024:.2f} KB"
    return f"{byte_count / 1024 / 1024:.2f} MB"


def format_mb(byte_count: int) -> str:
    return f"{byte_count / 1024 / 1024:.2f} MB"


def format_speed(bytes_per_second: float) -> str:
    return f"{bytes_per_second / 1024 / 1024:.2f} MB/s"


def extract_links_from_release_body(body: str):
    if not body:
        return []

    links = []

    markdown_links = re.findall(r"\[([^\]]+)\]\((https?://[^\s\)]+)\)", body)

    for label, url in markdown_links:
        links.append({
            "label": label.strip(),
            "url": url.strip(),
        })

    raw_urls = re.findall(r"(https?://[^\s\)\]\}]+)", body)

    for url in raw_urls:
        url = url.strip()
        already_exists = any(x["url"] == url for x in links)

        if not already_exists:
            links.append({
                "label": "",
                "url": url,
            })

    return links


def filename_from_url_or_label(url: str, label: str = ""):
    label = str(label or "").strip()

    if label and "." in label:
        return safe_filename(label)

    try:
        path = urlparse(url).path
        filename = os.path.basename(path)
        filename = unquote(filename)

        if filename:
            return safe_filename(filename)
    except Exception:
        pass

    return "downloaded_file"


class DownloadStatusDialog(QDialog):
    def __init__(self, parent=None, title="Download Status"):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.resize(520, 220)
        self.setModal(False)

        layout = QVBoxLayout(self)

        self.title_label = QLabel("Preparing download...")
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.title_label)

        self.speed_label = QLabel("0.00 MB/s")
        self.speed_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1565c0;")
        layout.addWidget(self.speed_label)

        self.size_label = QLabel("0.00 MB / 0.00 MB")
        layout.addWidget(self.size_label)

        self.percent_label = QLabel("0%")
        layout.addWidget(self.percent_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #555;")
        layout.addWidget(self.status_label)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setEnabled(False)
        layout.addWidget(self.close_btn)

    def set_stage(self, text: str):
        self.title_label.setText(text)
        self.speed_label.setText("Working...")
        self.size_label.setText("")
        self.percent_label.setText("")
        self.status_label.setText(text)
        self.progress_bar.setRange(0, 0)
        QApplication.processEvents()

    def update_download(self, filename, downloaded, total_size, speed):
        self.progress_bar.setRange(0, 100)

        if total_size > 0:
            percent = int(downloaded * 100 / total_size)
            percent = max(0, min(100, percent))

            self.title_label.setText(f"Downloading: {filename}")
            self.speed_label.setText(format_speed(speed))
            self.size_label.setText(f"{format_mb(downloaded)} / {format_mb(total_size)}")
            self.percent_label.setText(f"{percent}%")
            self.progress_bar.setValue(percent)
            self.status_label.setText("Downloading...")
        else:
            self.title_label.setText(f"Downloading: {filename}")
            self.speed_label.setText(format_speed(speed))
            self.size_label.setText(f"{format_mb(downloaded)} / Unknown size")
            self.percent_label.setText("")
            self.progress_bar.setRange(0, 0)
            self.status_label.setText("Downloading...")

        QApplication.processEvents()

    def finish_success(self, text="Download completed"):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.speed_label.setText("Completed")
        self.percent_label.setText("100%")
        self.status_label.setText(text)
        self.close_btn.setEnabled(True)
        QApplication.processEvents()

    def finish_failed(self, text="Download failed"):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.speed_label.setText("Failed")
        self.percent_label.setText("0%")
        self.status_label.setText(text)
        self.close_btn.setEnabled(True)
        QApplication.processEvents()


class GitHubSyncManager(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyQt6 GitHub Sync Manager")
        self.resize(1450, 880)

        self.repo_rows = []
        self.current_repo_owner = ""
        self.current_repo_name = ""
        self.icon_provider = QFileIconProvider()
        self._updating_tree_checks = False
        self.gitignore_patterns = []

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.page_repo_list = QWidget()
        self.page_upload = QWidget()
        self.page_setup = QWidget()
        self.page_prompt = QWidget()

        self.tabs.addTab(self.page_repo_list, "Page 1: Repository List")
        self.tabs.addTab(self.page_upload, "Page 2: Upload New Repository")
        self.tabs.addTab(self.page_setup, "Page 3: Setup Guide")
        self.tabs.addTab(self.page_prompt, "Page 4: 标准 GitHub Prompt")

        self.build_repo_list_page()
        self.build_upload_page()
        self.build_setup_page()
        self.build_prompt_page()

    # ============================================================
    # Common
    # ============================================================

    def log(self, message: str, error: bool = False):
        color = "#c62828" if error else "#222222"
        safe = (
            str(message)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        self.output_log.append(f'<span style="color:{color};">{safe}</span>')
        self.output_log.ensureCursorVisible()
        QApplication.processEvents()

    def log_title(self, title: str):
        safe = (
            str(title)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        self.output_log.append(f'<br><b style="color:#1565c0;">{safe}</b>')
        self.output_log.ensureCursorVisible()
        QApplication.processEvents()

    def set_progress(self, value, text=""):
        try:
            value = max(0, min(100, int(value)))
            self.progress_bar.setValue(value)

            if text:
                self.progress_bar.setFormat(text)
            else:
                self.progress_bar.setFormat(f"{value}%")

            QApplication.processEvents()
        except Exception:
            pass

    def run_command(self, cmd, cwd=None, title=None, quiet=False):
        if title:
            self.log_title(title)

        if not quiet:
            self.log(f"$ {' '.join(cmd)}")

            if cwd:
                self.log(f"cwd: {cwd}")

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                shell=False,
                encoding="utf-8",
                errors="replace",
            )

            if not quiet:
                if result.stdout.strip():
                    self.log(result.stdout.strip())

                if result.stderr.strip():
                    self.log(result.stderr.strip(), error=result.returncode != 0)

                if result.returncode != 0:
                    self.log(f"Command exit code: {result.returncode}", error=True)

            return result

        except FileNotFoundError:
            if not quiet:
                self.log(f"Command not found: {cmd[0]}", error=True)
            return None

        except Exception as e:
            if not quiet:
                self.log(f"Error: {e}", error=True)
            return None

    def run_command_to_file(self, cmd, output_file, cwd=None, title=None):
        if title:
            self.log_title(title)

        self.log(f"$ {' '.join(cmd)}")
        self.log(f"output: {output_file}")

        if cwd:
            self.log(f"cwd: {cwd}")

        try:
            with open(output_file, "wb") as f:
                result = subprocess.run(
                    cmd,
                    cwd=cwd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    shell=False,
                )

            if result.stderr:
                stderr_text = result.stderr.decode("utf-8", errors="replace").strip()
                if stderr_text:
                    self.log(stderr_text, error=result.returncode != 0)

            if result.returncode != 0:
                self.log(f"Command exit code: {result.returncode}", error=True)

            return result

        except FileNotFoundError:
            self.log(f"Command not found: {cmd[0]}", error=True)
            return None

        except Exception as e:
            self.log(f"Error: {e}", error=True)
            return None

    def download_url_to_file(self, url, output_file, title=None, dialog=None):
        if title:
            self.log_title(title)

        self.log(f"Download URL: {url}")
        self.log(f"output: {output_file}")

        if dialog is None:
            dialog = DownloadStatusDialog(self, "Download Status")
            dialog.show()

        filename = os.path.basename(output_file)

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "PyQt6-GitHub-Sync-Manager",
                },
            )

            with urllib.request.urlopen(req, timeout=180) as response:
                total_size = response.headers.get("Content-Length")

                try:
                    total_size = int(total_size) if total_size else 0
                except Exception:
                    total_size = 0

                downloaded = 0
                chunk_size = 1024 * 512
                start_time = time.time()
                last_update_time = start_time

                with open(output_file, "wb") as f:
                    while True:
                        chunk = response.read(chunk_size)

                        if not chunk:
                            break

                        f.write(chunk)
                        downloaded += len(chunk)

                        now = time.time()
                        elapsed = max(now - start_time, 0.001)
                        speed = downloaded / elapsed

                        if now - last_update_time >= 0.1:
                            dialog.update_download(
                                filename=filename,
                                downloaded=downloaded,
                                total_size=total_size,
                                speed=speed,
                            )
                            last_update_time = now

                elapsed = max(time.time() - start_time, 0.001)
                speed = downloaded / elapsed

                dialog.update_download(
                    filename=filename,
                    downloaded=downloaded,
                    total_size=total_size,
                    speed=speed,
                )

            dialog.finish_success("Download completed")
            self.log(f"Downloaded: {output_file}")
            return True

        except Exception as e:
            self.log(f"Download URL failed: {e}", error=True)
            dialog.finish_failed(str(e))
            return False

    def validate_project_folder(self):
        folder = self.project_folder_input.text().strip()

        if not folder:
            QMessageBox.warning(self, "Missing Project Folder", "Please select a project folder first.")
            return None

        if not os.path.isdir(folder):
            QMessageBox.warning(self, "Invalid Folder", "Selected project folder does not exist.")
            return None

        return folder

    def validate_owner_repo(self):
        owner = self.upload_owner_input.text().strip()
        repo = self.repo_name_input.text().strip()

        if not owner:
            QMessageBox.warning(self, "Missing Owner", "Please enter GitHub owner.")
            return None, None

        if not repo:
            QMessageBox.warning(self, "Missing Repository Name", "Please enter repository name.")
            return None, None

        return owner, repo

    # ============================================================
    # Page 1: Repository List
    # ============================================================

    def build_repo_list_page(self):
        main_layout = QVBoxLayout(self.page_repo_list)

        top_box = QGroupBox("Repository List")
        top_layout = QGridLayout(top_box)

        self.list_owner_input = QLineEdit(DEFAULT_OWNER)
        self.repo_search_input = QLineEdit()
        self.repo_search_input.setPlaceholderText("Search repo name...")

        self.refresh_repo_btn = QPushButton("Refresh Repo List")
        self.list_check_login_btn = QPushButton("Check GitHub Login")
        self.list_login_btn = QPushButton("Login")

        top_layout.addWidget(QLabel("GitHub Owner:"), 0, 0)
        top_layout.addWidget(self.list_owner_input, 0, 1)
        top_layout.addWidget(self.refresh_repo_btn, 0, 2)
        top_layout.addWidget(self.list_check_login_btn, 0, 3)
        top_layout.addWidget(self.list_login_btn, 0, 4)

        top_layout.addWidget(QLabel("Search:"), 1, 0)
        top_layout.addWidget(self.repo_search_input, 1, 1, 1, 4)

        main_layout.addWidget(top_box)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self.repo_table = QTableWidget()
        self.repo_table.setColumnCount(4)
        self.repo_table.setHorizontalHeaderLabels([
            "Repo Name",
            "Visibility",
            "Updated At",
            "URL",
        ])
        self.repo_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.repo_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.repo_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.repo_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.repo_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.repo_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.repo_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.repo_table.customContextMenuRequested.connect(self.show_repo_table_context_menu)

        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)

        detail_btn_layout = QHBoxLayout()

        self.open_browser_btn = QPushButton("Open Repo in Browser")
        self.copy_url_btn = QPushButton("Copy Repo URL")
        self.use_repo_btn = QPushButton("Use This Repo as Target")
        self.load_files_btn = QPushButton("Load All Files")
        self.download_zip_btn = QPushButton("Download All as ZIP")
        self.open_selected_file_btn = QPushButton("Open Selected Item in GitHub")

        detail_btn_layout.addWidget(self.open_browser_btn)
        detail_btn_layout.addWidget(self.copy_url_btn)
        detail_btn_layout.addWidget(self.use_repo_btn)
        detail_btn_layout.addWidget(self.load_files_btn)
        detail_btn_layout.addWidget(self.download_zip_btn)
        detail_btn_layout.addWidget(self.open_selected_file_btn)
        detail_btn_layout.addStretch()

        detail_layout.addLayout(detail_btn_layout)

        self.repo_detail_tree = QTreeWidget()
        self.repo_detail_tree.setColumnCount(5)
        self.repo_detail_tree.setHeaderLabels([
            "Name",
            "Type",
            "Size",
            "Status",
            "URL",
        ])
        self.repo_detail_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.repo_detail_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.repo_detail_tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.repo_detail_tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.repo_detail_tree.header().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.repo_detail_tree.setAlternatingRowColors(True)
        self.repo_detail_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.repo_detail_tree.customContextMenuRequested.connect(self.show_repo_detail_context_menu)
        self.repo_detail_tree.itemChanged.connect(self.on_repo_detail_item_changed)
        self.repo_detail_tree.itemDoubleClicked.connect(self.repo_detail_item_double_clicked)

        detail_layout.addWidget(self.repo_detail_tree)

        splitter.addWidget(self.repo_table)
        splitter.addWidget(detail_widget)
        splitter.setSizes([330, 460])

        main_layout.addWidget(splitter)

        self.refresh_repo_btn.clicked.connect(self.refresh_repo_list)
        self.repo_search_input.textChanged.connect(self.filter_repo_table)
        self.open_browser_btn.clicked.connect(self.open_selected_repo_in_browser)
        self.copy_url_btn.clicked.connect(self.copy_selected_repo_url)
        self.use_repo_btn.clicked.connect(self.use_selected_repo_as_target)
        self.list_check_login_btn.clicked.connect(self.check_github_login)
        self.list_login_btn.clicked.connect(self.github_login)
        self.load_files_btn.clicked.connect(self.load_selected_repo_all_files)
        self.download_zip_btn.clicked.connect(self.download_selected_repo_all_as_zip)
        self.open_selected_file_btn.clicked.connect(self.open_current_repo_detail_item_in_github)

        self.repo_table.cellClicked.connect(self.repo_table_cell_clicked)

    def repo_table_cell_clicked(self, row, col):
        if col == 0:
            self.load_selected_repo_all_files()
        elif col == 3:
            self.open_selected_repo_in_browser()

    def show_repo_table_context_menu(self, position):
        item = self.repo_table.itemAt(position)

        if item is None:
            return

        row = item.row()
        self.repo_table.selectRow(row)

        menu = QMenu(self)

        open_action = QAction("Open Repo", self)
        save_action = QAction("Download All as ZIP", self)

        open_action.triggered.connect(self.open_selected_repo_in_browser)
        save_action.triggered.connect(self.download_selected_repo_all_as_zip)

        menu.addAction(open_action)
        menu.addAction(save_action)

        menu.exec(self.repo_table.viewport().mapToGlobal(position))

    def show_repo_detail_context_menu(self, position):
        item = self.repo_detail_tree.itemAt(position)

        if item is None:
            return

        self.repo_detail_tree.setCurrentItem(item)

        menu = QMenu(self)

        open_action = QAction("Open in GitHub", self)
        check_action = QAction("Check This Item", self)
        uncheck_action = QAction("Uncheck This Item", self)
        expand_action = QAction("Expand", self)
        collapse_action = QAction("Collapse", self)
        save_action = QAction("Save", self)

        open_action.triggered.connect(lambda: self.open_repo_detail_item_in_github(item))
        check_action.triggered.connect(lambda: item.setCheckState(0, Qt.CheckState.Checked))
        uncheck_action.triggered.connect(lambda: item.setCheckState(0, Qt.CheckState.Unchecked))
        expand_action.triggered.connect(lambda: item.setExpanded(True))
        collapse_action.triggered.connect(lambda: item.setExpanded(False))
        save_action.triggered.connect(lambda: self.save_repo_detail_item(item))

        menu.addAction(open_action)
        menu.addSeparator()
        menu.addAction(check_action)
        menu.addAction(uncheck_action)
        menu.addSeparator()
        menu.addAction(expand_action)
        menu.addAction(collapse_action)
        menu.addSeparator()
        menu.addAction(save_action)

        menu.exec(self.repo_detail_tree.viewport().mapToGlobal(position))

    def get_selected_repo_row(self):
        selected = self.repo_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "No Repository Selected", "Please select one repository first.")
            return None

        row = selected[0].row()

        name_item = self.repo_table.item(row, 0)
        url_item = self.repo_table.item(row, 3)

        if not name_item or not url_item:
            return None

        return {
            "name": name_item.text(),
            "url": url_item.text(),
        }

    def refresh_repo_list(self):
        owner = self.list_owner_input.text().strip()

        if not owner:
            QMessageBox.warning(self, "Missing Owner", "Please enter GitHub owner.")
            return

        self.log_title("Refresh GitHub Repository List")

        result = self.run_command([
            "gh",
            "repo",
            "list",
            owner,
            "--limit",
            "100",
            "--json",
            "name,visibility,url,updatedAt",
        ])

        if result is None or result.returncode != 0:
            QMessageBox.warning(self, "Repo List Failed", "Cannot load repository list.")
            return

        try:
            repos = json.loads(result.stdout)
        except Exception as e:
            self.log(f"JSON parse error: {e}", error=True)
            QMessageBox.warning(self, "JSON Error", "Cannot parse gh repo list JSON output.")
            return

        self.repo_rows = repos
        self.populate_repo_table(repos)

    def populate_repo_table(self, repos):
        self.repo_table.setRowCount(0)

        for repo in repos:
            row = self.repo_table.rowCount()
            self.repo_table.insertRow(row)

            self.repo_table.setItem(row, 0, QTableWidgetItem(repo.get("name", "")))
            self.repo_table.setItem(row, 1, QTableWidgetItem(repo.get("visibility", "")))
            self.repo_table.setItem(row, 2, QTableWidgetItem(repo.get("updatedAt", "")))
            self.repo_table.setItem(row, 3, QTableWidgetItem(repo.get("url", "")))

        self.filter_repo_table()
        self.log(f"Loaded {len(repos)} repositories.")

    def filter_repo_table(self):
        keyword = self.repo_search_input.text().strip().lower()

        for row in range(self.repo_table.rowCount()):
            item = self.repo_table.item(row, 0)
            repo_name = item.text().lower() if item else ""
            self.repo_table.setRowHidden(row, keyword not in repo_name)

    def open_selected_repo_in_browser(self):
        repo = self.get_selected_repo_row()
        if not repo:
            return

        webbrowser.open(repo["url"])
        self.log(f"Opened browser: {repo['url']}")

    def copy_selected_repo_url(self):
        repo = self.get_selected_repo_row()
        if not repo:
            return

        QApplication.clipboard().setText(repo["url"])
        self.log(f"Copied repo URL: {repo['url']}")

    def use_selected_repo_as_target(self):
        repo = self.get_selected_repo_row()
        if not repo:
            return

        owner = self.list_owner_input.text().strip() or DEFAULT_OWNER

        self.upload_owner_input.setText(owner)
        self.repo_name_input.setText(repo["name"])

        self.tabs.setCurrentWidget(self.page_upload)

        self.log_title("Use Selected Repository as Target")
        self.log(f"Owner: {owner}")
        self.log(f"Repository: {repo['name']}")

    def load_selected_repo_all_files(self):
        repo = self.get_selected_repo_row()
        if not repo:
            return

        owner = self.list_owner_input.text().strip() or DEFAULT_OWNER
        repo_name = repo["name"]

        self.current_repo_owner = owner
        self.current_repo_name = repo_name

        self.repo_detail_tree.clear()

        self.log_title(f"Load All Files: {owner}/{repo_name}")

        source_root = self.create_repo_detail_root(
            "Repository Source",
            "folder",
            "",
            "source root",
            f"https://github.com/{owner}/{repo_name}",
            checked=True,
        )

        releases_root = self.create_repo_detail_root(
            "Releases",
            "folder",
            "",
            "release root",
            f"https://github.com/{owner}/{repo_name}/releases",
            checked=True,
        )

        packages_root = self.create_repo_detail_root(
            "Packages",
            "folder",
            "",
            "package root",
            f"https://github.com/users/{owner}/packages",
            checked=False,
        )

        default_branch = self.get_default_branch(owner, repo_name)

        if default_branch:
            self.load_repo_source_files_to_tree(owner, repo_name, default_branch, source_root)

        self.load_releases_to_tree(owner, repo_name, releases_root)
        self.load_packages_to_tree(owner, repo_name, packages_root)

        self.repo_detail_tree.expandToDepth(1)
        self.refresh_repo_detail_all_parent_states()

        self.log("Load All Files completed.")

    def create_repo_detail_root(self, name, ftype, size, status, url, checked=True):
        item = QTreeWidgetItem(self.repo_detail_tree)
        item.setText(0, name)
        item.setText(1, ftype)
        item.setText(2, size)
        item.setText(3, status)
        item.setText(4, url)

        item.setData(0, ROLE_PATH, name)
        item.setData(0, ROLE_KIND, "folder")
        item.setData(0, ROLE_URL, url)
        item.setData(0, ROLE_TYPE, ftype)
        item.setData(0, ROLE_DOWNLOADABLE, False)

        item.setFlags(
            item.flags()
            | Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
        )

        item.setCheckState(0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

        try:
            item.setIcon(0, self.icon_provider.icon(QFileIconProvider.IconType.Folder))
        except Exception:
            pass

        return item

    def create_repo_detail_child(
        self,
        parent,
        name,
        ftype,
        size,
        status,
        url,
        rel_path,
        kind="file",
        downloadable=True,
        checked=True,
    ):
        item = QTreeWidgetItem(parent)

        item.setText(0, name)
        item.setText(1, ftype)
        item.setText(2, size)
        item.setText(3, status)
        item.setText(4, url)

        item.setData(0, ROLE_PATH, rel_path)
        item.setData(0, ROLE_KIND, kind)
        item.setData(0, ROLE_URL, url)
        item.setData(0, ROLE_TYPE, ftype)
        item.setData(0, ROLE_DOWNLOADABLE, downloadable)

        item.setFlags(
            item.flags()
            | Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
        )

        item.setCheckState(0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

        try:
            if kind == "folder":
                item.setIcon(0, self.icon_provider.icon(QFileIconProvider.IconType.Folder))
            else:
                fake_info = QFileInfo(name)
                item.setIcon(0, self.icon_provider.icon(fake_info))
        except Exception:
            pass

        return item

    def find_child_by_name_and_kind(self, parent, name, kind):
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.text(0) == name and child.data(0, ROLE_KIND) == kind:
                return child
        return None

    def add_source_path_to_repo_tree(self, source_root, owner, repo_name, branch, path, ftype, size):
        parts = path.split("/")
        parent = source_root
        current_path = ""

        for index, part in enumerate(parts):
            current_path = part if not current_path else f"{current_path}/{part}"
            is_last = index == len(parts) - 1

            if not is_last:
                existing = self.find_child_by_name_and_kind(parent, part, "folder")

                if existing:
                    parent = existing
                else:
                    folder_url = f"https://github.com/{owner}/{repo_name}/tree/{branch}/{current_path}"
                    parent = self.create_repo_detail_child(
                        parent=parent,
                        name=part,
                        ftype="source:tree",
                        size="",
                        status="folder",
                        url=folder_url,
                        rel_path=current_path,
                        kind="folder",
                        downloadable=False,
                        checked=True,
                    )

            else:
                existing = self.find_child_by_name_and_kind(
                    parent,
                    part,
                    "folder" if ftype == "tree" else "file",
                )
                if existing:
                    return

                if ftype == "tree":
                    url = f"https://github.com/{owner}/{repo_name}/tree/{branch}/{current_path}"
                    self.create_repo_detail_child(
                        parent=parent,
                        name=part,
                        ftype="source:tree",
                        size="",
                        status="folder",
                        url=url,
                        rel_path=current_path,
                        kind="folder",
                        downloadable=False,
                        checked=True,
                    )
                else:
                    url = f"https://github.com/{owner}/{repo_name}/blob/{branch}/{current_path}"
                    self.create_repo_detail_child(
                        parent=parent,
                        name=part,
                        ftype="source:blob",
                        size=size,
                        status="file",
                        url=url,
                        rel_path=current_path,
                        kind="file",
                        downloadable=True,
                        checked=True,
                    )

    def get_default_branch(self, owner, repo_name):
        branch_result = self.run_command([
            "gh",
            "repo",
            "view",
            f"{owner}/{repo_name}",
            "--json",
            "defaultBranchRef",
        ], title="Get Default Branch")

        if branch_result is None or branch_result.returncode != 0:
            QMessageBox.warning(self, "Failed", "Cannot get default branch.")
            return None

        try:
            branch_json = json.loads(branch_result.stdout)
            return branch_json.get("defaultBranchRef", {}).get("name", "main")
        except Exception as e:
            self.log(f"Parse default branch failed: {e}", error=True)
            return "main"

    def load_repo_source_files_to_tree(self, owner, repo_name, default_branch, source_root):
        self.log_title("Load Repository Source Files")

        tree_result = self.run_command([
            "gh",
            "api",
            f"repos/{owner}/{repo_name}/git/trees/{default_branch}?recursive=1",
        ])

        if tree_result is None or tree_result.returncode != 0:
            self.log("Cannot load repository source files.", error=True)
            return

        try:
            tree_json = json.loads(tree_result.stdout)
            files = tree_json.get("tree", [])

            count = 0

            for f in files:
                path = f.get("path", "")
                ftype = f.get("type", "")
                size = format_bytes(f.get("size", "")) if f.get("size") is not None else ""

                if not path:
                    continue

                self.add_source_path_to_repo_tree(
                    source_root=source_root,
                    owner=owner,
                    repo_name=repo_name,
                    branch=default_branch,
                    path=path,
                    ftype=ftype,
                    size=size,
                )
                count += 1

            self.log(f"Loaded repository source files/folders: {count}")

        except Exception as e:
            self.log(f"Parse repo tree failed: {e}", error=True)

    def load_packages_to_tree(self, owner, repo_name, packages_root):
        self.log_title("Load GitHub Packages")

        package_types = ["container", "npm", "maven", "rubygems", "nuget"]
        total = 0

        for package_type in package_types:
            type_root = self.create_repo_detail_child(
                parent=packages_root,
                name=package_type,
                ftype=f"package:{package_type}",
                size="",
                status="package type",
                url=f"https://github.com/users/{owner}/packages/{package_type}",
                rel_path=f"Packages/{package_type}",
                kind="folder",
                downloadable=False,
                checked=False,
            )

            result = self.run_command([
                "gh",
                "api",
                f"users/{owner}/packages?package_type={package_type}",
            ], title=f"Check Packages: {package_type}")

            if result is None or result.returncode != 0:
                continue

            try:
                packages = json.loads(result.stdout)
            except Exception:
                continue

            for pkg in packages:
                name = pkg.get("name", "")
                html_url = pkg.get("html_url", "")

                if not html_url:
                    html_url = f"https://github.com/users/{owner}/packages/{package_type}/package/{name}"

                self.create_repo_detail_child(
                    parent=type_root,
                    name=name,
                    ftype=f"package:{package_type}",
                    size="",
                    status="open only",
                    url=html_url,
                    rel_path=f"Packages/{package_type}/{name}",
                    kind="file",
                    downloadable=False,
                    checked=False,
                )
                total += 1

        self.log(f"Loaded GitHub packages: {total}")

    def load_releases_to_tree(self, owner, repo_name, releases_root):
        self.log_title("Load GitHub Releases")

        result = self.run_command([
            "gh",
            "api",
            f"repos/{owner}/{repo_name}/releases",
        ])

        if result is None or result.returncode != 0:
            self.log("No releases found or cannot load releases.", error=True)
            return

        try:
            releases = json.loads(result.stdout)
        except Exception as e:
            self.log(f"Parse releases failed: {e}", error=True)
            return

        total = 0

        for release in releases:
            tag_name = release.get("tag_name", "")
            release_name = release.get("name", "") or tag_name
            html_url = release.get("html_url", "")

            release_folder = self.create_repo_detail_child(
                parent=releases_root,
                name=release_name,
                ftype="release",
                size="",
                status=tag_name,
                url=html_url,
                rel_path=f"Releases/{tag_name}",
                kind="folder",
                downloadable=False,
                checked=True,
            )

            zipball_url = release.get("zipball_url", "")
            tarball_url = release.get("tarball_url", "")

            if zipball_url:
                self.create_repo_detail_child(
                    parent=release_folder,
                    name=f"{tag_name}_source_code.zip",
                    ftype="release:zipball",
                    size="",
                    status="source zip",
                    url=zipball_url,
                    rel_path=f"Releases/{tag_name}/{tag_name}_source_code.zip",
                    kind="file",
                    downloadable=True,
                    checked=True,
                )
                total += 1

            if tarball_url:
                self.create_repo_detail_child(
                    parent=release_folder,
                    name=f"{tag_name}_source_code.tar.gz",
                    ftype="release:tarball",
                    size="",
                    status="source tar.gz",
                    url=tarball_url,
                    rel_path=f"Releases/{tag_name}/{tag_name}_source_code.tar.gz",
                    kind="file",
                    downloadable=True,
                    checked=True,
                )
                total += 1

            assets = release.get("assets", [])

            if assets:
                assets_folder = self.create_repo_detail_child(
                    parent=release_folder,
                    name="assets",
                    ftype="release:assets",
                    size="",
                    status="folder",
                    url=html_url,
                    rel_path=f"Releases/{tag_name}/assets",
                    kind="folder",
                    downloadable=False,
                    checked=True,
                )

                for asset in assets:
                    asset_name = asset.get("name", "")
                    size = format_bytes(asset.get("size", ""))
                    browser_download_url = asset.get("browser_download_url", "")

                    self.create_repo_detail_child(
                        parent=assets_folder,
                        name=asset_name,
                        ftype="release:asset",
                        size=size,
                        status="asset",
                        url=browser_download_url,
                        rel_path=f"Releases/{tag_name}/assets/{asset_name}",
                        kind="file",
                        downloadable=True,
                        checked=True,
                    )
                    total += 1

            body = release.get("body", "") or ""
            body_links = extract_links_from_release_body(body)

            if body_links:
                body_folder = self.create_repo_detail_child(
                    parent=release_folder,
                    name="body_download_links",
                    ftype="release:body-links",
                    size="",
                    status="folder",
                    url=html_url,
                    rel_path=f"Releases/{tag_name}/body_download_links",
                    kind="folder",
                    downloadable=False,
                    checked=True,
                )

                for link in body_links:
                    label = link.get("label", "")
                    url = link.get("url", "")

                    if not url:
                        continue

                    filename = filename_from_url_or_label(url, label)

                    self.create_repo_detail_child(
                        parent=body_folder,
                        name=filename,
                        ftype="release:body-link",
                        size="",
                        status="body link",
                        url=url,
                        rel_path=f"Releases/{tag_name}/body_download_links/{filename}",
                        kind="file",
                        downloadable=True,
                        checked=True,
                    )
                    total += 1

        self.log(f"Loaded release records/assets/body links: {total}")

    def on_repo_detail_item_changed(self, item, column):
        if self._updating_tree_checks:
            return

        if column != 0:
            return

        self._updating_tree_checks = True

        state = item.checkState(0)
        self.apply_repo_detail_check_to_children(item, state)
        self.update_repo_detail_parent_check_states(item)

        self._updating_tree_checks = False

    def apply_repo_detail_check_to_children(self, item, state):
        for i in range(item.childCount()):
            child = item.child(i)
            child.setCheckState(0, state)

            if child.childCount() > 0:
                self.apply_repo_detail_check_to_children(child, state)

    def update_repo_detail_parent_check_states(self, item):
        parent = item.parent()

        while parent is not None:
            checked = 0
            unchecked = 0
            partial = 0

            for i in range(parent.childCount()):
                state = parent.child(i).checkState(0)

                if state == Qt.CheckState.Checked:
                    checked += 1
                elif state == Qt.CheckState.Unchecked:
                    unchecked += 1
                else:
                    partial += 1

            if partial > 0 or (checked > 0 and unchecked > 0):
                parent.setCheckState(0, Qt.CheckState.PartiallyChecked)
            elif checked > 0 and unchecked == 0:
                parent.setCheckState(0, Qt.CheckState.Checked)
            else:
                parent.setCheckState(0, Qt.CheckState.Unchecked)

            parent = parent.parent()

    def refresh_repo_detail_all_parent_states(self):
        self._updating_tree_checks = True

        for i in range(self.repo_detail_tree.topLevelItemCount()):
            self.refresh_repo_detail_item_state(self.repo_detail_tree.topLevelItem(i))

        self._updating_tree_checks = False

    def refresh_repo_detail_item_state(self, item):
        if item.childCount() == 0:
            return item.checkState(0)

        checked = 0
        unchecked = 0
        partial = 0

        for i in range(item.childCount()):
            state = self.refresh_repo_detail_item_state(item.child(i))

            if state == Qt.CheckState.Checked:
                checked += 1
            elif state == Qt.CheckState.Unchecked:
                unchecked += 1
            else:
                partial += 1

        if partial > 0 or (checked > 0 and unchecked > 0):
            item.setCheckState(0, Qt.CheckState.PartiallyChecked)
        elif checked > 0 and unchecked == 0:
            item.setCheckState(0, Qt.CheckState.Checked)
        else:
            item.setCheckState(0, Qt.CheckState.Unchecked)

        return item.checkState(0)

    def repo_detail_item_double_clicked(self, item, column):
        self.open_repo_detail_item_in_github(item)

    def open_current_repo_detail_item_in_github(self):
        item = self.repo_detail_tree.currentItem()
        if not item:
            QMessageBox.warning(self, "No Item Selected", "Please select one item first.")
            return
        self.open_repo_detail_item_in_github(item)

    def open_repo_detail_item_in_github(self, item):
        url = item.data(0, ROLE_URL)

        if not url:
            QMessageBox.warning(self, "No URL", "Selected item does not have GitHub URL.")
            return

        webbrowser.open(url)
        self.log(f"Opened: {url}")

    def collect_downloadable_repo_detail_items(self, item, output):
        state = item.checkState(0)
        downloadable = bool(item.data(0, ROLE_DOWNLOADABLE))

        if downloadable and state == Qt.CheckState.Checked:
            output.append(item)

        for i in range(item.childCount()):
            self.collect_downloadable_repo_detail_items(item.child(i), output)

    def save_repo_detail_item(self, item):
        kind = item.data(0, ROLE_KIND)
        downloadable = bool(item.data(0, ROLE_DOWNLOADABLE))

        if kind == "folder":
            self.save_repo_detail_folder_as_zip(item)
            return

        if not downloadable:
            QMessageBox.information(
                self,
                "Open Only",
                "This item is not a direct downloadable file.\nPlease use Open in GitHub instead.",
            )
            return

        self.save_repo_detail_single_file(item)

    def save_repo_detail_single_file(self, item):
        ftype = item.data(0, ROLE_TYPE) or ""
        url = item.data(0, ROLE_URL) or ""
        rel_path = item.data(0, ROLE_PATH) or item.text(0)

        if not url:
            QMessageBox.warning(self, "No URL", "Selected item does not have URL.")
            return

        download_url = url

        if ftype == "source:blob" and "github.com" in url and "/blob/" in url:
            download_url = self.github_blob_url_to_raw(url)

        default_name = self.suggest_filename_from_detail(ftype, rel_path, download_url)

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            default_name,
            "All Files (*.*)",
        )

        if not save_path:
            return

        download_dialog = DownloadStatusDialog(self, "Save File Download Status")
        download_dialog.show()

        ok = self.download_url_to_file(
            download_url,
            save_path,
            title=f"Save: {os.path.basename(save_path)}",
            dialog=download_dialog,
        )

        if ok:
            QMessageBox.information(self, "Saved", f"File saved:\n{save_path}")
        else:
            QMessageBox.warning(self, "Save Failed", "Failed to save selected file.")

    def save_repo_detail_folder_as_zip(self, item):
        downloadable_items = []
        self.collect_downloadable_repo_detail_items(item, downloadable_items)

        if not downloadable_items:
            QMessageBox.information(
                self,
                "No Downloadable Files",
                "This folder has no checked downloadable files.",
            )
            return

        folder_name = safe_filename(item.text(0))
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Folder as ZIP",
            f"{folder_name}.zip",
            "Zip Files (*.zip)",
        )

        if not save_path:
            return

        temp_dir = tempfile.mkdtemp(prefix="repo_detail_folder_")
        base_dir = os.path.join(temp_dir, folder_name)
        os.makedirs(base_dir, exist_ok=True)

        download_dialog = DownloadStatusDialog(self, "Save Folder Download Status")
        download_dialog.show()

        try:
            total = len(downloadable_items)

            for index, child in enumerate(downloadable_items, start=1):
                ftype = child.data(0, ROLE_TYPE) or ""
                url = child.data(0, ROLE_URL) or ""
                rel_path = child.data(0, ROLE_PATH) or child.text(0)

                if not url:
                    continue

                download_url = url

                if ftype == "source:blob" and "github.com" in url and "/blob/" in url:
                    download_url = self.github_blob_url_to_raw(url)

                safe_rel = rel_path.replace("\\", "/")

                if "/" in safe_rel:
                    safe_rel_parts = [safe_filename(x) for x in safe_rel.split("/") if x.strip()]
                    safe_rel = os.path.join(*safe_rel_parts)
                else:
                    safe_rel = safe_filename(safe_rel)

                output_file = os.path.join(base_dir, safe_rel)
                os.makedirs(os.path.dirname(output_file), exist_ok=True)

                download_dialog.set_stage(f"Downloading {index}/{total}: {child.text(0)}")

                self.download_url_to_file(
                    download_url,
                    output_file,
                    title=f"Download folder file: {child.text(0)}",
                    dialog=download_dialog,
                )

            download_dialog.set_stage("Creating ZIP...")

            base_without_ext = save_path[:-4] if save_path.lower().endswith(".zip") else save_path
            zip_file = shutil.make_archive(base_without_ext, "zip", base_dir)

            download_dialog.finish_success("Folder ZIP completed")

            QMessageBox.information(
                self,
                "Saved",
                f"Folder saved as ZIP:\n{zip_file}",
            )

        except Exception as e:
            download_dialog.finish_failed(str(e))
            self.log(f"Save folder ZIP failed: {e}", error=True)
            QMessageBox.warning(self, "Save Failed", str(e))

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def github_blob_url_to_raw(self, url):
        try:
            parsed = urlparse(url)
            parts = parsed.path.strip("/").split("/")

            if len(parts) >= 5 and parts[2] == "blob":
                owner = parts[0]
                repo = parts[1]
                branch = parts[3]
                file_path = "/".join(parts[4:])

                return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"

        except Exception as e:
            self.log(f"Convert blob URL failed: {e}", error=True)

        return url

    def suggest_filename_from_detail(self, ftype, display_path, url):
        if ftype in ["release:body-link", "release:asset"]:
            label = display_path.split("/", 1)[-1].strip()
            return filename_from_url_or_label(url, label)

        if ftype == "release:zipball":
            return safe_filename(display_path.replace("/", "_")) + ".zip"

        if ftype == "release:tarball":
            return safe_filename(display_path.replace("/", "_")) + ".tar.gz"

        if display_path:
            filename = os.path.basename(display_path)
            if filename:
                return safe_filename(filename)

        return filename_from_url_or_label(url, "")

    def download_selected_repo_all_as_zip(self):
        repo = self.get_selected_repo_row()
        if not repo:
            return

        owner = self.list_owner_input.text().strip() or DEFAULT_OWNER
        repo_name = repo["name"]

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save All Repository Files ZIP",
            f"{repo_name}_all_files.zip",
            "Zip Files (*.zip)",
        )

        if not save_path:
            return

        self.log_title(f"Download All as ZIP: {owner}/{repo_name}")

        download_dialog = DownloadStatusDialog(self, "Download All as ZIP Status")
        download_dialog.show()
        download_dialog.set_stage("Preparing download...")

        temp_dir = tempfile.mkdtemp(prefix="github_sync_all_")
        bundle_dir = os.path.join(temp_dir, f"{repo_name}_all_files")

        source_dir = os.path.join(bundle_dir, "01_repository_source")
        releases_dir = os.path.join(bundle_dir, "02_releases")
        packages_dir = os.path.join(bundle_dir, "03_packages_manifest")

        os.makedirs(source_dir, exist_ok=True)
        os.makedirs(releases_dir, exist_ok=True)
        os.makedirs(packages_dir, exist_ok=True)

        try:
            clone_target = os.path.join(source_dir, repo_name)

            download_dialog.set_stage("Downloading repository source...")

            clone_result = self.run_command([
                "gh",
                "repo",
                "clone",
                f"{owner}/{repo_name}",
                clone_target,
            ], title="Download repository source")

            if clone_result is None or clone_result.returncode != 0:
                download_dialog.finish_failed("Download failed")
                QMessageBox.warning(
                    self,
                    "Clone Failed",
                    "Cannot clone repository source.",
                )
                return

            git_dir = os.path.join(clone_target, ".git")
            if os.path.isdir(git_dir):
                shutil.rmtree(git_dir, ignore_errors=True)

            download_dialog.set_stage("Repository source downloaded")

            releases_result = self.run_command([
                "gh",
                "api",
                f"repos/{owner}/{repo_name}/releases",
            ], title="Load release metadata")

            releases = []

            if releases_result is not None and releases_result.returncode == 0:
                try:
                    releases = json.loads(releases_result.stdout)
                except Exception as e:
                    self.log(f"Parse releases failed: {e}", error=True)
                    releases = []
            else:
                self.log("No releases found or cannot load releases.", error=True)

            download_dialog.set_stage("Release metadata loaded")

            release_manifest = []

            for release_index, release in enumerate(releases, start=1):
                tag_name = release.get("tag_name", "")
                release_name = release.get("name", "") or tag_name
                html_url = release.get("html_url", "")
                assets = release.get("assets", [])
                body = release.get("body", "") or ""
                body_links = extract_links_from_release_body(body)

                if not tag_name:
                    continue

                safe_tag = safe_filename(tag_name)
                release_folder = os.path.join(releases_dir, safe_tag)
                os.makedirs(release_folder, exist_ok=True)

                info = {
                    "tag_name": tag_name,
                    "release_name": release_name,
                    "html_url": html_url,
                    "asset_count": len(assets),
                    "body_link_count": len(body_links),
                    "assets": [],
                    "body_links": [],
                }

                release_info_path = os.path.join(release_folder, "release_info.json")
                with open(release_info_path, "w", encoding="utf-8") as f:
                    json.dump(release, f, indent=2, ensure_ascii=False)

                self.log_title(f"Download release: {tag_name}")

                if assets:
                    download_dialog.set_stage(f"Downloading release assets: {tag_name}")

                    asset_result = self.run_command([
                        "gh",
                        "release",
                        "download",
                        tag_name,
                        "--repo",
                        f"{owner}/{repo_name}",
                        "--dir",
                        release_folder,
                        "--clobber",
                    ], title=f"Download release assets: {tag_name}")

                    if asset_result is None or asset_result.returncode != 0:
                        self.log(f"Release asset download failed: {tag_name}", error=True)

                    for asset in assets:
                        info["assets"].append({
                            "name": asset.get("name", ""),
                            "size": asset.get("size", ""),
                            "browser_download_url": asset.get("browser_download_url", ""),
                        })
                else:
                    self.log(f"No uploaded assets for release: {tag_name}")

                if body_links:
                    body_files_dir = os.path.join(release_folder, "body_download_links")
                    os.makedirs(body_files_dir, exist_ok=True)

                    self.log_title(f"Download release body links: {tag_name}")

                    for idx, link in enumerate(body_links, start=1):
                        label = link.get("label", "")
                        url = link.get("url", "")

                        if not url:
                            continue

                        filename = filename_from_url_or_label(url, label)

                        final_name = filename
                        final_path = os.path.join(body_files_dir, final_name)

                        if os.path.exists(final_path):
                            stem = Path(filename).stem
                            suffix = Path(filename).suffix
                            final_name = f"{stem}_{idx}{suffix}"
                            final_path = os.path.join(body_files_dir, final_name)

                        ok = self.download_url_to_file(
                            url,
                            final_path,
                            title=f"Download body file: {final_name}",
                            dialog=download_dialog,
                        )

                        info["body_links"].append({
                            "label": label,
                            "url": url,
                            "saved_as": final_name if ok else "",
                            "downloaded": ok,
                        })
                else:
                    self.log(f"No body download links for release: {tag_name}")

                download_dialog.set_stage(f"Downloading release source ZIP: {tag_name}")

                zip_output = os.path.join(release_folder, f"{safe_tag}_source_code.zip")
                zip_result = self.run_command_to_file([
                    "gh",
                    "api",
                    f"repos/{owner}/{repo_name}/zipball/{tag_name}",
                ], zip_output, title=f"Download release source ZIP: {tag_name}")

                if zip_result is None or zip_result.returncode != 0:
                    self.log(f"Cannot download source zip for {tag_name}", error=True)
                    if os.path.exists(zip_output):
                        try:
                            os.remove(zip_output)
                        except Exception:
                            pass

                download_dialog.set_stage(f"Downloading release source TAR.GZ: {tag_name}")

                tar_output = os.path.join(release_folder, f"{safe_tag}_source_code.tar.gz")
                tar_result = self.run_command_to_file([
                    "gh",
                    "api",
                    f"repos/{owner}/{repo_name}/tarball/{tag_name}",
                ], tar_output, title=f"Download release source TAR.GZ: {tag_name}")

                if tar_result is None or tar_result.returncode != 0:
                    self.log(f"Cannot download source tarball for {tag_name}", error=True)
                    if os.path.exists(tar_output):
                        try:
                            os.remove(tar_output)
                        except Exception:
                            pass

                release_manifest.append(info)

            package_manifest = self.collect_packages_manifest(owner)

            package_manifest_path = os.path.join(packages_dir, "packages_manifest.json")
            with open(package_manifest_path, "w", encoding="utf-8") as f:
                json.dump(package_manifest, f, indent=2, ensure_ascii=False)

            self.log("Packages manifest saved.")
            self.log(package_manifest_path)
            download_dialog.set_stage("Packages manifest saved")

            manifest = {
                "owner": owner,
                "repository": repo_name,
                "repository_url": repo.get("url", ""),
                "included": [
                    "current repository source code",
                    "release uploaded assets",
                    "release body markdown download links",
                    "release generated source zip",
                    "release generated source tar.gz",
                    "release_info.json",
                    "packages_manifest.json",
                ],
                "note": (
                    "GitHub Packages are saved as manifest only because different "
                    "package types require different download methods. Release body links "
                    "are downloaded into body_download_links folder."
                ),
                "release_count": len(releases),
                "releases": release_manifest,
            }

            manifest_path = os.path.join(bundle_dir, "download_manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)

            download_dialog.set_stage("Creating final ZIP...")

            base_without_ext = save_path[:-4] if save_path.lower().endswith(".zip") else save_path

            zip_file = shutil.make_archive(
                base_without_ext,
                "zip",
                bundle_dir,
            )

            download_dialog.finish_success("Download All completed")
            self.log_title("Download All Completed")
            self.log(f"ZIP saved: {zip_file}")

            QMessageBox.information(
                self,
                "Download All Complete",
                f"All repository files downloaded and packed:\n{zip_file}",
            )

        except Exception as e:
            download_dialog.finish_failed("Download failed")
            self.log(f"Download All failed: {e}", error=True)
            QMessageBox.warning(self, "Download All Failed", str(e))

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def collect_packages_manifest(self, owner):
        self.log_title("Collect Packages Manifest")

        package_types = ["container", "npm", "maven", "rubygems", "nuget"]
        all_packages = []

        for package_type in package_types:
            result = self.run_command([
                "gh",
                "api",
                f"users/{owner}/packages?package_type={package_type}",
            ], title=f"Collect packages: {package_type}")

            if result is None or result.returncode != 0:
                continue

            try:
                packages = json.loads(result.stdout)
            except Exception:
                continue

            for pkg in packages:
                all_packages.append({
                    "package_type": package_type,
                    "name": pkg.get("name", ""),
                    "html_url": pkg.get("html_url", ""),
                    "visibility": pkg.get("visibility", ""),
                    "updated_at": pkg.get("updated_at", ""),
                })

        self.log(f"Collected package records: {len(all_packages)}")
        return all_packages

    # ============================================================
    # Page 2: Upload New Repository
    # ============================================================

    def build_upload_page(self):
        layout = QVBoxLayout(self.page_upload)

        top_row = QHBoxLayout()

        form_box = QGroupBox("Upload / Sync Settings")
        form = QGridLayout(form_box)

        self.project_folder_input = QLineEdit()
        self.project_folder_input.setReadOnly(True)

        self.select_folder_btn = QPushButton("Select Project Folder")
        self.clear_folder_btn = QPushButton("Clear")

        self.upload_owner_input = QLineEdit(DEFAULT_OWNER)
        self.repo_name_input = QLineEdit()

        self.visibility_combo = QComboBox()
        self.visibility_combo.addItems(["Public", "Private"])

        self.commit_msg_input = QLineEdit("Initial commit")

        form.addWidget(QLabel("Project Folder:"), 0, 0)
        form.addWidget(self.project_folder_input, 0, 1, 1, 3)
        form.addWidget(self.select_folder_btn, 1, 1)
        form.addWidget(self.clear_folder_btn, 1, 2)

        form.addWidget(QLabel("GitHub Owner:"), 2, 0)
        form.addWidget(self.upload_owner_input, 2, 1, 1, 3)

        form.addWidget(QLabel("Repository Name:"), 3, 0)
        form.addWidget(self.repo_name_input, 3, 1, 1, 3)

        form.addWidget(QLabel("Visibility:"), 4, 0)
        form.addWidget(self.visibility_combo, 4, 1, 1, 3)

        form.addWidget(QLabel("Commit Message:"), 5, 0)
        form.addWidget(self.commit_msg_input, 5, 1, 1, 3)

        action_box = QGroupBox("Actions")
        action_layout = QGridLayout(action_box)

        self.check_tools_btn = QPushButton("Check Tools")
        self.upload_check_login_btn = QPushButton("Check GitHub Login")
        self.upload_login_btn = QPushButton("Login")
        self.gitignore_btn = QPushButton("Generate Safe .gitignore")
        self.status_btn = QPushButton("Check Status")
        self.scan_folder_btn = QPushButton("Refresh File Explorer")
        self.create_missing_btn = QPushButton("Create Missing Standard Files")
        self.select_all_btn = QPushButton("Select All Safe Files")
        self.unselect_risky_btn = QPushButton("Unselect Risky Files")
        self.expand_all_btn = QPushButton("Expand All")
        self.collapse_all_btn = QPushButton("Collapse All")
        self.first_upload_btn = QPushButton("One Click First Upload")
        self.update_push_btn = QPushButton("One Click Update Push")

        action_layout.addWidget(self.check_tools_btn, 0, 0)
        action_layout.addWidget(self.upload_check_login_btn, 0, 1)
        action_layout.addWidget(self.upload_login_btn, 0, 2)

        action_layout.addWidget(self.gitignore_btn, 1, 0)
        action_layout.addWidget(self.status_btn, 1, 1)
        action_layout.addWidget(self.scan_folder_btn, 1, 2)

        action_layout.addWidget(self.create_missing_btn, 2, 0)
        action_layout.addWidget(self.select_all_btn, 2, 1)
        action_layout.addWidget(self.unselect_risky_btn, 2, 2)

        action_layout.addWidget(self.expand_all_btn, 3, 0)
        action_layout.addWidget(self.collapse_all_btn, 3, 1)

        action_layout.addWidget(self.first_upload_btn, 4, 0)
        action_layout.addWidget(self.update_push_btn, 4, 1)

        top_row.addWidget(form_box, stretch=2)
        top_row.addWidget(action_box, stretch=2)

        layout.addLayout(top_row)

        splitter = QSplitter(Qt.Orientation.Vertical)

        file_box = QWidget()
        file_layout = QVBoxLayout(file_box)

        file_layout.addWidget(QLabel("Folder File Explorer - Tick files or folders you want to upload:"))

        self.folder_tree = QTreeWidget()
        self.folder_tree.setColumnCount(5)
        self.folder_tree.setHeaderLabels(["Name", "Type", "Size", "Status", "Path"])
        self.folder_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.folder_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.folder_tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.folder_tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.folder_tree.header().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.folder_tree.setAlternatingRowColors(True)
        self.folder_tree.itemChanged.connect(self.on_folder_tree_item_changed)
        self.folder_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.folder_tree.customContextMenuRequested.connect(self.show_folder_tree_context_menu)

        file_layout.addWidget(self.folder_tree)

        log_box = QWidget()
        log_layout = QVBoxLayout(log_box)

        log_layout.addWidget(QLabel("Download / Command Progress:"))

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Ready")
        log_layout.addWidget(self.progress_bar)

        log_layout.addWidget(QLabel("Output Log:"))

        self.output_log = QTextEdit()
        self.output_log.setReadOnly(True)
        self.output_log.setStyleSheet("""
            QTextEdit {
                background: #fafafa;
                color: #222;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
        """)

        log_layout.addWidget(self.output_log)

        splitter.addWidget(file_box)
        splitter.addWidget(log_box)
        splitter.setSizes([560, 260])

        layout.addWidget(splitter)

        self.select_folder_btn.clicked.connect(self.select_project_folder)
        self.clear_folder_btn.clicked.connect(self.clear_project_folder)
        self.check_tools_btn.clicked.connect(self.check_tools)
        self.upload_check_login_btn.clicked.connect(self.check_github_login)
        self.upload_login_btn.clicked.connect(self.github_login)
        self.gitignore_btn.clicked.connect(self.generate_safe_gitignore)
        self.status_btn.clicked.connect(self.check_status)
        self.scan_folder_btn.clicked.connect(self.scan_folder_files)
        self.create_missing_btn.clicked.connect(self.create_missing_standard_files)
        self.select_all_btn.clicked.connect(self.select_all_files)
        self.unselect_risky_btn.clicked.connect(self.unselect_risky_files)
        self.expand_all_btn.clicked.connect(self.folder_tree.expandAll)
        self.collapse_all_btn.clicked.connect(self.folder_tree.collapseAll)
        self.first_upload_btn.clicked.connect(self.one_click_first_upload)
        self.update_push_btn.clicked.connect(self.one_click_update_push)

    def select_project_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")

        if not folder:
            return

        self.project_folder_input.setText(folder)

        folder_name = os.path.basename(folder)
        repo_name = slugify_repo_name(folder_name)

        if not self.repo_name_input.text().strip():
            self.repo_name_input.setText(repo_name)

        self.log_title("Project Folder Selected")
        self.log(folder)
        self.log(f"Auto repository name: {repo_name}")

        self.scan_folder_files()

    def clear_project_folder(self):
        self.project_folder_input.clear()
        self.repo_name_input.clear()
        self.folder_tree.clear()

        self.log_title("Project Folder Cleared")
        self.log("Project folder, repository name, and folder file list cleared.")

    def check_tools(self):
        self.log_title("Check Tools")
        self.run_command(["git", "--version"])
        self.run_command(["gh", "--version"])

    def check_github_login(self):
        self.log_title("Check GitHub Login")

        result = self.run_command(["gh", "auth", "status"])

        if result is None or result.returncode != 0:
            QMessageBox.warning(
                self,
                "GitHub Not Logged In",
                "GitHub CLI is not logged in.\n\nClick Login and complete login.",
            )
        else:
            QMessageBox.information(self, "GitHub Login OK", "GitHub CLI login looks OK.")

    def github_login(self):
        self.log_title("GitHub Login")
        self.log("Opening Windows terminal for: gh auth login")

        try:
            subprocess.run(
                ["cmd", "/c", "start", "cmd", "/k", "gh auth login"],
                shell=False,
                capture_output=True,
                text=True,
            )
            self.log("A new terminal window was opened for GitHub login.")
            self.log("After login, click Check GitHub Login again.")
        except Exception as e:
            self.log(f"Login command failed: {e}", error=True)

    def generate_safe_gitignore(self):
        folder = self.validate_project_folder()
        if not folder:
            return

        gitignore_path = Path(folder) / ".gitignore"

        existing_lines = []
        if gitignore_path.exists():
            existing_lines = gitignore_path.read_text(
                encoding="utf-8",
                errors="replace",
            ).splitlines()

        existing_clean = {line.strip() for line in existing_lines if line.strip()}

        new_lines = list(existing_lines)

        if new_lines and new_lines[-1].strip() != "":
            new_lines.append("")

        new_lines.append("# Safe ignore rules generated by PyQt6 GitHub Sync Manager")

        added = 0
        for item in SAFE_GITIGNORE_ITEMS:
            if item not in existing_clean:
                new_lines.append(item)
                added += 1

        gitignore_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

        self.log_title("Generate Safe .gitignore")
        self.log(f".gitignore path: {gitignore_path}")
        self.log(f"Added {added} missing ignore rules.")

        QMessageBox.information(
            self,
            ".gitignore Updated",
            f".gitignore generated / updated.\nAdded {added} missing rules.",
        )

        self.scan_folder_files()

    def create_missing_standard_files(self):
        folder = self.validate_project_folder()
        if not folder:
            return

        root = Path(folder)
        created = []

        readme = root / "README.md"
        if not readme.exists():
            repo_name = self.repo_name_input.text().strip() or slugify_repo_name(root.name)
            readme.write_text(
                f"# {repo_name}\n\nProject description coming soon.\n",
                encoding="utf-8",
            )
            created.append("README.md")

        gitignore = root / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text("\n".join(SAFE_GITIGNORE_ITEMS) + "\n", encoding="utf-8")
            created.append(".gitignore")

        license_file = root / "LICENSE"
        if not license_file.exists():
            license_file.write_text(
                "MIT License\n\nCopyright (c) 2026\n\nPermission is hereby granted...\n",
                encoding="utf-8",
            )
            created.append("LICENSE")

        requirements = root / "requirements.txt"
        if not requirements.exists():
            requirements.write_text("# Add Python packages here\n", encoding="utf-8")
            created.append("requirements.txt")

        main_exists = any((root / x).exists() for x in MAIN_CODE_CANDIDATES)

        self.log_title("Create Missing Standard Files")

        if created:
            self.log("Created:")
            for f in created:
                self.log(f"- {f}")
        else:
            self.log("No missing standard files.")

        if not main_exists:
            self.log("Warning: No obvious main code file found.", error=True)
            QMessageBox.warning(
                self,
                "Main Code Not Found",
                "No obvious main code file found.\n\nExpected one of:\n"
                + "\n".join(MAIN_CODE_CANDIDATES)
                + "\n\nYou can still upload, but please confirm your main source code exists.",
            )

        self.scan_folder_files()

    # ============================================================
    # Upload File Explorer
    # ============================================================

    def scan_folder_files(self):
        folder = self.validate_project_folder()
        if not folder:
            return

        self._updating_tree_checks = True
        self.folder_tree.clear()

        root = Path(folder)
        self.gitignore_patterns = self.load_gitignore_patterns(root)

        self.log_title("Refresh Folder File Explorer")
        self.log(f"Root: {root}")

        count = {
            "files": 0,
            "folders": 0,
            "risky": 0,
            "ignored": 0,
        }

        try:
            entries = sorted(
                list(root.iterdir()),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )

            for path in entries:
                self.add_path_to_tree(self.folder_tree, root, path, count)

            self._updating_tree_checks = False

            for i in range(self.folder_tree.topLevelItemCount()):
                self.refresh_folder_item_check_state(self.folder_tree.topLevelItem(i))

            self.folder_tree.expandToDepth(1)

            self.log(f"Folders: {count['folders']}")
            self.log(f"Files: {count['files']}")
            self.log(f"Risky items: {count['risky']}")
            self.log(f"Ignored by .gitignore: {count['ignored']}")

            missing = []
            for f in IMPORTANT_UPLOAD_FILES:
                if not (root / f).exists():
                    missing.append(f)

            main_exists = any((root / x).exists() for x in MAIN_CODE_CANDIDATES)

            if missing:
                self.log("Missing standard files:", error=True)
                for f in missing:
                    self.log(f"- {f}", error=True)

            if not main_exists:
                self.log("No obvious main code file found.", error=True)

        except Exception as e:
            self._updating_tree_checks = False
            self.log(f"Scan folder failed: {e}", error=True)
            QMessageBox.warning(self, "Scan Failed", str(e))

    def load_gitignore_patterns(self, root: Path):
        patterns = []

        gitignore_path = root / ".gitignore"

        if not gitignore_path.exists():
            return patterns

        try:
            lines = gitignore_path.read_text(
                encoding="utf-8",
                errors="replace",
            ).splitlines()

            for line in lines:
                line = line.strip()

                if not line:
                    continue

                if line.startswith("#"):
                    continue

                patterns.append(line)

        except Exception as e:
            self.log(f"Read .gitignore failed: {e}", error=True)

        return patterns

    def is_gitignored_path(self, rel):
        rel = rel.replace("\\", "/")
        rel_lower = rel.lower()
        basename = os.path.basename(rel_lower)

        patterns = getattr(self, "gitignore_patterns", [])

        ignored = False

        for pattern in patterns:
            pattern = pattern.strip()

            if not pattern or pattern.startswith("#"):
                continue

            negated = pattern.startswith("!")
            if negated:
                pattern = pattern[1:].strip()

            pattern = pattern.replace("\\", "/").lower()

            matched = False

            if pattern.endswith("/"):
                folder_pattern = pattern.rstrip("/")
                parts = rel_lower.split("/")

                if folder_pattern in parts:
                    matched = True

                if rel_lower.startswith(folder_pattern + "/"):
                    matched = True

            elif "/" not in pattern and fnmatch.fnmatch(basename, pattern):
                matched = True

            elif fnmatch.fnmatch(rel_lower, pattern):
                matched = True

            if matched:
                ignored = not negated

        return ignored

    def add_path_to_tree(self, parent, root: Path, path: Path, count: dict):
        rel = path.relative_to(root).as_posix()

        if rel == ".git" or rel.startswith(".git/"):
            return

        ignored = self.is_gitignored_path(rel)
        risky = self.is_risky_path(rel) or ignored
        important = self.is_important_file(rel)

        item = QTreeWidgetItem(parent)

        item.setText(0, path.name)
        item.setText(4, rel)

        item.setData(0, ROLE_PATH, rel)
        item.setData(0, ROLE_RISKY, risky)
        item.setData(0, ROLE_IGNORED, ignored)

        try:
            item.setIcon(0, self.icon_provider.icon(QFileInfo(str(path))))
        except Exception:
            pass

        item.setFlags(
            item.flags()
            | Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
        )

        if path.is_dir():
            count["folders"] += 1
            item.setText(1, "Folder")
            item.setText(2, "")
            item.setData(0, ROLE_KIND, "folder")

            if risky:
                if ignored:
                    item.setText(3, "IGNORED by .gitignore")
                    count["ignored"] += 1
                else:
                    item.setText(3, "RISKY folder / not expanded")

                item.setCheckState(0, Qt.CheckState.Unchecked)
                count["risky"] += 1
                return

            item.setText(3, "folder")
            item.setCheckState(0, Qt.CheckState.Checked)

            try:
                children = sorted(
                    list(path.iterdir()),
                    key=lambda p: (not p.is_dir(), p.name.lower()),
                )

                for child in children:
                    self.add_path_to_tree(item, root, child, count)

            except PermissionError:
                item.setText(3, "Permission denied")
                item.setCheckState(0, Qt.CheckState.Unchecked)

        else:
            count["files"] += 1
            item.setText(1, path.suffix.lower() or "File")
            item.setData(0, ROLE_KIND, "file")

            try:
                item.setText(2, format_bytes(path.stat().st_size))
            except Exception:
                item.setText(2, "")

            if risky:
                if ignored:
                    item.setText(3, "IGNORED by .gitignore")
                    count["ignored"] += 1
                else:
                    item.setText(3, "RISKY / usually should not upload")

                item.setCheckState(0, Qt.CheckState.Unchecked)
                count["risky"] += 1
            elif important:
                item.setText(3, "IMPORTANT / recommended")
                item.setCheckState(0, Qt.CheckState.Checked)
            else:
                item.setText(3, "normal")
                item.setCheckState(0, Qt.CheckState.Checked)

    def refresh_folder_item_check_state(self, item):
        if item.childCount() == 0:
            return item.checkState(0)

        checked = 0
        unchecked = 0
        partial = 0

        for i in range(item.childCount()):
            child = item.child(i)
            state = self.refresh_folder_item_check_state(child)

            if state == Qt.CheckState.Checked:
                checked += 1
            elif state == Qt.CheckState.Unchecked:
                unchecked += 1
            else:
                partial += 1

        self._updating_tree_checks = True

        if partial > 0 or (checked > 0 and unchecked > 0):
            item.setCheckState(0, Qt.CheckState.PartiallyChecked)
        elif checked > 0 and unchecked == 0:
            item.setCheckState(0, Qt.CheckState.Checked)
        else:
            item.setCheckState(0, Qt.CheckState.Unchecked)

        self._updating_tree_checks = False
        return item.checkState(0)

    def on_folder_tree_item_changed(self, item, column):
        if self._updating_tree_checks:
            return

        if column != 0:
            return

        self._updating_tree_checks = True

        state = item.checkState(0)
        kind = item.data(0, ROLE_KIND)

        if kind == "folder":
            self.apply_check_state_to_children(item, state)

        self.update_parent_check_states(item)

        self._updating_tree_checks = False

    def apply_check_state_to_children(self, item, state):
        for i in range(item.childCount()):
            child = item.child(i)
            risky = bool(child.data(0, ROLE_RISKY))

            if state == Qt.CheckState.Checked:
                if risky:
                    child.setCheckState(0, Qt.CheckState.Unchecked)
                else:
                    child.setCheckState(0, Qt.CheckState.Checked)
            elif state == Qt.CheckState.Unchecked:
                child.setCheckState(0, Qt.CheckState.Unchecked)

            if child.childCount() > 0:
                self.apply_check_state_to_children(child, child.checkState(0))

    def update_parent_check_states(self, item):
        parent = item.parent()

        while parent is not None:
            checked = 0
            unchecked = 0
            partial = 0

            for i in range(parent.childCount()):
                state = parent.child(i).checkState(0)

                if state == Qt.CheckState.Checked:
                    checked += 1
                elif state == Qt.CheckState.Unchecked:
                    unchecked += 1
                else:
                    partial += 1

            if partial > 0 or (checked > 0 and unchecked > 0):
                parent.setCheckState(0, Qt.CheckState.PartiallyChecked)
            elif checked > 0 and unchecked == 0:
                parent.setCheckState(0, Qt.CheckState.Checked)
            else:
                parent.setCheckState(0, Qt.CheckState.Unchecked)

            parent = parent.parent()

    def show_folder_tree_context_menu(self, position):
        item = self.folder_tree.itemAt(position)
        if item is None:
            return

        self.folder_tree.setCurrentItem(item)

        menu = QMenu(self)

        open_action = QAction("Open in File Explorer", self)
        check_action = QAction("Check This Item", self)
        uncheck_action = QAction("Uncheck This Item", self)
        expand_action = QAction("Expand", self)
        collapse_action = QAction("Collapse", self)

        open_action.triggered.connect(lambda: self.open_tree_item_in_explorer(item))
        check_action.triggered.connect(lambda: item.setCheckState(0, Qt.CheckState.Checked))
        uncheck_action.triggered.connect(lambda: item.setCheckState(0, Qt.CheckState.Unchecked))
        expand_action.triggered.connect(lambda: item.setExpanded(True))
        collapse_action.triggered.connect(lambda: item.setExpanded(False))

        menu.addAction(open_action)
        menu.addSeparator()
        menu.addAction(check_action)
        menu.addAction(uncheck_action)
        menu.addSeparator()
        menu.addAction(expand_action)
        menu.addAction(collapse_action)

        menu.exec(self.folder_tree.viewport().mapToGlobal(position))

    def open_tree_item_in_explorer(self, item):
        folder = self.validate_project_folder()
        if not folder:
            return

        rel = item.data(0, ROLE_PATH)
        if not rel:
            return

        full_path = Path(folder) / rel

        try:
            if full_path.is_dir():
                os.startfile(str(full_path))
            else:
                subprocess.run(["explorer", "/select,", str(full_path)], shell=False)
        except Exception as e:
            self.log(f"Open in explorer failed: {e}", error=True)

    def select_all_files(self):
        self._updating_tree_checks = True

        for i in range(self.folder_tree.topLevelItemCount()):
            item = self.folder_tree.topLevelItem(i)
            self.set_item_checked_safely(item, Qt.CheckState.Checked)

        self._updating_tree_checks = False

        for i in range(self.folder_tree.topLevelItemCount()):
            self.refresh_folder_item_check_state(self.folder_tree.topLevelItem(i))

    def unselect_risky_files(self):
        self._updating_tree_checks = True

        for i in range(self.folder_tree.topLevelItemCount()):
            self.uncheck_risky_recursive(self.folder_tree.topLevelItem(i))

        self._updating_tree_checks = False

        for i in range(self.folder_tree.topLevelItemCount()):
            self.refresh_folder_item_check_state(self.folder_tree.topLevelItem(i))

    def set_item_checked_safely(self, item, state):
        risky = bool(item.data(0, ROLE_RISKY))

        if state == Qt.CheckState.Checked and risky:
            item.setCheckState(0, Qt.CheckState.Unchecked)
        else:
            item.setCheckState(0, state)

        for i in range(item.childCount()):
            self.set_item_checked_safely(item.child(i), state)

    def uncheck_risky_recursive(self, item):
        risky = bool(item.data(0, ROLE_RISKY))

        if risky:
            item.setCheckState(0, Qt.CheckState.Unchecked)

        for i in range(item.childCount()):
            self.uncheck_risky_recursive(item.child(i))

    def get_selected_upload_paths(self):
        selected = []

        for i in range(self.folder_tree.topLevelItemCount()):
            self.collect_selected_paths(self.folder_tree.topLevelItem(i), selected)

        normalized = []
        seen = set()

        for path in selected:
            if path not in seen:
                normalized.append(path)
                seen.add(path)

        return normalized

    def collect_selected_paths(self, item, selected):
        rel = item.data(0, ROLE_PATH)
        kind = item.data(0, ROLE_KIND)
        state = item.checkState(0)

        if state == Qt.CheckState.Checked:
            if rel:
                selected.append(rel)
            return

        if state == Qt.CheckState.PartiallyChecked and kind == "folder":
            for i in range(item.childCount()):
                self.collect_selected_paths(item.child(i), selected)

    def get_selected_upload_files(self):
        return self.get_selected_upload_paths()

    def is_important_file(self, rel):
        rel_lower = rel.lower()

        if rel in IMPORTANT_UPLOAD_FILES:
            return True

        if rel_lower in [x.lower() for x in MAIN_CODE_CANDIDATES]:
            return True

        if rel_lower == "database/schema.sql":
            return True

        return False

    def is_risky_path(self, rel):
        rel_lower = rel.lower()
        parts = rel_lower.split("/")

        for part in parts:
            if part in SENSITIVE_DIR_NAMES:
                return True

        for pattern in SENSITIVE_FILE_PATTERNS:
            if fnmatch.fnmatch(os.path.basename(rel_lower), pattern.lower()):
                return True

        if any(keyword in os.path.basename(rel_lower) for keyword in SENSITIVE_NAME_KEYWORDS):
            return True

        return False

    def safety_scan_selected_files(self, selected_files):
        risky = [f for f in selected_files if self.is_risky_path(f)]

        if risky:
            self.log_title("Safety Scan Warning")
            self.log("You selected risky files/folders:", error=True)

            for f in risky[:100]:
                self.log(f, error=True)

            msg = (
                "You selected possible sensitive files or folders.\n\n"
                "The program will NOT delete anything.\n\n"
                "Please confirm these files are safe to upload.\n\n"
                "Continue?"
            )

            reply = QMessageBox.warning(
                self,
                "Safety Scan Warning",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            return reply == QMessageBox.StandardButton.Yes

        self.log("Selected file/folder safety scan OK.")
        return True

    def git_add_selected_files(self, folder, selected_files):
        if not selected_files:
            QMessageBox.warning(self, "No Files Selected", "Please tick at least one file or folder to upload.")
            return False

        self.log_title("git add selected files/folders")

        added_count = 0
        skipped_count = 0

        for rel in selected_files:
            ignored_result = self.run_command(
                ["git", "check-ignore", "-q", "--", rel],
                cwd=folder,
                quiet=True,
            )

            if ignored_result is not None and ignored_result.returncode == 0:
                self.log(f"Skipped ignored file/folder: {rel}", error=True)
                skipped_count += 1
                continue

            result = self.run_command(["git", "add", "--", rel], cwd=folder)

            if result is None:
                QMessageBox.warning(self, "Git Add Failed", f"git add failed:\n{rel}")
                return False

            if result.returncode != 0:
                self.log(f"git add failed, skipped: {rel}", error=True)
                skipped_count += 1
                continue

            added_count += 1

        self.log(f"git add completed. Added: {added_count}, Skipped: {skipped_count}")

        if added_count == 0:
            QMessageBox.warning(
                self,
                "Nothing Added",
                "No selected files were added.\n\nThey may all be ignored by .gitignore.",
            )
            return False

        return True

    def check_status(self):
        folder = self.validate_project_folder()
        if not folder:
            return

        self.log_title("Git Status")
        self.run_command(["git", "status", "--short"], cwd=folder)

    def is_git_repo(self, folder):
        result = self.run_command(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=folder,
            title="Check Git Repository",
        )

        return result is not None and result.returncode == 0 and "true" in result.stdout.lower()

    def one_click_first_upload(self):
        folder = self.validate_project_folder()
        if not folder:
            return

        owner, repo = self.validate_owner_repo()
        if not owner or not repo:
            return

        selected_files = self.get_selected_upload_files()

        if not selected_files:
            QMessageBox.warning(self, "No Files Selected", "Please tick files or folders you want to upload first.")
            return

        if not self.safety_scan_selected_files(selected_files):
            self.log("User cancelled after Safety Scan warning.", error=True)
            return

        commit_msg = self.commit_msg_input.text().strip() or "Initial commit"
        visibility = self.visibility_combo.currentText().lower()

        self.log_title("One Click First Upload")

        git_folder = Path(folder) / ".git"

        if not git_folder.exists():
            result = self.run_command(["git", "init"], cwd=folder, title="git init")
            if result is None or result.returncode != 0:
                QMessageBox.warning(self, "Git Init Failed", "git init failed.")
                return
        else:
            self.log("Git repository already exists. Skip git init.")

        if not self.git_add_selected_files(folder, selected_files):
            return

        diff_result = self.run_command(
            ["git", "diff", "--cached", "--quiet"],
            cwd=folder,
            title="Check Staged Changes",
        )

        if diff_result is None:
            return

        if diff_result.returncode == 1:
            commit_result = self.run_command(
                ["git", "commit", "-m", commit_msg],
                cwd=folder,
                title="git commit",
            )
            if commit_result is None or commit_result.returncode != 0:
                QMessageBox.warning(self, "Commit Failed", "git commit failed.")
                return
        elif diff_result.returncode == 0:
            self.log("No changes to commit.")
        else:
            self.log("git diff --cached --quiet returned unexpected error.", error=True)
            return

        branch_result = self.run_command(
            ["git", "branch", "-M", "main"],
            cwd=folder,
            title="Set branch to main",
        )

        if branch_result is None or branch_result.returncode != 0:
            QMessageBox.warning(self, "Branch Failed", "git branch -M main failed.")
            return

        view_result = self.run_command(
            ["gh", "repo", "view", f"{owner}/{repo}"],
            title="Check GitHub Repo Exists",
        )

        if view_result is None:
            return

        if view_result.returncode != 0:
            create_cmd = ["gh", "repo", "create", f"{owner}/{repo}"]

            if visibility == "public":
                create_cmd.append("--public")
            else:
                create_cmd.append("--private")

            create_result = self.run_command(
                create_cmd,
                title="Create GitHub Repository",
            )

            if create_result is None or create_result.returncode != 0:
                QMessageBox.warning(self, "Repo Create Failed", "GitHub repo create failed.")
                return
        else:
            self.log("GitHub repository already exists. Skip create.")

        if not self.ensure_remote_origin(folder, owner, repo):
            return

        push_result = self.run_command(
            ["git", "push", "-u", "origin", "main"],
            cwd=folder,
            title="git push -u origin main",
        )

        if push_result is None or push_result.returncode != 0:
            QMessageBox.warning(self, "Push Failed", "git push failed.")
            return

        QMessageBox.information(self, "Upload Complete", "First upload completed successfully.")

    def ensure_remote_origin(self, folder, owner, repo):
        target_url = f"https://github.com/{owner}/{repo}.git"

        self.log_title("Check Remote Origin")
        self.log(f"Target origin URL: {target_url}")

        result = self.run_command(
            ["git", "remote", "get-url", "origin"],
            cwd=folder,
        )

        if result is None:
            return False

        if result.returncode != 0:
            add_result = self.run_command(
                ["git", "remote", "add", "origin", target_url],
                cwd=folder,
                title="Add Remote Origin",
            )

            if add_result is None or add_result.returncode != 0:
                QMessageBox.warning(self, "Remote Failed", "git remote add origin failed.")
                return False

            return True

        current_url = result.stdout.strip()

        if current_url == target_url:
            self.log("origin already correct. No action needed.")
            return True

        self.log(f"origin exists but different: {current_url}")

        set_result = self.run_command(
            ["git", "remote", "set-url", "origin", target_url],
            cwd=folder,
            title="Set Remote Origin URL",
        )

        if set_result is None or set_result.returncode != 0:
            QMessageBox.warning(self, "Remote Failed", "git remote set-url origin failed.")
            return False

        return True

    def one_click_update_push(self):
        folder = self.validate_project_folder()
        if not folder:
            return

        selected_files = self.get_selected_upload_files()

        if not selected_files:
            QMessageBox.warning(self, "No Files Selected", "Please tick files or folders you want to upload first.")
            return

        if not self.safety_scan_selected_files(selected_files):
            self.log("User cancelled after Safety Scan warning.", error=True)
            return

        commit_msg = self.commit_msg_input.text().strip() or "Update"

        self.log_title("One Click Update Push")

        if not self.is_git_repo(folder):
            QMessageBox.warning(
                self,
                "Not Git Repository",
                "Selected folder is not a Git repository.\nPlease use One Click First Upload first.",
            )
            return

        status_result = self.run_command(
            ["git", "status", "--short"],
            cwd=folder,
            title="git status --short",
        )

        if status_result is None:
            return

        if not status_result.stdout.strip():
            self.log("No changes to push.")
            QMessageBox.information(self, "No Changes", "No changes to push.")
            return

        if not self.git_add_selected_files(folder, selected_files):
            return

        diff_result = self.run_command(
            ["git", "diff", "--cached", "--quiet"],
            cwd=folder,
            title="Check Staged Changes",
        )

        if diff_result is None:
            return

        if diff_result.returncode == 0:
            self.log("No selected staged changes to commit.")
            QMessageBox.information(self, "No Selected Changes", "Selected files/folders have no changes.")
            return

        commit_result = self.run_command(
            ["git", "commit", "-m", commit_msg],
            cwd=folder,
            title="git commit",
        )

        if commit_result is None or commit_result.returncode != 0:
            QMessageBox.warning(self, "Commit Failed", "git commit failed.")
            return

        push_result = self.run_command(
            ["git", "push"],
            cwd=folder,
            title="git push",
        )

        if push_result is None or push_result.returncode != 0:
            QMessageBox.warning(self, "Push Failed", "git push failed.")
            return

        QMessageBox.information(self, "Update Complete", "Update push completed successfully.")

    # ============================================================
    # Page 3: Setup Guide
    # ============================================================

    def build_setup_page(self):
        layout = QVBoxLayout(self.page_setup)

        btn_layout = QHBoxLayout()
        copy_btn = QPushButton("Copy Setup Guide")
        btn_layout.addWidget(copy_btn)
        btn_layout.addStretch()

        self.setup_text = QTextEdit()
        self.setup_text.setPlainText(SETUP_GUIDE)
        self.setup_text.setReadOnly(False)

        layout.addLayout(btn_layout)
        layout.addWidget(self.setup_text)

        copy_btn.clicked.connect(
            lambda: QApplication.clipboard().setText(self.setup_text.toPlainText())
        )

    # ============================================================
    # Page 4: Standard GitHub Prompt
    # ============================================================

    def build_prompt_page(self):
        layout = QVBoxLayout(self.page_prompt)

        btn_layout = QHBoxLayout()
        copy_btn = QPushButton("Copy Prompt")
        btn_layout.addWidget(copy_btn)
        btn_layout.addStretch()

        self.prompt_text = QTextEdit()
        self.prompt_text.setPlainText(STANDARD_CODEX_PROMPT)
        self.prompt_text.setReadOnly(False)

        layout.addLayout(btn_layout)
        layout.addWidget(self.prompt_text)

        copy_btn.clicked.connect(
            lambda: QApplication.clipboard().setText(self.prompt_text.toPlainText())
        )


def main():
    app = QApplication([])
    window = GitHubSyncManager()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
