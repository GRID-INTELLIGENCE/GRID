"""Prompt manager for custom user prompts."""


from .models import Prompt, PromptContext, PromptPriority, PromptSource
from .prompt_store import PromptStore


class PromptManager:
    """Manages custom user prompts with priority-based selection."""

    def __init__(self, store: PromptStore | None = None):
        """Initialize prompt manager.

        Args:
            store: Optional prompt store for persistence
        """
        self.store = store or PromptStore()
        self._prompt_cache: dict[str, list[Prompt]] = {}

    def add_prompt(
        self,
        name: str,
        content: str,
        user_id: str | None = None,
        org_id: str | None = None,
        source: PromptSource = PromptSource.USER_CUSTOM,
        priority: PromptPriority = PromptPriority.MEDIUM,
        context: PromptContext | None = None,
        tags: list[str] | None = None,
        description: str | None = None,
    ) -> Prompt:
        """Add a custom prompt.

        Args:
            name: Prompt name
            content: Prompt content
            user_id: User ID (for user custom prompts)
            org_id: Organization ID
            source: Prompt source
            priority: Prompt priority
            context: Prompt context
            tags: Tags for categorization
            description: Prompt description

        Returns:
            Created prompt
        """
        prompt = Prompt(
            name=name,
            content=content,
            user_id=user_id,
            org_id=org_id,
            source=source,
            priority=priority,
            context=context or PromptContext(user_id=user_id, org_id=org_id),
            tags=tags or [],
            description=description,
        )

        self.store.save_prompt(prompt)
        self._invalidate_cache(user_id, org_id)

        return prompt

    def get_prompt(
        self,
        name: str,
        user_id: str | None = None,
        org_id: str | None = None,
        context: PromptContext | None = None,
    ) -> Prompt | None:
        """Get a prompt by name with context matching.

        Priority order:
        1. User custom prompts (highest priority)
        2. Org default prompts
        3. System default prompts

        Args:
            name: Prompt name
            user_id: User ID
            org_id: Organization ID
            context: Optional context for matching

        Returns:
            Best matching prompt or None
        """
        # Try user custom first (highest priority)
        if user_id:
            prompt = self.store.get_prompt_by_name(name, user_id=user_id, source=PromptSource.USER_CUSTOM)
            if prompt:
                return prompt

        # Try org default
        if org_id:
            prompt = self.store.get_prompt_by_name(name, org_id=org_id, source=PromptSource.ORG_DEFAULT)
            if prompt:
                return prompt

        # Try system default
        prompt = self.store.get_prompt_by_name(name, source=PromptSource.SYSTEM_DEFAULT)
        return prompt

    def get_prompts_for_context(
        self,
        context: PromptContext,
        limit: int = 10,
    ) -> list[Prompt]:
        """Get prompts matching a context.

        Args:
            context: Context to match
            limit: Maximum number of prompts

        Returns:
            List of matching prompts, sorted by priority
        """
        prompts = self.store.query_prompts(
            user_id=context.user_id,
            org_id=context.org_id,
            operation_type=context.operation_type,
            domain=context.domain,
            limit=limit,
        )

        # Sort by priority (user custom > org default > system default)
        priority_order = {
            PromptSource.USER_CUSTOM: 3,
            PromptSource.ORG_DEFAULT: 2,
            PromptSource.SYSTEM_DEFAULT: 1,
        }

        prompts.sort(
            key=lambda p: (
                priority_order.get(p.source, 0),
                p.priority.value if p.priority else "medium",
            ),
            reverse=True,
        )

        return prompts[:limit]

    def get_user_custom_prompts(self, user_id: str) -> list[Prompt]:
        """Get all custom prompts for a user.

        Args:
            user_id: User identifier

        Returns:
            List of user's custom prompts
        """
        return self.store.query_prompts(user_id=user_id, source=PromptSource.USER_CUSTOM)

    def update_prompt(
        self,
        prompt_id: str,
        content: str | None = None,
        name: str | None = None,
        priority: PromptPriority | None = None,
        tags: list[str] | None = None,
    ) -> Prompt | None:
        """Update a prompt.

        Args:
            prompt_id: Prompt identifier
            content: New content
            name: New name
            priority: New priority
            tags: New tags

        Returns:
            Updated prompt or None if not found
        """
        prompt = self.store.get_prompt(prompt_id)
        if not prompt:
            return None

        if content is not None:
            prompt.content = content
        if name is not None:
            prompt.name = name
        if priority is not None:
            prompt.priority = priority
        if tags is not None:
            prompt.tags = tags

        prompt.update_timestamp()
        self.store.save_prompt(prompt)
        self._invalidate_cache(prompt.user_id, prompt.org_id)

        return prompt

    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt.

        Args:
            prompt_id: Prompt identifier

        Returns:
            True if deleted, False if not found
        """
        prompt = self.store.get_prompt(prompt_id)
        if prompt:
            self._invalidate_cache(prompt.user_id, prompt.org_id)
        return self.store.delete_prompt(prompt_id)

    def _invalidate_cache(self, user_id: str | None, org_id: str | None) -> None:
        """Invalidate prompt cache."""
        if user_id:
            self._prompt_cache.pop(user_id, None)
        if org_id:
            self._prompt_cache.pop(org_id, None)
