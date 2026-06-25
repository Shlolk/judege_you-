import logging
import os
from pathlib import Path
from typing import Dict, Any
import re

logger = logging.getLogger(__name__)

LANGUAGE_MAP = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".jsx": "javascript", ".tsx": "typescript", ".java": "java",
    ".cpp": "cpp", ".cc": "cpp", ".c": "c", ".h": "c",
    ".go": "go", ".rs": "rust", ".rb": "ruby", ".php": "php",
}


class CodeParser:
    async def analyze_directory(self, directory_path: str) -> Dict[str, Any]:
        analysis = {"files": [], "metrics": {"total_files": 0, "languages": {}, "lines": 0},
                    "quality_score": 0.0}
        for root, dirs, files in os.walk(directory_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__', 'venv')]
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in LANGUAGE_MAP:
                    fp = os.path.join(root, file)
                    info = await self.analyze_file(fp)
                    analysis["files"].append(info)
                    analysis["metrics"]["total_files"] += 1
                    lang = LANGUAGE_MAP[ext]
                    analysis["metrics"]["languages"][lang] = analysis["metrics"]["languages"].get(lang, 0) + 1
                    analysis["metrics"]["lines"] += info.get("lines", 0)
        analysis["quality_score"] = min(100, analysis["metrics"]["total_files"] * 5 +
                                         (1 - analysis["metrics"].get("lines", 0) / max(1, analysis["metrics"]["total_files"]) * 0.01) * 50)
        return analysis

    async def analyze_file(self, file_path: str) -> Dict[str, Any]:
        ext = Path(file_path).suffix.lower()
        lang = LANGUAGE_MAP.get(ext, "unknown")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            lines = code.splitlines()
            deps = self._extract_deps(code, lang)
            return {"path": file_path, "language": lang, "extension": ext,
                    "lines": len(lines), "size_bytes": len(code.encode()),
                    "complexity": {"cyclomatic": self._cyclomatic(code, lang),
                                   "functions": code.count("def ") if lang == "python" else code.count("function "),
                                   "classes": code.count("class ")},
                    "dependencies": deps,
                    "quality_metrics": {"comment_ratio": sum(1 for l in lines if l.strip().startswith(("#", "//"))) / max(1, len(lines)),
                                        "code_structure_score": min(1.0, code.count("def ") / 10) if lang == "python" else 0.5}}
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return {"path": file_path, "language": lang, "error": str(e), "lines": 0, "size_bytes": 0,
                    "complexity": {}, "dependencies": {}, "quality_metrics": {}}

    def _cyclomatic(self, code: str, lang: str) -> int:
        count = 1
        for kw in ["if ", "elif ", "while ", "for ", "except", "case ", "&&", "||"]:
            count += code.count(kw)
        return count

    def _extract_deps(self, code: str, lang: str) -> Dict[str, list]:
        deps = {"imports": [], "external": []}
        if lang == "python":
            deps["imports"] = re.findall(r'^\s*import\s+(\w+)', code, re.MULTILINE)
            deps["external"] = re.findall(r'^\s*from\s+(\w+)', code, re.MULTILINE)
        elif lang in ("javascript", "typescript"):
            deps["imports"] = re.findall(r'require\([\'"]([^\'"]+)[\'"]\)', code)
            deps["external"] = re.findall(r'from\s+[\'"]([^\'"]+)[\'"]', code)
        return deps
