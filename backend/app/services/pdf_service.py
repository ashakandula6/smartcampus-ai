import fitz  # PyMuPDF
import re
from typing import List, Dict
from app.core.config import get_settings

settings = get_settings()


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract all text from a PDF given its bytes."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        full_text += f"\n[Page {page_num + 1}]\n"
        full_text += page.get_text("text")
    doc.close()
    return full_text


def clean_text(text: str) -> str:
    """Remove excessive whitespace and fix common PDF extraction artifacts."""
    # Remove multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Fix hyphenated line breaks (common in PDFs)
    text = re.sub(r'-\n([a-z])', r'\1', text)
    # Remove lone single characters on a line (page numbers, etc.)
    text = re.sub(r'\n[^\w\s]\n', '\n', text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[Dict]:
    """
    Split text into overlapping chunks for embedding.
    Returns list of {text, chunk_index, start_char, end_char}
    """
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP

    # Split by sentences first (better than hard character split)
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_chunk = ""
    current_start = 0
    char_pos = 0

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += " " + sentence if current_chunk else sentence
        else:
            if current_chunk:
                chunks.append({
                    "text": current_chunk.strip(),
                    "chunk_index": len(chunks),
                })
                # Overlap: keep last `overlap` characters
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + " " + sentence
            else:
                # Single sentence longer than chunk_size — split by words
                words = sentence.split()
                half = len(words) // 2
                chunks.append({
                    "text": " ".join(words[:half]),
                    "chunk_index": len(chunks),
                })
                current_chunk = " ".join(words[half:])

    # Add remaining text
    if current_chunk.strip():
        chunks.append({
            "text": current_chunk.strip(),
            "chunk_index": len(chunks),
        })

    return chunks


def process_pdf_to_chunks(pdf_bytes: bytes) -> List[Dict]:
    """Full pipeline: PDF bytes → cleaned text → chunks."""
    raw_text = extract_text_from_pdf(pdf_bytes)
    clean = clean_text(raw_text)
    chunks = chunk_text(clean)
    return chunks
