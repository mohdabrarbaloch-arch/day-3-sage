"""Extract plain text from uploaded files.

Supported: .txt, .md (plain read), .pdf (PyPDF2). Everything else is rejected
upstream by the extension allow-list.
"""

import io

from PyPDF2 import PdfReader


class ExtractionError(ValueError):
    pass


def extract_text(filename: str, data: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith((".txt", ".md")):
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return data.decode("utf-8", errors="replace")
            except Exception as exc:
                raise ExtractionError("could not decode text file") from exc

    if name.endswith(".pdf"):
        try:
            reader = PdfReader(io.BytesIO(data))
            pages = [(page.extract_text() or "").strip() for page in reader.pages]
            text = "\n\n".join(p for p in pages if p)
            if not text:
                raise ExtractionError("PDF has no extractable text (it may be scanned)")
            return text
        except ExtractionError:
            raise
        except Exception as exc:
            raise ExtractionError(f"could not read PDF: {exc}") from exc

    raise ExtractionError(f"unsupported file type: {name}")
