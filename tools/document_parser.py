import os
from pathlib import Path
try:
    import pdfplumber
except ImportError:
    pdfplumber = None
try:
    import docx
except ImportError:
    docx = None

class DocumentParser:
    """
    Parses PDF, DOCX, and Markdown files to extract raw text content.
    """

    @staticmethod
    def parse(file_path: str) -> str:
        """Parse document and return extracted text."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        ext = path.suffix.lower()
        if ext == ".pdf":
            return DocumentParser._parse_pdf(path)
        elif ext == ".docx":
            return DocumentParser._parse_docx(path)
        elif ext in [".md", ".txt"]:
            return DocumentParser._parse_text(path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}. Expected .pdf, .docx, .md, or .txt")

    @staticmethod
    def _parse_pdf(path: Path) -> str:
        if pdfplumber is None:
            raise ImportError("pdfplumber is required to parse PDFs. Run: pip install pdfplumber")
            
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        return text.strip()

    @staticmethod
    def _parse_docx(path: Path) -> str:
        if docx is None:
            raise ImportError("python-docx is required to parse DOCX files. Run: pip install python-docx")
            
        doc = docx.Document(path)
        return "\n".join([para.text for para in doc.paragraphs]).strip()

    @staticmethod
    def _parse_text(path: Path) -> str:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read().strip()
