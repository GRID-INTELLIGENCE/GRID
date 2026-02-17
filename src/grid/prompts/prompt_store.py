"""Prompt store for persisting prompts."""

import json
from pathlib import Path

from .models import Prompt, PromptSource


class PromptStore:
    """Store for persisting and querying prompts."""

    def __init__(self, storage_path: Path | None = None):
        """Initialize prompt store.

        Args:
            storage_path: Path to store prompts (default: ./grid/data/prompts)
        """
        if storage_path is None:
            storage_path = Path("grid/data/prompts")
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # In-memory index
        self._prompt_index: dict[str, str] = {}  # prompt_id -> file_path
        self._load_index()

    def _load_index(self) -> None:
        """Load prompt index from disk."""
        index_file = self.storage_path / "index.json"
        if index_file.exists():
            try:
                with open(index_file) as f:
                    self._prompt_index = json.load(f)
            except Exception:
                self._prompt_index = {}

    def _save_index(self) -> None:
        """Save prompt index to disk."""
        index_file = self.storage_path / "index.json"
        try:
            with open(index_file, "w") as f:
                json.dump(self._prompt_index, f, indent=2)
        except Exception:  # noqa: S110 intentional silent handling
            pass  # Best effort

    def _get_prompt_file(self, prompt_id: str) -> Path:
        """Get file path for a prompt ID."""
        return self.storage_path / f"{prompt_id}.json"

    def save_prompt(self, prompt: Prompt) -> None:
        """Save a prompt to storage.

        Args:
            prompt: Prompt to save
        """
        prompt_file = self._get_prompt_file(prompt.prompt_id)
        try:
            with open(prompt_file, "w") as f:
                json.dump(prompt.model_dump(mode="json"), f, indent=2, default=str)

            # Update index
            self._prompt_index[prompt.prompt_id] = str(prompt_file)
            self._save_index()
        except Exception as e:
            print(f"Failed to save prompt {prompt.prompt_id}: {e}")

    def get_prompt(self, prompt_id: str) -> Prompt | None:
        """Get a prompt by ID.

        Args:
            prompt_id: Prompt identifier

        Returns:
            Prompt or None if not found
        """
        prompt_file = self._prompt_index.get(prompt_id)
        if not prompt_file:
            return None

        try:
            with open(prompt_file) as f:
                data = json.load(f)
                return Prompt(**data)
        except Exception:
            return None

    def get_prompt_by_name(
        self,
        name: str,
        user_id: str | None = None,
        org_id: str | None = None,
        source: PromptSource | None = None,
    ) -> Prompt | None:
        """Get a prompt by name with optional filters.

        Args:
            name: Prompt name
            user_id: Optional user ID filter
            org_id: Optional org ID filter
            source: Optional source filter

        Returns:
            Matching prompt or None
        """
        # Search through index
        for prompt_id in self._prompt_index:
            prompt = self.get_prompt(prompt_id)
            if not prompt:
                continue

            if prompt.name != name:
                continue

            if user_id and prompt.user_id != user_id:
                continue
            if org_id and prompt.org_id != org_id:
                continue
            if source and prompt.source != source:
                continue

            return prompt

        return None

    def query_prompts(
        self,
        user_id: str | None = None,
        org_id: str | None = None,
        source: PromptSource | None = None,
        operation_type: str | None = None,
        domain: str | None = None,
        limit: int = 100,
    ) -> list[Prompt]:
        """Query prompts by various criteria.

        Args:
            user_id: Filter by user ID
            org_id: Filter by organization ID
            source: Filter by source
            operation_type: Filter by operation type
            domain: Filter by domain
            limit: Maximum number of results

        Returns:
            List of matching prompts
        """
        results = []
        count = 0

        for prompt_id in self._prompt_index:
            if count >= limit:
                break

            prompt = self.get_prompt(prompt_id)
            if not prompt:
                continue

            # Apply filters
            if user_id and prompt.user_id != user_id:
                continue
            if org_id and prompt.org_id != org_id:
                continue
            if source and prompt.source != source:
                continue
            if operation_type and prompt.context.operation_type != operation_type:
                continue
            if domain and prompt.context.domain != domain:
                continue

            results.append(prompt)
            count += 1

        return results

    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt.

        Args:
            prompt_id: Prompt identifier

        Returns:
            True if deleted, False if not found
        """
        prompt_file = self._prompt_index.get(prompt_id)
        if not prompt_file:
            return False

        try:
            Path(prompt_file).unlink(missing_ok=True)
            del self._prompt_index[prompt_id]
            self._save_index()
            return True
        except Exception:
            return False
