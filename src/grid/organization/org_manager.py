"""Organization manager for multi-org/multi-user operations."""

from .discipline import DisciplineManager
from .models import Organization, OrganizationRole, User, UserRole, UserStatus


class OrganizationManager:
    """Manages organizations and users."""

    def __init__(self):
        """Initialize organization manager."""
        self.organizations: dict[str, Organization] = {}
        self.users: dict[str, User] = {}
        self.discipline_manager = DisciplineManager()

        # Initialize default organizations
        self._initialize_default_orgs()

    def _initialize_default_orgs(self) -> None:
        """Initialize default organizations (OpenAI, NVIDIA, Walt Disney Pictures)."""
        # OpenAI
        openai_org = Organization(
            org_id="openai",
            name="OpenAI",
            role=OrganizationRole.OPENAI,
            domain="openai.com",
            settings={
                "primary_focus": ["AI research", "LLM development", "GPT models"],
                "deep_focus": None,
                "strict_mode": True,
                "auto_penalty": True,
            },
        )
        self.organizations["openai"] = openai_org

        # NVIDIA
        nvidia_org = Organization(
            org_id="nvidia",
            name="NVIDIA",
            role=OrganizationRole.NVIDIA,
            domain="nvidia.com",
            settings={
                "primary_focus": ["GPU computing", "AI acceleration", "CUDA"],
                "deep_focus": None,
                "strict_mode": True,
                "auto_penalty": True,
            },
        )
        self.organizations["nvidia"] = nvidia_org

        # Walt Disney Pictures (deep focus)
        disney_org = Organization(
            org_id="walt_disney_pictures",
            name="Walt Disney Pictures",
            role=OrganizationRole.WALT_DISNEY_PICTURES,
            domain="disney.com",
            settings={
                "primary_focus": ["Entertainment", "Animation", "Storytelling"],
                "deep_focus": "Walt Disney Pictures",
                "strict_mode": True,
                "auto_penalty": True,
            },
        )
        self.organizations["walt_disney_pictures"] = disney_org

    def create_organization(
        self,
        name: str,
        role: OrganizationRole,
        domain: str | None = None,
    ) -> Organization:
        """Create a new organization."""
        org = Organization(
            org_id=f"org_{name.lower().replace(' ', '_')}",
            name=name,
            role=role,
            domain=domain,
        )
        self.organizations[org.org_id] = org
        return org

    def get_organization(self, org_id: str) -> Organization | None:
        """Get an organization by ID."""
        return self.organizations.get(org_id)

    def create_user(
        self,
        username: str,
        email: str | None = None,
        org_id: str | None = None,
        role: UserRole = UserRole.VIEWER,
    ) -> User:
        """Create a new user."""
        user = User(
            username=username,
            email=email,
            org_id=org_id,
            role=role,
        )
        if org_id:
            user.add_org(org_id)
            org = self.get_organization(org_id)
            if org:
                org.add_user(user.user_id, is_admin=(role == UserRole.ADMIN))

        self.users[user.user_id] = user
        return user

    def get_user(self, user_id: str) -> User | None:
        """Get a user by ID."""
        return self.users.get(user_id)

    def add_user_to_org(self, user_id: str, org_id: str, is_admin: bool = False) -> bool:
        """Add a user to an organization."""
        user = self.get_user(user_id)
        org = self.get_organization(org_id)
        if not user or not org:
            return False

        user.add_org(org_id)
        org.add_user(user_id, is_admin=is_admin)
        return True

    def remove_user_from_org(self, user_id: str, org_id: str) -> bool:
        """Remove a user from an organization."""
        user = self.get_user(user_id)
        org = self.get_organization(org_id)
        if not user or not org:
            return False

        user.remove_org(org_id)
        org.remove_user(user_id)
        return True

    def get_org_users(self, org_id: str) -> list[User]:
        """Get all users in an organization."""
        org = self.get_organization(org_id)
        if not org:
            return []

        return [self.users[uid] for uid in org.user_ids if uid in self.users]

    def get_user_orgs(self, user_id: str) -> list[Organization]:
        """Get all organizations a user belongs to."""
        user = self.get_user(user_id)
        if not user:
            return []

        return [self.organizations[oid] for oid in user.org_ids if oid in self.organizations]

    def check_user_permission(self, user_id: str, feature: str, org_id: str | None = None) -> bool:
        """Check if user has permission for a feature."""
        user = self.get_user(user_id)
        if not user:
            return False

        # Check user status
        if user.status != UserStatus.ACTIVE:
            return False

        # Check penalties
        penalty_points = self.discipline_manager.get_user_penalty_points(user_id)
        if penalty_points >= 50.0:  # Threshold for feature restriction
            return False

        # Check org permissions
        if org_id:
            org = self.get_organization(org_id)
            if org:
                if feature in org.settings.restricted_features:
                    return False
                if org.settings.allowed_features and feature not in org.settings.allowed_features:
                    return False

        return True

    def record_user_activity(self, user_id: str) -> None:
        """Record user activity."""
        user = self.get_user(user_id)
        if user:
            user.update_activity()
