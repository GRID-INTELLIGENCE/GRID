@echo off
cd /d E:\grid-rag-enhanced
set PYTHONPATH=E:\grid-rag-enhanced\src;E:\grid-rag-enhanced
.venv\Scripts\python.exe -m grid.mcp.enhanced_rag_server
