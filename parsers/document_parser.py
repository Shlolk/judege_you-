import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class DocumentParser:
    async def analyze_document(self, file_path: str) -> Dict[str, Any]:
        ext = Path(file_path).suffix.lower()
        if ext == ".md":
            return await self._analyze_markdown(file_path)
        elif ext == ".txt":
            return self._analyze_text(file_path)
        elif ext == ".pdf":
            return await self._analyze_pdf(file_path)
        return {"file_path": file_path, "type": "unknown", "content": "", "metadata": {}, "analysis": {}}

    async def _analyze_markdown(self, file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            lines = content.splitlines()
            return {"file_path": file_path, "type": "markdown", "content": content,
                    "metadata": {"word_count": len(content.split()), "line_count": len(lines),
                                 "heading_count": sum(1 for l in lines if l.strip().startswith("#")),
                                 "code_blocks": sum(1 for l in lines if l.strip().startswith("```"))},
                    "analysis": {"readability": min(100, len(content.split()) / 50 * 10),
                                 "has_toc": any("table of contents" in l.lower() for l in lines[:10])}}
        except Exception as e:
            return {"file_path": file_path, "type": "markdown", "error": str(e), "content": ""}

    def _analyze_text(self, file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"file_path": file_path, "type": "text", "content": content,
                    "metadata": {"word_count": len(content.split()), "line_count": len(content.splitlines())},
                    "analysis": {}}
        except Exception as e:
            return {"file_path": file_path, "type": "text", "error": str(e)}

    async def _analyze_pdf(self, file_path: str) -> Dict[str, Any]:
        try:
            from pypdf import PdfReader
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
            content = "\n".join(page.extract_text() or "" for page in reader.pages)
            return {"file_path": file_path, "type": "pdf", "content": content,
                    "metadata": {"page_count": len(reader.pages), "word_count": len(content.split())},
                    "analysis": {}}
        except Exception as e:
            return {"file_path": file_path, "type": "pdf", "error": str(e), "content": ""}
