#!/usr/bin/env python3
"""
RAG Chat HTTP Server - Simple web interface for GRID RAG chat.

Run: uv run python rag_chat_server.py
Open: http://localhost:8765
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.rag.chat import RAGChatSession

# Suppress noisy logging
os.environ["GRID_QUIET"] = "1"
os.environ["USE_DATABRICKS"] = "false"
os.environ["MOTHERSHIP_USE_DATABRICKS"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

logging.basicConfig(level=logging.WARNING)

from dataclasses import dataclass

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

app = FastAPI(title="GRID RAG Chat")

# Global session state
_session: RAGChatSession | None = None


@dataclass
class ChatConfig:
    model: str = "ministral-3:3b"
    ollama_base_url: str = "http://localhost:11434"
    top_k: int = 8
    temperature: float = 0.7
    collection_name: str = "grid_knowledge_base"
    vector_store_path: str = ""


async def get_session() -> RAGChatSession:
    global _session
    if _session is None:
        from tools.rag.chat import ChatConfig as SessionConfig
        from tools.rag.chat import RAGChatSession

        config = SessionConfig(
            model="ministral-3:3b",
            top_k=8,
            temperature=0.7,
            show_sources=True,
        )
        _session = RAGChatSession(config)
        await _session.initialize()
    return _session


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GRID RAG Chat</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: rgba(0, 255, 200, 0.1);
            border-bottom: 1px solid rgba(0, 255, 200, 0.3);
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        .header h1 {
            color: #00ffc8;
            font-size: 1.5rem;
            font-weight: 600;
        }
        .header .stats {
            margin-left: auto;
            font-size: 0.85rem;
            color: #888;
        }
        .chat-container {
            flex: 1;
            max-width: 1200px;
            width: 100%;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            padding: 1rem;
        }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        .message {
            padding: 1rem;
            border-radius: 12px;
            max-width: 85%;
            animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.user {
            background: linear-gradient(135deg, #0066cc 0%, #0044aa 100%);
            align-self: flex-end;
        }
        .message.assistant {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            align-self: flex-start;
        }
        .message .role {
            font-size: 0.75rem;
            color: rgba(255, 255, 255, 0.5);
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .message .content {
            line-height: 1.6;
            white-space: pre-wrap;
        }
        .message .sources {
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            font-size: 0.8rem;
            color: #888;
        }
        .sources-title {
            color: #00ffc8;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        .source-item {
            padding: 0.25rem 0;
            color: #aaa;
        }
        .input-area {
            padding: 1rem;
            background: rgba(0, 0, 0, 0.3);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        .input-form {
            display: flex;
            gap: 1rem;
            max-width: 1000px;
            margin: 0 auto;
        }
        .input-form input {
            flex: 1;
            padding: 1rem 1.5rem;
            border: 1px solid rgba(0, 255, 200, 0.3);
            border-radius: 25px;
            background: rgba(0, 0, 0, 0.5);
            color: #fff;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.3s;
        }
        .input-form input:focus {
            border-color: #00ffc8;
        }
        .input-form input::placeholder {
            color: #666;
        }
        .input-form button {
            padding: 1rem 2rem;
            background: linear-gradient(135deg, #00ffc8 0%, #00cc99 100%);
            border: none;
            border-radius: 25px;
            color: #000;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .input-form button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 20px rgba(0, 255, 200, 0.3);
        }
        .input-form button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        .typing {
            display: flex;
            gap: 4px;
            padding: 0.5rem;
        }
        .typing span {
            width: 8px;
            height: 8px;
            background: #00ffc8;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }
        .typing span:nth-child(2) { animation-delay: 0.2s; }
        .typing span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
            0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); }
            30% { opacity: 1; transform: scale(1); }
        }
        .error {
            background: rgba(255, 50, 50, 0.1);
            border: 1px solid rgba(255, 50, 50, 0.3);
            color: #ff6666;
        }
        code {
            background: rgba(0, 0, 0, 0.3);
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: 'Consolas', monospace;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>GRID RAG Chat</h1>
        <span class="stats" id="stats">Loading...</span>
    </div>

    <div class="chat-container">
        <div class="messages" id="messages">
            <div class="message assistant">
                <div class="role">System</div>
                <div class="content">Welcome to GRID RAG Chat! I have access to the GRID codebase. Ask me about architecture, patterns, safety systems, or any code-related questions.</div>
            </div>
        </div>

        <div class="input-area">
            <form class="input-form" id="chat-form">
                <input type="text" id="query" placeholder="Ask about GRID architecture, code, patterns..." autocomplete="off" />
                <button type="submit" id="send-btn">Send</button>
            </form>
        </div>
    </div>

    <script>
        const messagesDiv = document.getElementById('messages');
        const chatForm = document.getElementById('chat-form');
        const queryInput = document.getElementById('query');
        const sendBtn = document.getElementById('send-btn');
        const statsSpan = document.getElementById('stats');

        let isLoading = false;

        // Load stats
        fetch('/api/stats')
            .then(r => r.json())
            .then(data => {
                statsSpan.textContent = `${data.documents} chunks | ${data.model}`;
            })
            .catch(() => {
                statsSpan.textContent = 'RAG Ready';
            });

        function addMessage(role, content, sources = null) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${role}`;

            const roleDiv = document.createElement('div');
            roleDiv.className = 'role';
            roleDiv.textContent = role === 'user' ? 'You' : 'GRID';

            const contentDiv = document.createElement('div');
            contentDiv.className = 'content';
            contentDiv.textContent = content;

            msgDiv.appendChild(roleDiv);
            msgDiv.appendChild(contentDiv);

            if (sources && sources.length > 0) {
                const sourcesDiv = document.createElement('div');
                sourcesDiv.className = 'sources';
                sourcesDiv.innerHTML = `<div class="sources-title">Sources:</div>` +
                    sources.map(s => `<div class="source-item">${s}</div>`).join('');
                msgDiv.appendChild(sourcesDiv);
            }

            messagesDiv.appendChild(msgDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function addTyping() {
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message assistant typing-indicator';
            typingDiv.id = 'typing';
            typingDiv.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
            messagesDiv.appendChild(typingDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function removeTyping() {
            const typing = document.getElementById('typing');
            if (typing) typing.remove();
        }

        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const query = queryInput.value.trim();
            if (!query || isLoading) return;

            isLoading = true;
            sendBtn.disabled = true;
            queryInput.value = '';

            addMessage('user', query);
            addTyping();

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query })
                });

                const data = await response.json();
                removeTyping();

                if (data.error) {
                    addMessage('assistant error', `Error: ${data.error}`);
                } else {
                    addMessage('assistant', data.response, data.sources);
                }
            } catch (err) {
                removeTyping();
                addMessage('assistant error', `Connection error: ${err.message}`);
            }

            isLoading = false;
            sendBtn.disabled = false;
            queryInput.focus();
        });

        queryInput.focus();
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_TEMPLATE


@app.get("/api/stats")
async def stats():
    try:
        session = await get_session()
        if session._engine:
            s = session._engine.get_stats()
            return {
                "documents": s.get("document_count", 0),
                "model": session.config.model,
                "collection": session.config.collection_name,
            }
    except Exception as e:
        return {"error": str(e), "documents": 0, "model": "unknown"}
    return {"documents": 0, "model": "unknown"}


@app.post("/api/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        query = body.get("query", "")

        if not query:
            return {"error": "No query provided"}

        session = await get_session()

        # Retrieve context
        context = await session.retrieve(query)

        # Build response
        sources = []
        if context.documents:
            for i, (meta, dist) in enumerate(zip(context.metadatas, context.distances, strict=False), 1):
                path = meta.get("path", "unknown")
                sources.append(f"{i}. {path} (dist: {dist:.3f})")

        # Stream response from Ollama
        full_response = [chunk async for chunk in session.stream_response(query, context)]

        response_text = "".join(full_response)

        # Update history
        session.history.append({"role": "user", "content": query})
        session.history.append({"role": "assistant", "content": response_text})

        return {
            "response": response_text,
            "sources": sources,
            "intent": context.intent,
        }

    except Exception as e:
        import traceback
        return {"error": f"{str(e)}\n{traceback.format_exc()}"}


if __name__ == "__main__":
    print("=" * 60)
    print("  GRID RAG Chat Server")
    print("=" * 60)
    print("  URL: http://localhost:8766")
    print("  Model: ministral-3:3b")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8766, log_level="warning")
