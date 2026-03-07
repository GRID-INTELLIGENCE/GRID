# GRID Liftoff: Quick-Start & Env Setup
**Sequence for Immediate Operation**

Follow this liftoff sequence to initialize the GRID environment and start your first intelligence synthesis.

---

## 🚀 1. The Startup Sequence

### Stage 1: Environment Activation
```powershell
# Activate local virtual environment
.\.venv\Scripts\Activate.ps1

# Verify dependencies
pip install -e .
```

### Stage 2: Synthesis Engine Check
```powershell
# Verify Trajectory Diffusion components
python -m motion.trajectory_diffusion --num-samples 1
```

### Stage 3: UI Launch
```powershell
# Launch the Stratagem Intelligence Studio
cd application
npm run dev
```

---

## 🔋 2. Environment Dependencies

| Component | Required Version | Purpose |
|-----------|------------------|---------|
| **Python** | 3.10+ | Core AI & RAG Logic |
| **Node.js** | 18+ | Frontend Dashboard |
| **Rust** | 1.70+ | Acceleration Layer |
| **ripgrep (rg)** | 13+ | `grid-grep` Search Core |

---

## 🛠️ 3. Common Startup Tasks
Use these pre-configured tasks for rapid environment setup:

- **`/setup-grid`**: One-click dependency install and telemetry check.
- **`/verify-stability`**: Run the P0 test battery for core modules.
- **`/rebuild-index`**: Clear and reconstruct the RAG vector database.

---

## 🚨 4. First-Time Troubleshooting
- **ModuleNotFoundError**: Ensure the `.venv` is active and you've run `pip install -e .` from the root.
- **Port 3000 busy**: The dashboard may conflict with other dev servers. Change port in `.env`.
- **RAG failure**: Check `.rag_logs/` for embedding API connection issues.

---

**Status**: Ready for Pilot Ignition
**Date**: 2026-01-06
