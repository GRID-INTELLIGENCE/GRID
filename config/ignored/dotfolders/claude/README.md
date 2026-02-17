# GRID Skills Registry - Claude's Skill Definitions

This directory contains actionable, concrete skills for GRID powered by existing modules.

---

## 📚 Documentation Index

### Getting Started
- **[QUICK_START.md](guides/QUICK_START.md)** - 5-minute quick start with examples
- **[CLAUDE_SETUP.md](guides/CLAUDE_SETUP.md)** - Installation and setup guide

### Understanding Skills
- **[ACTIONABLE_SKILLS.md](guides/ACTIONABLE_SKILLS.md)** - Philosophy and design of each skill
- **[SKILLS_MANIFEST.md](skills/SKILLS_MANIFEST.md)** - Detailed API reference for all skills

### Creating Skills
- **[SKILL_DEVELOPMENT.md](guides/SKILL_DEVELOPMENT.md)** - How to create new skills

---

## 🎯 Available Skills

| Skill ID | Purpose | Status |
|----------|---------|--------|
| `intelligence.git_analyze` | Analyze git changes with AI | ✅ Ready |
| `rag.query_knowledge` | Query GRID's knowledge base | ✅ Ready |
| `patterns.detect_entities` | Extract entities from text | ✅ Ready |
| `analysis.process_context` | Full analysis pipeline | ✅ Ready |
| `youtube.transcript_analyze` | Analyze transcripts | ✅ Ready |

---

## 🚀 Quick Examples

### List all skills
```powershell
.\venv\Scripts\python.exe -m grid skills list
```

### Extract entities from text
```powershell
.\venv\Scripts\python.exe -m grid skills run patterns.detect_entities \
  --args-json "{text:'John Smith works at Microsoft'}"
```

### Query knowledge base
```powershell
.\venv\Scripts\python.exe -m grid skills run rag.query_knowledge \
  --args-json "{query:'How does RAG work?', top_k:3}"
```

### Analyze git changes
```powershell
.\venv\Scripts\python.exe -m grid skills run intelligence.git_analyze \
  --args-json "{verbose:true}"
```

### Full context analysis
```powershell
.\venv\Scripts\python.exe -m grid skills run analysis.process_context \
  --args-json "{text:'Great new feature!', include_sentiment:true}"
```

---

## 📖 Learning Path

1. Start with [QUICK_START.md](guides/QUICK_START.md)
2. Understand design in [ACTIONABLE_SKILLS.md](guides/ACTIONABLE_SKILLS.md)
3. Explore API in [SKILLS_MANIFEST.md](skills/SKILLS_MANIFEST.md)
4. Create custom skills with [SKILL_DEVELOPMENT.md](guides/SKILL_DEVELOPMENT.md)

---

## 🔧 Folder Structure

```
.claude/
├── skills/
│   ├── SKILLS_MANIFEST.md              # API reference for all skills
│   ├── intelligence_git_analyze.py      # Git intelligence skill
│   ├── rag_query_knowledge.py           # RAG query skill
│   ├── patterns_detect_entities.py      # Entity extraction skill
│   └── analysis_process_context.py      # Full analysis skill
│
└── guides/
    ├── QUICK_START.md                  # 5-minute quickstart
    ├── ACTIONABLE_SKILLS.md            # Design philosophy
    ├── SKILL_DEVELOPMENT.md            # How to create skills
    └── CLAUDE_SETUP.md                 # Setup & troubleshooting
```

---

## ✨ Key Features

✅ **Local-First**: All skills run locally, no external APIs required
✅ **Composable**: Output of one skill feeds into another
✅ **Observable**: Includes timing, confidence, and metadata
✅ **Fallback-Safe**: Gracefully degrades if dependencies missing
✅ **Well-Documented**: Examples, API docs, and guides included

---

## 🎓 Design Philosophy

Each skill:
- **Wraps existing GRID code** for consistency
- **Has clear input/output schemas** for predictability
- **Includes fallbacks** for robustness
- **Returns structured data** for composability
- **Includes metadata** (timing, confidence, sources)

---

## 💡 What Problems Do Skills Solve?

| Problem | Solution |
|---------|----------|
| Too many diffs to understand | `intelligence.git_analyze` |
| Can't find things in docs | `rag.query_knowledge` |
| Unstructured text is hard | `patterns.detect_entities` |
| Need complete analysis | `analysis.process_context` |
| Long transcripts | `youtube.transcript_analyze` |

---

## 🚀 Next Steps

1. Follow [CLAUDE_SETUP.md](guides/CLAUDE_SETUP.md) to install
2. Try examples in [QUICK_START.md](guides/QUICK_START.md)
3. Read [ACTIONABLE_SKILLS.md](guides/ACTIONABLE_SKILLS.md) to understand design
4. Create custom skills with [SKILL_DEVELOPMENT.md](guides/SKILL_DEVELOPMENT.md)

---

## 📞 Support

- Skills not loading? → Check [CLAUDE_SETUP.md](guides/CLAUDE_SETUP.md#troubleshooting)
- Need API details? → See [SKILLS_MANIFEST.md](skills/SKILLS_MANIFEST.md)
- Want custom skills? → Read [SKILL_DEVELOPMENT.md](guides/SKILL_DEVELOPMENT.md)
- Understand the design? → [ACTIONABLE_SKILLS.md](guides/ACTIONABLE_SKILLS.md)

---

**Created**: `.claude` folder with actionable skill definitions for GRID
**Status**: Ready for development and deployment
**Documentation**: Complete with guides and examples
