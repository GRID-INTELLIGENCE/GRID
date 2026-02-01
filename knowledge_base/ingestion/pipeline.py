"""
Data Ingestion Pipeline
=======================

Handles ingestion of data from various sources into the knowledge base.
Supports files, URLs, APIs, and streaming data.
"""

import hashlib
import json
import logging
import subprocess
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import docx
import nbformat
import PyPDF2
import requests
import yaml
from bs4 import BeautifulSoup

from ..core.config import KnowledgeBaseConfig
from ..core.database import KnowledgeBaseDB

logger = logging.getLogger(__name__)


@dataclass
class ChunkingProfile:
    """Chunking profile configuration."""

    chunk_size: int
    overlap: int
    description: str = ""


@dataclass
class SourceConfig:
    """Source configuration from manifest."""

    path: str
    profile: str
    metadata: dict[str, Any]


@dataclass
class IngestionManifest:
    """Ingestion manifest configuration."""

    profiles: dict[str, ChunkingProfile] = field(default_factory=dict)
    sources: list[SourceConfig] = field(default_factory=list)
    security: dict[str, Any] = field(default_factory=dict)
    sync: dict[str, Any] = field(default_factory=dict)
    feedback: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentData:
    """Document data structure."""

    id: str
    title: str
    content: str
    source_type: str
    source_path: str
    file_type: str
    metadata: dict[str, Any]


@dataclass
class IngestionResult:
    """Result of ingestion operation."""

    document_id: str
    chunks_created: int
    success: bool
    error_message: str | None = None


class DataConnector(ABC):
    """Abstract base class for data connectors."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to data source."""
        pass

    @abstractmethod
    def fetch_data(self) -> Iterator[DocumentData]:
        """Fetch data from source."""
        pass

    @abstractmethod
    def get_metadata(self) -> dict[str, Any]:
        """Get connector metadata."""
        pass


class FileConnector(DataConnector):
    """Connector for local file system."""

    def __init__(self, directory: str, file_patterns: list[str] = None, manifest_path: str | None = None):
        self.directory = Path(directory)
        self.file_patterns = file_patterns or ["*.txt", "*.md", "*.pdf", "*.docx"]
        self.supported_extensions = {
            ".txt",
            ".md",
            ".pdf",
            ".docx",  # existing
            ".py",
            ".rst",
            ".json",
            ".yaml",
            ".yml",
            ".ipynb",  # new
        }
        self.manifest_path = manifest_path
        self.manifest = self._load_manifest() if manifest_path else None

    def _load_manifest(self) -> IngestionManifest | None:
        """Load ingestion manifest from YAML file."""
        try:
            manifest_path = Path(self.manifest_path)
            if not manifest_path.exists():
                return None

            with open(manifest_path) as f:
                data = yaml.safe_load(f)

            # Parse profiles
            profiles = {}
            if "profiles" in data:
                for name, profile_data in data["profiles"].items():
                    profiles[name] = ChunkingProfile(
                        chunk_size=profile_data.get("chunk_size", 800),
                        overlap=profile_data.get("overlap", 120),
                        description=profile_data.get("description", ""),
                    )

            # Parse sources
            sources = []
            if "sources" in data:
                for source_data in data["sources"]:
                    sources.append(
                        SourceConfig(
                            path=source_data["path"],
                            profile=source_data["profile"],
                            metadata=source_data.get("metadata", {}),
                        )
                    )

            return IngestionManifest(
                profiles=profiles,
                sources=sources,
                security=data.get("security", {}),
                sync=data.get("sync", {}),
                feedback=data.get("feedback", {}),
            )
        except Exception as e:
            logger.error(f"Error loading manifest: {e}")
            return None

    def connect(self) -> bool:
        """Check if directory exists."""
        return self.directory.exists() and self.directory.is_dir()

    def fetch_data(self) -> Iterator[DocumentData]:
        """Fetch documents from directory."""
        for pattern in self.file_patterns:
            for file_path in self.directory.glob(pattern):
                if file_path.is_file():
                    try:
                        doc_data = self._process_file(file_path)
                        if doc_data:
                            yield doc_data
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")

    def _process_file(self, file_path: Path) -> DocumentData | None:
        """Process a single file."""
        content = ""
        file_type = file_path.suffix.lower()

        if file_type == ".txt" or file_type == ".md":
            content = file_path.read_text(encoding="utf-8")
        elif file_type == ".pdf":
            content = self._extract_pdf_text(file_path)
        elif file_type == ".docx":
            content = self._extract_docx_text(file_path)
        elif file_type == ".py":
            content = self._extract_code_text(file_path)
        elif file_type == ".rst":
            content = file_path.read_text(encoding="utf-8")
        elif file_type == ".json":
            content = self._extract_json_text(file_path)
        elif file_type == ".yaml" or file_type == ".yml":
            content = self._extract_yaml_text(file_path)
        elif file_type == ".ipynb":
            content = self._extract_notebook_text(file_path)
        else:
            return None

        # Generate document ID from file hash
        file_hash = hashlib.md5(file_path.read_bytes()).hexdigest()
        doc_id = f"file_{file_hash}"

        # Get git metadata
        git_metadata = self._get_git_metadata(file_path)

        # Get chunking profile from manifest
        chunking_profile = None
        if self.manifest:
            for source in self.manifest.sources:
                if file_path.match(source.path):
                    profile_name = source.profile
                    chunking_profile = self.manifest.profiles.get(profile_name)
                    break

        metadata = {
            "file_size": file_path.stat().st_size,
            "modified_time": file_path.stat().st_mtime,
            "file_hash": file_hash,
            "chunking_profile": chunking_profile.description if chunking_profile else "",
        }

        # Add git metadata if available
        if git_metadata:
            metadata.update(git_metadata)

        return DocumentData(
            id=doc_id,
            title=file_path.stem,
            content=content,
            source_type="file",
            source_path=str(file_path),
            file_type=file_type[1:],  # Remove the dot
            metadata=metadata,
        )

    def _get_git_metadata(self, file_path: Path) -> dict[str, Any] | None:
        """Get git metadata for a file."""
        try:
            # Get git commit SHA
            result = subprocess.run(
                ["git", "log", "-n", "1", "--pretty=format:%H", "--", str(file_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                commit_sha = result.stdout.strip()
                return {"git_commit": commit_sha, "doc_version": f"main@{commit_sha}"}
        except Exception as e:
            logger.debug(f"Could not get git metadata for {file_path}: {e}")
        return None

    def _extract_code_text(self, file_path: Path) -> str:
        """Extract text from code files."""
        return file_path.read_text(encoding="utf-8")

    def _extract_json_text(self, file_path: Path) -> str:
        """Extract text from JSON files."""
        data = json.loads(file_path.read_text(encoding="utf-8"))
        return json.dumps(data, indent=2)

    def _extract_yaml_text(self, file_path: Path) -> str:
        """Extract text from YAML files."""
        data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
        return yaml.dump(data, default_flow_style=False)

    def _extract_notebook_text(self, file_path: Path) -> str:
        """Extract text from Jupyter notebooks."""
        nb = nbformat.read(str(file_path), as_version=4)
        content_parts = []
        for cell in nb.cells:
            if cell.cell_type == "markdown":
                content_parts.append(cell.source)
            elif cell.cell_type == "code":
                content_parts.append(f"```python\n{cell.source}\n```")
        return "\n\n".join(content_parts)

    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF file."""
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text

    def _extract_docx_text(self, file_path: Path) -> str:
        """Extract text from DOCX file."""
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text

    def get_metadata(self) -> dict[str, Any]:
        return {"type": "file", "directory": str(self.directory), "patterns": self.file_patterns}


class WebConnector(DataConnector):
    """Connector for web URLs."""

    def __init__(self, urls: list[str], headers: dict[str, str] = None):
        self.urls = urls
        self.headers = headers or {"User-Agent": "KnowledgeBase/1.0"}

    def connect(self) -> bool:
        """Test connection to URLs."""
        try:
            # Test first URL
            if self.urls:
                response = requests.head(self.urls[0], headers=self.headers, timeout=10)
                return response.status_code < 400
            return True
        except Exception:
            return False

    def fetch_data(self) -> Iterator[DocumentData]:
        """Fetch content from URLs."""
        for url in self.urls:
            try:
                doc_data = self._fetch_url(url)
                if doc_data:
                    yield doc_data
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")

    def _fetch_url(self, url: str) -> DocumentData | None:
        """Fetch content from a single URL."""
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()

        # Parse HTML content
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract title
        title = soup.title.string if soup.title else urlparse(url).path

        # Extract text content
        for script in soup(["script", "style"]):
            script.extract()
        content = soup.get_text(separator="\n", strip=True)

        # Generate document ID from URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()
        doc_id = f"url_{url_hash}"

        return DocumentData(
            id=doc_id,
            title=title,
            content=content,
            source_type="url",
            source_path=url,
            file_type="html",
            metadata={
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type"),
                "url_hash": url_hash,
            },
        )

    def get_metadata(self) -> dict[str, Any]:
        return {"type": "web", "urls": self.urls, "headers": self.headers}


class APIConnector(DataConnector):
    """Connector for REST APIs."""

    def __init__(self, base_url: str, endpoints: list[str], headers: dict[str, str] = None, auth_token: str = None):
        self.base_url = base_url.rstrip("/")
        self.endpoints = endpoints
        self.headers = headers or {"Content-Type": "application/json"}
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"

    def connect(self) -> bool:
        """Test API connection."""
        try:
            response = requests.get(f"{self.base_url}/health", headers=self.headers, timeout=10)
            return response.status_code < 400
        except Exception:
            return False

    def fetch_data(self) -> Iterator[DocumentData]:
        """Fetch data from API endpoints."""
        for endpoint in self.endpoints:
            try:
                doc_data = self._fetch_endpoint(endpoint)
                if doc_data:
                    yield doc_data
            except Exception as e:
                logger.error(f"Error fetching {endpoint}: {e}")

    def _fetch_endpoint(self, endpoint: str) -> DocumentData | None:
        """Fetch data from a single endpoint."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Convert API response to text content
        if isinstance(data, dict):
            content = "\n".join([f"{k}: {v}" for k, v in data.items()])
        elif isinstance(data, list):
            content = "\n".join([str(item) for item in data])
        else:
            content = str(data)

        # Generate document ID
        endpoint_hash = hashlib.md5(endpoint.encode()).hexdigest()
        doc_id = f"api_{endpoint_hash}"

        return DocumentData(
            id=doc_id,
            title=f"API: {endpoint}",
            content=content,
            source_type="api",
            source_path=url,
            file_type="json",
            metadata={
                "endpoint": endpoint,
                "status_code": response.status_code,
                "response_size": len(response.content),
            },
        )

    def get_metadata(self) -> dict[str, Any]:
        return {"type": "api", "base_url": self.base_url, "endpoints": self.endpoints}


class TextProcessor:
    """Process and chunk text content."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 150):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str) -> list[str]:
        """Split text into overlapping chunks."""
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Find a good break point (sentence end)
            if end < len(text):
                # Look for sentence endings within the last 200 chars
                search_end = min(end + 200, len(text))
                break_chars = [". ", "! ", "? ", "\n\n"]

                best_break = end
                for break_char in break_chars:
                    pos = text.rfind(break_char, end, search_end)
                    if pos != -1 and pos > best_break:
                        best_break = pos + len(break_char)

                end = best_break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - self.overlap

            # Ensure we don't get stuck
            if start >= end:
                start = end

        return chunks

    def get_chunking_profile(self, profile_name: str, manifest: IngestionManifest | None = None) -> "ChunkingProfile":
        """Get chunking profile by name."""
        if manifest and profile_name in manifest.profiles:
            return manifest.profiles[profile_name]
        # Return default profile
        return ChunkingProfile(chunk_size=1000, overlap=150)


class DataIngestionPipeline:
    """Main data ingestion pipeline."""

    def __init__(self, config: KnowledgeBaseConfig, db: KnowledgeBaseDB, manifest_path: str | None = None):
        self.config = config
        self.db = db
        self.connectors: list[DataConnector] = []
        self.manifest_path = manifest_path
        self.manifest = self._load_manifest() if manifest_path else None
        self.processor = TextProcessor()
        self.ingestion_stats = {"documents_processed": 0, "chunks_created": 0, "errors": 0}
        self.last_ingested_sha = self._load_last_ingested_sha()

    def _load_manifest(self) -> IngestionManifest | None:
        """Load ingestion manifest from YAML file."""
        try:
            manifest_path = Path(self.manifest_path)
            if not manifest_path.exists():
                return None

            with open(manifest_path) as f:
                data = yaml.safe_load(f)

            # Parse profiles
            profiles = {}
            if "profiles" in data:
                for name, profile_data in data["profiles"].items():
                    profiles[name] = ChunkingProfile(
                        chunk_size=profile_data.get("chunk_size", 800),
                        overlap=profile_data.get("overlap", 120),
                        description=profile_data.get("description", ""),
                    )

            # Parse sources
            sources = []
            if "sources" in data:
                for source_data in data["sources"]:
                    sources.append(
                        SourceConfig(
                            path=source_data["path"],
                            profile=source_data["profile"],
                            metadata=source_data.get("metadata", {}),
                        )
                    )

            return IngestionManifest(
                profiles=profiles,
                sources=sources,
                security=data.get("security", {}),
                sync=data.get("sync", {}),
                feedback=data.get("feedback", {}),
            )
        except Exception as e:
            logger.error(f"Error loading manifest: {e}")
            return None

    def _load_last_ingested_sha(self) -> str | None:
        """Load last ingested commit SHA from database."""
        try:
            with self.db.session() as cursor:
                cursor.execute("SELECT extra_metadata FROM kb_documents WHERE id = 'last_ingested_sha'")
                row = cursor.fetchone()
                if row:
                    metadata = json.loads(row[0])
                    return metadata.get("sha")
        except Exception as e:
            logger.debug(f"Could not load last ingested SHA: {e}")
        return None

    def _save_last_ingested_sha(self, sha: str) -> None:
        """Save last ingested commit SHA to database."""
        try:
            with self.db.session() as cursor:
                cursor.execute(
                    """
                    MERGE INTO kb_documents t
                    USING (SELECT 'last_ingested_sha' AS id) s
                    ON t.id = s.id
                    WHEN MATCHED THEN UPDATE SET
                        title = 'Last Ingested SHA',
                        extra_metadata = ?,
                        updated_at = current_timestamp()
                    WHEN NOT MATCHED THEN INSERT
                        (id, title, content, source_type, source_path, file_type, extra_metadata, created_at, updated_at)
                    VALUES ('last_ingested_sha', 'Last Ingested SHA', '', 'system', '', '', ?, current_timestamp(), current_timestamp())
                    """,
                    (json.dumps({"sha": sha}), json.dumps({"sha": sha})),
                )
        except Exception as e:
            logger.error(f"Could not save last ingested SHA: {e}")

    def get_changed_files(self, since_sha: str | None = None) -> list[Path]:
        """Get list of files changed since last ingestion."""
        try:
            if not since_sha:
                # Get all files from manifest sources
                changed_files = []
                if self.manifest:
                    for source in self.manifest.sources:
                        pattern = source.path
                        # Convert glob pattern to files
                        base_dir = Path.cwd()
                        for file_path in base_dir.glob(pattern):
                            if file_path.is_file():
                                changed_files.append(file_path)
                return changed_files

            # Use git diff to get changed files
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{since_sha}..HEAD"], capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                changed_files = [Path(f.strip()) for f in result.stdout.split("\n") if f.strip()]
                return changed_files
        except Exception as e:
            logger.error(f"Error getting changed files: {e}")
        return []

    def check_for_secrets(self, file_path: Path) -> bool:
        """Check if file contains secrets using detect-secrets."""
        try:
            result = subprocess.run(
                ["detect-secrets", "scan", str(file_path)], capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                output = result.stdout
                # Check if any secrets were found
                return "No secrets detected" not in output
        except FileNotFoundError:
            logger.warning("detect-secrets not installed, skipping secret scan")
        except Exception as e:
            logger.error(f"Error checking for secrets: {e}")
        return False

    def should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped based on security rules."""
        if not self.manifest:
            return False

        skip_patterns = self.manifest.security.get("skip_patterns", [])

        for pattern in skip_patterns:
            if file_path.match(pattern):
                return True

        return False

    def add_connector(self, connector: DataConnector) -> None:
        """Add a data connector to the pipeline."""
        if connector.connect():
            self.connectors.append(connector)
            logger.info(f"Connector added: {connector.get_metadata()}")
        else:
            logger.error(f"Failed to connect: {connector.get_metadata()}")

    def run_ingestion(self) -> dict[str, Any]:
        """Run the complete ingestion pipeline."""
        logger.info("Starting data ingestion pipeline")

        for connector in self.connectors:
            logger.info(f"Processing connector: {connector.get_metadata()['type']}")

            for doc_data in connector.fetch_data():
                try:
                    result = self._process_document(doc_data)
                    if result.success:
                        self.ingestion_stats["documents_processed"] += 1
                        self.ingestion_stats["chunks_created"] += result.chunks_created
                        logger.info(f"Processed document: {doc_data.id}")
                    else:
                        self.ingestion_stats["errors"] += 1
                        logger.error(f"Failed to process {doc_data.id}: {result.error_message}")
                except Exception as e:
                    self.ingestion_stats["errors"] += 1
                    logger.error(f"Error processing {doc_data.id}: {e}")

        logger.info("Data ingestion pipeline completed")
        return self.ingestion_stats.copy()

    def _process_document(self, doc_data: DocumentData) -> IngestionResult:
        """Process a single document."""
        try:
            # Add document to database
            self.db.add_document(
                doc_id=doc_data.id,
                title=doc_data.title,
                content=doc_data.content,
                source_type=doc_data.source_type,
                source_path=doc_data.source_path,
                file_type=doc_data.file_type,
                metadata=doc_data.metadata,
            )

            # Chunk the content
            chunks = self.processor.chunk_text(doc_data.content)
            chunks_created = 0

            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_data.id}_chunk_{i}"

                # For now, use empty embedding (will be filled by embedding engine)
                embedding = []

                self.db.add_chunk(
                    chunk_id=chunk_id,
                    document_id=doc_data.id,
                    content=chunk,
                    chunk_index=i,
                    embedding=embedding,
                    token_count=len(chunk.split()),
                    metadata={"chunk_index": i},
                )

                chunks_created += 1

            return IngestionResult(document_id=doc_data.id, chunks_created=chunks_created, success=True)

        except Exception as e:
            return IngestionResult(document_id=doc_data.id, chunks_created=0, success=False, error_message=str(e))

    def get_stats(self) -> dict[str, Any]:
        """Get ingestion statistics."""
        return {
            **self.ingestion_stats,
            "connectors_count": len(self.connectors),
            "connectors_info": [c.get_metadata() for c in self.connectors],
        }
