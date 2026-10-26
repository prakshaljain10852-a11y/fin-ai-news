"""PDF text extraction using pdfplumber."""
import pdfplumber
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class ExtractedContent:
    """Extracted content from a PDF newsletter."""
    filename: str
    full_text: str
    page_count: int
    tables: List[List[List[str]]]  # List of tables, each table is list of rows


class PDFExtractor:
    """Extracts text and tables from PDF newsletters."""

    def __init__(self):
        pass

    def extract(self, pdf_path: str) -> Optional[ExtractedContent]:
        """Extract text and tables from PDF."""
        path = Path(pdf_path)
        if not path.exists():
            print(f"PDF not found: {pdf_path}")
            return None

        try:
            full_text_parts = []
            all_tables = []
            page_count = 0

            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)
                for i, page in enumerate(pdf.pages):
                    # Extract text
                    text = page.extract_text()
                    if text:
                        full_text_parts.append(f"--- Page {i+1} ---\n{text}")

                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            # Clean table cells
                            cleaned_table = []
                            for row in table:
                                cleaned_row = [cell.strip() if cell else "" for cell in row]
                                cleaned_table.append(cleaned_row)
                            all_tables.append(cleaned_table)

            full_text = "\n\n".join(full_text_parts)

            return ExtractedContent(
                filename=path.name,
                full_text=full_text,
                page_count=page_count,
                tables=all_tables
            )

        except Exception as e:
            print(f"Error extracting PDF {pdf_path}: {e}")
            return None

    def extract_multiple(self, pdf_paths: List[str]) -> List[ExtractedContent]:
        """Extract content from multiple PDFs."""
        results = []
        for path in pdf_paths:
            content = self.extract(path)
            if content:
                results.append(content)
        return results