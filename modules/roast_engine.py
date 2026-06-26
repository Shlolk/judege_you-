import logging
import os
from typing import List, Optional

logger = logging.getLogger(__name__)


class RoastResult:
    def __init__(self, project_name: str, total_files: int, languages: dict,
                 burn: str, score: int, shade: List[str]):
        self.project_name = project_name
        self.total_files = total_files
        self.languages = languages
        self.burn = burn
        self.score = score
        self.shade = shade


class RoastEngine:
    """Generates brutally honest project roasts using AI."""

    def __init__(self, ollama_client):
        self.ollama = ollama_client

    async def roast_project(self, path: str) -> RoastResult:
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            raise FileNotFoundError(f"Directory not found: {path}")

        files = []
        extensions = {}
        for root, dirs, fnames in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__" and d != "node_modules"]
            for f in fnames:
                ext = os.path.splitext(f)[1].lower()
                if ext:
                    extensions[ext] = extensions.get(ext, 0) + 1
                fpath = os.path.join(root, f)
                try:
                    files.append({"name": f, "path": fpath, "size": os.path.getsize(fpath)})
                except OSError:
                    pass

        files.sort(key=lambda x: -x["size"])
        big_files = [f for f in files[:5] if f["size"] > 0]
        total_files = len(files)
        total_size = sum(f["size"] for f in files)

        # Gather project info for the roast prompt
        dir_names = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d)) and not d.startswith(".")]
        lang_summary = ", ".join(f"{ext}: {cnt}" for ext, cnt in sorted(extensions.items(), key=lambda x: -x[1])[:8])
        big_file_names = "\n".join(f"  - {os.path.relpath(f['path'], path)} ({f['size'] / 1024:.1f} KB)" for f in big_files[:3])

        prompt = (
            f"You are an merciless roast master. Brutally roast this software project with savage humor. "
            f"Be mean, creative, and absolutely hilarious. No mercy. Tear it apart.\n\n"
            f"Project path: {path}\n"
            f"Total files: {total_files}\n"
            f"Total size: {total_size / 1024:.1f} KB\n"
            f"Languages/extensions: {lang_summary if lang_summary else 'none detected'}\n"
            f"Top-level directories: {', '.join(dir_names[:10]) if dir_names else 'none'}\n"
            f"Largest files:\n{big_file_names if big_file_names else '  (none)'}\n\n"
            f"Respond in this format:\n"
            f"ROAST: <a long, savage, hilarious burn paragraph roasting every aspect of this project>\n"
            f"SCORE: <0-100, how badly this project got roasted>\n"
            f"SHADE: <point 1>\n"
            f"SHADE: <point 2>\n"
            f"SHADE: <point 3>\n"
            f"SHADE: <point 4>\n"
            f"SHADE: <point 5>"
        )

        raw = await self.ollama.generate(prompt, temperature=0.95, max_tokens=1024)

        burn, score, shade = self._parse(raw, total_files, lang_summary)
        project_name = os.path.basename(path)
        return RoastResult(
            project_name=project_name,
            total_files=total_files,
            languages=extensions,
            burn=burn,
            score=score,
            shade=shade,
        )

    def _parse(self, raw: str, total_files: int, lang_summary: str) -> tuple:
        burn = "Your project is like a participation trophy — it shows up but doesn't actually achieve anything."
        score = 69
        shade = [
            "This codebase looks like it was written at 3 AM after three energy drinks.",
            "Your architecture is held together with duct tape and prayer.",
            "The only design pattern here is 'spaghetti à la chaos'.",
        ]

        for line in raw.splitlines():
            line = line.strip()
            if line.upper().startswith("ROAST:"):
                burn = line[6:].strip()
            elif line.upper().startswith("SCORE:"):
                try:
                    score = int("".join(c for c in line[6:].strip() if c.isdigit() or c == ".").split(".")[0])
                    score = max(0, min(100, score))
                except (ValueError, IndexError):
                    pass
            elif line.upper().startswith("SHADE:"):
                s = line[6:].strip()
                if s:
                    shade.append(s)

        if not shade:
            shade = ["No shade thrown — your project is that forgettable."]

        return burn, score, shade
