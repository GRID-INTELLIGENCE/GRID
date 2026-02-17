import uuid
from typing import Any


class AIBrainSession:
    def __init__(self, session_id: str, user_context: dict[str, Any], capabilities: list[str]):
        self.session_id = session_id
        self.user_context = user_context
        self.capabilities = capabilities


class AIBrain:
    def __init__(self, auth_context: dict[str, Any] | None = None):
        self.auth_context = auth_context or {}
        self.sessions: dict[str, AIBrainSession] = {}

    def create_session(self, user_context: dict[str, Any], capabilities: list[str]) -> AIBrainSession:
        session_id = str(uuid.uuid4())
        session = AIBrainSession(session_id, user_context, capabilities)
        self.sessions[session_id] = session
        return session
