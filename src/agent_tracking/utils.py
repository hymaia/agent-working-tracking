"""Shared utilities for agent task retrieval across IDE environments."""

from __future__ import annotations
import os


def get_last_task(conversation_id: str | None = None):
    """
    Return the last AgentTask from the appropriate store based on ENV_IDE.

    - ENV_IDE=antigravity  → ChatStore (antigravity_interceptor)
    - ENV_IDE=claude       → ClaudeStore (claude_interceptor)
    - unset                → tries Claude first, falls back to Antigravity
    """
    env = os.getenv("ENV_IDE", "").lower()

    if env == "antigravity":
        return _last_from_antigravity(conversation_id)
    elif env == "claude":
        return _last_from_claude(conversation_id)
    else:
        task = _last_from_claude(conversation_id)
        if task is not None:
            return task
        return _last_from_antigravity(conversation_id)


def _last_from_antigravity(conversation_id: str | None):
    from .antigravity_interceptor import ChatStore, get_current_session_id
    cid = conversation_id or get_current_session_id()
    if not cid:
        return None
    return ChatStore().get_last_task(cid)


def _last_from_claude(conversation_id: str | None):
    from .claude_interceptor import ClaudeStore, get_current_session_id
    from .antigravity_interceptor import AgentTask

    store = ClaudeStore()

    if conversation_id:
        messages = store.get_messages(session_id=conversation_id)
    else:
        current = get_current_session_id()
        if not current:
            return None
        project, session_id = current
        messages = store.get_messages(project=project, session_id=session_id)

    if not messages:
        return None

    last = messages[-1]
    return AgentTask(
        id=len(messages) - 1,
        conversation_id=last["session_id"],
        asked=last["text"],
        effectuated=last["effectuated"],
        files_modified=[],
        created_at=last["timestamp"],
    )
