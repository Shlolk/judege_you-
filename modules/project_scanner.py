import logging
logger = logging.getLogger(__name__)

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import os
import json
import hashlib
import subprocess

try:
    from git import Repo, InvalidGitRepositoryError
    HAS_GITPYTHON = True
except ImportError:
    HAS_GITPYTHON = False
    Repo = None
    InvalidGitRepositoryError = Exception

@dataclass
class FileInfo:
    path: str
    name: str
    extension: str
    size_bytes: int
    lines: int
    language: str
    last_modified: datetime
    permissions: str
    hash: str

@dataclass
class DirectoryInfo:
    path: str
    name: str
    file_count: int
    dir_count: int
    total_size_bytes: int
    depth: int

@dataclass
class GitInfo:
    has_git: bool
    branch: Optional[str] = None
    remote_url: Optional[str] = None
    last_commit_date: Optional[datetime] = None
    last_commit_message: Optional[str] = None
    commit_count: Optional[int] = None
    contributors: Optional[List[str]] = None

@dataclass
class ProjectScanResult:
    project_name: str
    project_path: str
    total_files: int
    total_dirs: int
    total_size_bytes: int
    languages: Dict[str, int]
    file_types: Dict[str, int]
    top_largest_files: List[FileInfo]
    git_info: GitInfo
    has_readme: bool
    has_tests: bool
    has_config: bool
    has_docker: bool
    has_ci: bool
    structure: List[DirectoryInfo]
    scan_metadata: Dict[str, Any]

class ProjectScanner:
    """Engine for scanning and analyzing project structure"""
    
    # Map extensions to languages
    LANGUAGE_MAP = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".jsx": "React JSX",
        ".tsx": "React TSX",
        ".java": "Java",
        ".cpp": "C++",
        ".cc": "C++",
        ".c": "C",
        ".h": "C/C++ Header",
        ".hpp": "C++ Header",
        ".go": "Go",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".php": "PHP",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
        ".cs": "C#",
        ".fs": "F#",
        ".r": "R",
        ".m": "Objective-C",
        ".mm": "Objective-C++",
        ".sh": "Shell",
        ".bash": "Bash",
        ".ps1": "PowerShell",
        ".sql": "SQL",
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".less": "Less",
        ".json": "JSON",
        ".xml": "XML",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".toml": "TOML",
        ".md": "Markdown",
        ".rst": "reStructuredText",
        ".txt": "Text",
        ".env": "Environment",
        ".dockerfile": "Dockerfile",
        ".gitignore": "GitIgnore",
    }
    
    # Config files to check
    CONFIG_FILES = [
        "package.json", "pyproject.toml", "Cargo.toml", "build.gradle",
        "pom.xml", "Gemfile", "requirements.txt", "Makefile", "CMakeLists.txt",
        "tsconfig.json", "webpack.config.js", "vite.config.ts", "next.config.js",
        ".env", ".env.example", "docker-compose.yml", "docker-compose.yaml",
    ]
    
    def __init__(self):
        self.ignored_dirs = {
            ".git", "__pycache__", "node_modules", "venv", ".venv",
            ".tox", "dist", "build", ".eggs", "*.egg-info",
            ".idea", ".vscode", ".DS_Store", "coverage", ".next",
            ".nuxt", "target", "bin", "obj", "vendor", ".bundle",
        }
        
        self.ignored_files = {
            ".DS_Store", "Thumbs.db", "*.pyc", "*.pyo", "*.so",
            "*.egg", "*.whl", "*.class", "*.o", "*.obj",
        }
    
    async def scan_project(self, path: str) -> ProjectScanResult:
        """Scan a project directory"""
        
        project_path = Path(path).resolve()
        
        if not project_path.exists():
            raise ValueError(f"Path does not exist: {path}")
        
        if not project_path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")
        
        # Collect all files and directories
        all_files = []
        all_dirs = []
        
        for root, dirs, files in os.walk(str(project_path)):
            # Filter ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
            
            rel_root = str(Path(root).relative_to(project_path))
            if rel_root == ".":
                rel_root = ""
            
            for file in files:
                file_path = Path(root) / file
                try:
                    file_info = self._get_file_info(file_path, project_path)
                    all_files.append(file_info)
                except:
                    continue
            
            if rel_root:  # Don't add root dir
                all_dirs.append(DirectoryInfo(
                    path=rel_root,
                    name=Path(rel_root).name,
                    file_count=len(files),
                    dir_count=len(dirs),
                    total_size_bytes=sum(
                        (Path(root) / f).stat().st_size
                        for f in files
                        if (Path(root) / f).exists()
                    ),
                    depth=len(rel_root.split(os.sep)),
                ))
        
        # Calculate statistics
        languages = {}
        file_types = {}
        total_size = 0
        
        for file in all_files:
            languages[file.language] = languages.get(file.language, 0) + 1
            file_types[file.extension] = file_types.get(file.extension, 0) + 1
            total_size += file.size_bytes
        
        # Sort files by size (largest first)
        sorted_files = sorted(all_files, key=lambda f: f.size_bytes, reverse=True)
        
        # Get git info
        git_info = self._get_git_info(project_path)
        
        # Check for important files
        files_set = {f.name for f in all_files}
        has_readme = any(
            f.lower() == "readme.md" or f.lower() == "readme.rst" or f.lower() == "readme.txt"
            for f in files_set
        )
        has_tests = any(
            "test" in f.name.lower() or "spec" in f.name.lower() or f.name.startswith("test_")
            for f in all_files
        )
        has_config = any(f in files_set for f in self.CONFIG_FILES)
        has_docker = any(
            f.lower() in ["dockerfile", "docker-compose.yml", "docker-compose.yaml"]
            for f in files_set
        )
        has_ci = any(
            ".github" in f.path or ".gitlab-ci.yml" in f.path or "Jenkinsfile" in f.name
            for f in all_files
        )
        
        return ProjectScanResult(
            project_name=project_path.name,
            project_path=str(project_path),
            total_files=len(all_files),
            total_dirs=len(all_dirs),
            total_size_bytes=total_size,
            languages=languages,
            file_types=file_types,
            top_largest_files=sorted_files[:10],
            git_info=git_info,
            has_readme=has_readme,
            has_tests=has_tests,
            has_config=has_config,
            has_docker=has_docker,
            has_ci=has_ci,
            structure=all_dirs,
            scan_metadata={
                "scan_time": datetime.now().isoformat(),
                "ignored_dirs_count": len(self.ignored_dirs),
                "file_count": len(all_files),
                "dir_count": len(all_dirs),
            }
        )
    
    def _get_file_info(
        self,
        file_path: Path,
        project_path: Path,
    ) -> FileInfo:
        """Get detailed information about a file"""
        
        stat = file_path.stat()
        extension = file_path.suffix.lower()
        
        # Get line count (for text files)
        lines = 0
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = sum(1 for _ in f)
        except:
            lines = 0
        
        # Calculate file hash
        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.md5(f.read(8192)).hexdigest()
        except:
            file_hash = "unknown"
        
        return FileInfo(
            path=str(file_path.relative_to(project_path)),
            name=file_path.name,
            extension=extension,
            size_bytes=stat.st_size,
            lines=lines,
            language=self.LANGUAGE_MAP.get(extension, "Unknown"),
            last_modified=datetime.fromtimestamp(stat.st_mtime),
            permissions=oct(stat.st_mode)[-3:],
            hash=file_hash,
        )
    
    def _get_git_info(self, project_path: Path) -> GitInfo:
        if not HAS_GITPYTHON:
            return GitInfo(has_git=False)
        try:
            repo = Repo(str(project_path))
            if repo.bare:
                return GitInfo(has_git=True)
            branch = None
            try:
                branch = repo.active_branch.name
            except:
                branch = "detached"
            remote_url = None
            try:
                if repo.remotes:
                    remote_url = repo.remotes[0].url
            except:
                pass
            last_commit_date = None
            last_commit_message = None
            commit_count = None
            contributors = None
            try:
                last_commit = repo.head.commit
                last_commit_date = datetime.fromtimestamp(last_commit.committed_date)
                last_commit_message = last_commit.message.strip()
                commit_count = sum(1 for _ in repo.iter_commits())
                contributors_set = set()
                for commit in repo.iter_commits(max_count=100):
                    if commit.author:
                        contributors_set.add(commit.author.name or str(commit.author))
                contributors = list(contributors_set)[:20]
            except:
                pass
            return GitInfo(has_git=True, branch=branch, remote_url=remote_url,
                           last_commit_date=last_commit_date, last_commit_message=last_commit_message,
                           commit_count=commit_count, contributors=contributors)
        except InvalidGitRepositoryError:
            return GitInfo(has_git=False)
        except Exception:
            return GitInfo(has_git=False)
    
    async def clone_repository(
        self,
        repo_url: str,
        target_dir: Optional[str] = None,
        branch: Optional[str] = None,
        depth: int = 1,
    ) -> str:
        """Clone a git repository for scanning"""
        
        if target_dir is None:
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            target_dir = f"./scanned_repos/{repo_name}"
        
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        
        clone_args = ["git", "clone"]
        
        if depth > 0:
            clone_args.extend(["--depth", str(depth)])
        
        if branch:
            clone_args.extend(["--branch", branch])
        
        clone_args.extend([repo_url, str(target_path)])
        
        try:
            result = subprocess.run(
                clone_args,
                capture_output=True,
                text=True,
                timeout=300,
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to clone: {result.stderr}")
            
            return str(target_path)
            
        except subprocess.TimeoutExpired:
            raise TimeoutError("Repository clone timed out")
    
    def generate_structure_tree(
        self,
        scan_result: ProjectScanResult,
        max_depth: int = 3,
    ) -> str:
        """Generate ASCII tree representation of project structure"""
        
        lines = [f"{scan_result.project_name}/"]
        
        # Build directory tree
        dir_tree = {}
        for dir_info in scan_result.structure:
            if dir_info.depth <= max_depth:
                parts = dir_info.path.split(os.sep)
                current = dir_tree
                for part in parts:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
        
        def _render_tree(tree: Dict, prefix: str = "", is_last: bool = True) -> List[str]:
            result = []
            items = list(tree.items())
            
            for i, (name, subtree) in enumerate(items):
                is_last_item = i == len(items) - 1
                connector = "└── " if is_last_item else "├── "
                result.append(f"{prefix}{connector}{name}/")
                
                extension = "    " if is_last_item else "│   "
                result.extend(_render_tree(subtree, prefix + extension, is_last_item))
            
            return result
        
        lines.extend(_render_tree(dir_tree))
        
        # Add file count and language info
        lines.append("")
        lines.append(f"Files: {scan_result.total_files}")
        lines.append(f"Directories: {scan_result.total_dirs}")
        lines.append(f"Total Size: {self._format_size(scan_result.total_size_bytes)}")
        lines.append(f"Languages: {', '.join(sorted(scan_result.languages.keys()))}")
        
        return "\n".join(lines)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

