# GRID MCP Documentation

> **Complete documentation suite for GRID's Model Context Protocol integration with Zed editor**

## 📚 Documentation Index

### Getting Started

1. **[Quick Start Guide](QUICK_START.md)** ⭐ *Start here!*
   - 5-step setup in 10 minutes
   - Prerequisites and installation
   - First steps with MCP
   - Essential troubleshooting

2. **[Complete Guide](MCP_COMPLETE_GUIDE.md)** 📖 *Comprehensive reference*
   - Full architecture overview
   - Detailed server specifications
   - Testing and validation
   - Best practices

### Advanced Topics

3. **[Optimization Guide](OPTIMIZATION_GUIDE.md)** ⚡ *Performance tuning*
   - RAG optimization strategies
   - Server-specific optimizations
   - Caching and resource management
   - Monitoring and profiling

4. **[Troubleshooting Guide](TROUBLESHOOTING.md)** 🔧 *Problem solving*
   - Quick diagnostics
   - Common issues and solutions
   - Reset procedures
   - Error message reference

---

## 🎯 What is GRID MCP?

GRID's Model Context Protocol (MCP) integration provides AI assistants in Zed editor with:

- **Multi-Repository Git Operations** - History, status, and diff across multiple repos
- **Cognitive Intelligence** - Project analysis and code understanding via Mastermind server
- **Local RAG System** - Query documentation using local Ollama models (no cloud APIs)
- **Persistent Memory** - Learn from past interactions and store case history
- **Sequential Reasoning** - Structured problem-solving for complex tasks

### Key Benefits

✅ **100% Local** - No external API calls, complete privacy  
✅ **Project-Aware** - Deep integration with GRID architecture  
✅ **Cognitive Layer** - Decision support aligned with mental models  
✅ **Pattern Learning** - Accumulates knowledge over time  
✅ **Multi-Modal** - File ops, Git, RAG, analysis, all in one place  

---

## 🚀 Quick Setup

```bash
# 1. Install dependencies
pip install -r requirements-mcp.txt

# 2. Pull Ollama models
ollama pull ministral-3:3b
ollama pull nomic-embed-text:latest

# 3. Initialize directories
mkdir -p .rag_db .grid_knowledge src/tools/agent_prompts/.case_memory

# 4. Configure Zed (see QUICK_START.md for full config)

# 5. Test
python tests/mcp/test_mcp_integration.py
```

**Next Steps**: See [Quick Start Guide](QUICK_START.md) for detailed instructions.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Zed Editor                          │
│                  (Model Context Protocol)               │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Filesystem  │  │   GRID Git   │  │ Mastermind   │
│   (Standard) │  │ (Multi-repo) │  │  (Cognitive) │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   GRID RAG   │  │    Memory    │  │  Sequential  │
│   (Local AI) │  │(Case History)│  │   Thinking   │
└──────────────┘  └──────────────┘  └──────────────┘
        │
        ▼
┌─────────────────────────────────────────┐
│  Ollama (Local LLM Infrastructure)      │
│  • ministral-3:3b (LLM)                 │
│  • nomic-embed-text (Embeddings)        │
└─────────────────────────────────────────┘
```

---

## 📋 Server Specifications

### 1. Filesystem Server (Standard)
- **Purpose**: File operations (read, write, search)
- **Provider**: `@modelcontextprotocol/server-filesystem`
- **Scope**: `E:\grid`

### 2. GRID Git Server (Custom)
- **Purpose**: Multi-repository Git operations
- **Source**: `src/grid/mcp/multi_git_server.py`
- **Features**: Status, log, diff, branches across multiple repos

### 3. GRID Mastermind Server (Custom)
- **Purpose**: Cognitive analysis and project navigation
- **Source**: `src/grid/mcp/mastermind_server.py`
- **Features**: File analysis, code search, dependency mapping

### 4. GRID RAG Server (Custom)
- **Purpose**: Local-only RAG with ChromaDB + Ollama
- **Source**: `mcp-setup/server/grid_rag_mcp_server.py`
- **Features**: Index, query, on-demand RAG, semantic search

### 5. Memory Server (Standard)
- **Purpose**: Persistent case history
- **Provider**: `@modelcontextprotocol/server-memory`
- **Storage**: `src/tools/agent_prompts/.case_memory/memory.json`

### 6. Sequential Thinking Server (Standard)
- **Purpose**: Structured reasoning
- **Provider**: `@modelcontextprotocol/server-sequential-thinking`

---

## 🔍 Common Use Cases

### Query Documentation
```
"Query RAG: How does the event processing pipeline work?"
```

### Analyze Code
```
"Analyze the file src/grid/mcp/mastermind_server.py"
"Search for event processing patterns"
```

### Git Operations
```
"Show me the last 10 commits"
"What's the status of the docs repository?"
"Diff README.md between HEAD and HEAD~1"
```

### Store Knowledge
```
"Store a memory about this optimization we just implemented"
"Search memories for similar caching strategies"
```

---

## 📊 Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Git status | <100ms | Per repository |
| Git log (50) | <200ms | Recent commits |
| RAG embedding | <200ms | Per query |
| RAG search | <50ms | Vector similarity |
| RAG generation | <3s | Full response with sources |
| File analysis | <1s | Small to medium files |

See [Optimization Guide](OPTIMIZATION_GUIDE.md) for tuning strategies.

---

## 🛠️ Testing

### Quick Health Check
```bash
python tests/mcp/test_mcp_integration.py
```

### Manual Testing
```bash
# Test RAG
python -m tools.rag.cli query "What are the cognition patterns?"

# Test Git
git -C E:\grid status

# Test Ollama
curl http://localhost:11434/api/tags
```

---

## 🐛 Troubleshooting

### Quick Fixes

1. **"MCP library not found"**
   ```bash
   pip install mcp
   ```

2. **"Cannot connect to Ollama"**
   ```bash
   ollama serve
   ```

3. **"Repository not found"**
   - Check `GIT_MCP_REPOSITORIES` format
   - Use double backslashes on Windows: `"default:E:\\grid"`

4. **Servers not responding**
   - Restart Zed completely
   - Check Zed logs for errors
   - Test server standalone: `python src/grid/mcp/multi_git_server.py`

**Full troubleshooting**: See [Troubleshooting Guide](TROUBLESHOOTING.md)

---

## 📈 Optimization Tips

### Quick Wins
- ✅ Enable RAG caching: `"RAG_CACHE_ENABLED": "true"`
- ✅ Use smaller embedding model: `"BAAI/bge-small-en-v1.5"`
- ✅ Reduce context size: `"max_context_tokens": 2048`
- ✅ Limit git log: `git_log(max_count=10)`

### Advanced
- 🔧 Batch embeddings
- 🔧 Parallel indexing
- 🔧 Multi-level caching
- 🔧 Resource limits

See [Optimization Guide](OPTIMIZATION_GUIDE.md) for details.

---

## 🤝 Contributing

### Reporting Issues

When reporting problems, include:

1. Python version: `python --version`
2. Installed packages: `pip list | grep mcp`
3. Ollama models: `ollama list`
4. Full error message with traceback
5. Configuration (sanitized)

### Adding New Tools

See [Complete Guide](MCP_COMPLETE_GUIDE.md#advanced-topics) for:
- Custom tool development
- Server extension patterns
- Testing strategies

---

## 📚 Related Documentation

- [GRID Architecture](../architecture.md)
- [RAG System](../../tools/rag/README.md)
- [Cognitive Layer](../../light_of_the_seven/README.md)
- [Pattern Language](../pattern_language.md)
- [MCP Protocol Specification](https://modelcontextprotocol.io)

---

## 📝 Version Information

- **MCP Version**: 2.2.0
- **Documentation Version**: 1.0
- **Last Updated**: 2025-01-15
- **Python Required**: 3.13+
- **Zed Required**: Latest stable

---

## ⚡ Quick Reference

### Essential Commands

```bash
# Install
pip install -r requirements-mcp.txt

# Pull models
ollama pull ministral-3:3b
ollama pull nomic-embed-text:latest

# Index docs
python -m tools.rag.cli index docs/ --recursive

# Test
python tests/mcp/test_mcp_integration.py

# Check health
curl http://localhost:11434/api/tags
```

### Essential Paths

| What | Where |
|------|-------|
| Config | Zed `settings.json` |
| Git Server | `src/grid/mcp/multi_git_server.py` |
| Mastermind | `src/grid/mcp/mastermind_server.py` |
| RAG Server | `mcp-setup/server/grid_rag_mcp_server.py` |
| Tests | `tests/mcp/test_mcp_integration.py` |
| RAG DB | `.rag_db/` |
| Memory | `src/tools/agent_prompts/.case_memory/memory.json` |

### Essential Environment Variables

```bash
OLLAMA_BASE_URL=http://localhost:11434
PYTHONPATH=E:\grid\src;E:\grid
GRID_ROOT=E:\grid
RAG_VECTOR_STORE_PATH=E:\grid\.rag_db
GIT_MCP_REPOSITORIES=default:E:\grid;docs:E:\grid\docs
```

---

## 🎓 Learning Path

1. **Beginner**: Start with [Quick Start Guide](QUICK_START.md)
2. **Intermediate**: Read [Complete Guide](MCP_COMPLETE_GUIDE.md)
3. **Advanced**: Study [Optimization Guide](OPTIMIZATION_GUIDE.md)
4. **Troubleshooting**: Keep [Troubleshooting Guide](TROUBLESHOOTING.md) handy

---

## 💡 Pro Tips

- **Index incrementally**: Don't re-index everything, just new docs
- **Use named repos**: Clear which Git repo you're working with
- **Cache aggressively**: Enable all caching options
- **Monitor resources**: Keep an eye on memory usage
- **Test after changes**: Run integration tests after config updates

---

## 🌟 Highlights

**Why GRID MCP is Powerful:**

1. **Local-First AI**: Complete privacy, no cloud dependencies
2. **Multi-Server Architecture**: Each server optimized for its task
3. **Cognitive Integration**: Aligns with GRID's cognitive principles
4. **Pattern Learning**: Gets smarter over time via memory server
5. **Production Ready**: Tested, optimized, and documented

**Perfect For:**
- Complex codebase navigation
- Architecture exploration
- Pattern discovery
- Technical decision support
- Knowledge management

---

**Need Help?** Start with the [Quick Start Guide](QUICK_START.md) or check [Troubleshooting](TROUBLESHOOTING.md).

**Ready to Optimize?** See the [Optimization Guide](OPTIMIZATION_GUIDE.md).

**Want Details?** Read the [Complete Guide](MCP_COMPLETE_GUIDE.md).

---

*Built with ❤️ for the GRID project - Local-first cognitive AI architecture*