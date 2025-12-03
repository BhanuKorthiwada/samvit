"""Document loading and chunking utilities for RAG."""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """A chunk of a document with metadata."""

    content: str
    metadata: dict = field(default_factory=dict)
    chunk_index: int = 0
    source_file: str = ""

    @property
    def chunk_id(self) -> str:
        """Generate unique ID for this chunk."""
        return f"{self.source_file}::chunk_{self.chunk_index}"


@dataclass
class ChunkingConfig:
    """Configuration for document chunking."""

    chunk_size: int = 1000
    chunk_overlap: int = 200
    separators: list[str] = field(default_factory=lambda: ["\n\n", "\n", ". ", " ", ""])


class DocumentLoader:
    """Load and chunk documents from various file formats."""

    SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}

    def __init__(self, config: ChunkingConfig | None = None):
        self.config = config or ChunkingConfig()

    def load_file(self, file_path: Path) -> str:
        """Load content from a file."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()

        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {suffix}. "
                f"Supported: {self.SUPPORTED_EXTENSIONS}"
            )

        if suffix == ".pdf":
            return self._load_pdf(file_path)
        else:
            return self._load_text(file_path)

    def _load_text(self, file_path: Path) -> str:
        """Load plain text or markdown file."""
        with open(file_path, encoding="utf-8") as f:
            return f.read()

    def _load_pdf(self, file_path: Path) -> str:
        """Load PDF file and extract text."""
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(file_path)
            text_parts = []

            for page_num, page in enumerate(doc, 1):
                text = page.get_text()
                if text.strip():
                    text_parts.append(f"[Page {page_num}]\n{text}")

            doc.close()
            return "\n\n".join(text_parts)
        except ImportError:
            logger.warning(
                "PyMuPDF not installed. PDF support disabled. "
                "Install with: pip install pymupdf"
            )
            raise ValueError(
                "PDF support requires PyMuPDF. Install with: pip install pymupdf"
            )

    def chunk_text(
        self,
        text: str,
        source_file: str = "",
        base_metadata: dict | None = None,
    ) -> list[DocumentChunk]:
        """Split text into overlapping chunks."""
        if not text.strip():
            return []

        chunks = self._recursive_split(
            text,
            self.config.chunk_size,
            self.config.chunk_overlap,
            self.config.separators,
        )

        base_metadata = base_metadata or {}

        return [
            DocumentChunk(
                content=chunk,
                metadata={
                    **base_metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                },
                chunk_index=i,
                source_file=source_file,
            )
            for i, chunk in enumerate(chunks)
        ]

    def _recursive_split(
        self,
        text: str,
        chunk_size: int,
        overlap: int,
        separators: list[str],
    ) -> list[str]:
        """Recursively split text using separators."""
        if len(text) <= chunk_size:
            return [text] if text.strip() else []

        separator = separators[0] if separators else ""
        next_separators = separators[1:] if len(separators) > 1 else [""]

        if separator:
            splits = text.split(separator)
        else:
            splits = list(text)

        chunks = []
        current_chunk = ""

        for split in splits:
            piece = split + separator if separator else split

            if len(current_chunk) + len(piece) <= chunk_size:
                current_chunk += piece
            else:
                if current_chunk.strip():
                    if len(current_chunk) > chunk_size and next_separators:
                        chunks.extend(
                            self._recursive_split(
                                current_chunk, chunk_size, overlap, next_separators
                            )
                        )
                    else:
                        chunks.append(current_chunk.strip())

                if overlap > 0 and chunks:
                    overlap_text = (
                        chunks[-1][-overlap:]
                        if len(chunks[-1]) > overlap
                        else chunks[-1]
                    )
                    current_chunk = overlap_text + piece
                else:
                    current_chunk = piece

        if current_chunk.strip():
            if len(current_chunk) > chunk_size and next_separators:
                chunks.extend(
                    self._recursive_split(
                        current_chunk, chunk_size, overlap, next_separators
                    )
                )
            else:
                chunks.append(current_chunk.strip())

        return chunks

    def load_and_chunk(
        self,
        file_path: Path,
        metadata: dict | None = None,
    ) -> list[DocumentChunk]:
        """Load a file and chunk it."""
        content = self.load_file(file_path)

        base_metadata = metadata or {}
        base_metadata["source"] = str(file_path)
        base_metadata["filename"] = file_path.name

        return self.chunk_text(
            content,
            source_file=str(file_path),
            base_metadata=base_metadata,
        )


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
