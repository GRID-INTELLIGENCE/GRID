"""
Knowledge Base Web Interface
============================

Simple HTML/JavaScript interface for interacting with the Knowledge Base API.
Provides search, ingestion, and management capabilities.
"""


def create_kb_interface(api_base_url: str = "http://localhost:8000") -> str:
    """Create HTML interface for the knowledge base."""

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GRID Knowledge Base</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

        .header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .card {{
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}

        .search-section {{
            margin-bottom: 30px;
        }}

        .search-input {{
            width: 100%;
            padding: 15px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 8px;
            margin-bottom: 15px;
            transition: border-color 0.3s;
        }}

        .search-input:focus {{
            outline: none;
            border-color: #667eea;
        }}

        .button {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            transition: transform 0.2s;
        }}

        .button:hover {{
            transform: translateY(-2px);
        }}

        .results {{
            margin-top: 20px;
        }}

        .result-item {{
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            background: #f9f9f9;
        }}

        .result-score {{
            color: #667eea;
            font-weight: bold;
            margin-bottom: 5px;
        }}

        .result-content {{
            margin-bottom: 10px;
        }}

        .result-meta {{
            font-size: 0.9em;
            color: #666;
        }}

        .tabs {{
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid #eee;
        }}

        .tab {{
            padding: 10px 20px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.3s;
        }}

        .tab.active {{
            border-bottom-color: #667eea;
            color: #667eea;
            font-weight: bold;
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        .form-group {{
            margin-bottom: 15px;
        }}

        .form-group label {{
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }}

        .form-group textarea {{
            width: 100%;
            min-height: 100px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-family: inherit;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}

        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}

        .stat-label {{
            color: #666;
            font-size: 0.9em;
        }}

        .loading {{
            text-align: center;
            padding: 20px;
            color: #666;
        }}

        .error {{
            background: #fee;
            color: #c33;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
        }}

        .success {{
            background: #efe;
            color: #363;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 GRID Knowledge Base</h1>
            <p>Intelligent document search and Q&A system</p>
        </div>

        <div class="tabs">
            <div class="tab active" onclick="showTab('search')">Search</div>
            <div class="tab" onclick="showTab('ask')">Ask AI</div>
            <div class="tab" onclick="showTab('add')">Add Document</div>
            <div class="tab" onclick="showTab('stats')">Statistics</div>
        </div>

        <!-- Search Tab -->
        <div id="search" class="tab-content active">
            <div class="card">
                <h2>🔍 Search Knowledge Base</h2>
                <div class="search-section">
                    <input type="text" id="searchQuery" class="search-input"
                           placeholder="Enter your search query...">
                    <button class="button" onclick="performSearch()">Search</button>
                </div>
                <div id="searchResults" class="results"></div>
            </div>
        </div>

        <!-- Ask AI Tab -->
        <div id="ask" class="tab-content">
            <div class="card">
                <h2>🤖 Ask AI Assistant</h2>
                <div class="search-section">
                    <input type="text" id="askQuery" class="search-input"
                           placeholder="Ask a question...">
                    <button class="button" onclick="askAI()">Ask AI</button>
                </div>
                <div id="aiResponse" class="results"></div>
            </div>
        </div>

        <!-- Add Document Tab -->
        <div id="add" class="tab-content">
            <div class="card">
                <h2>📄 Add New Document</h2>
                <form onsubmit="addDocument(event)">
                    <div class="form-group">
                        <label for="docTitle">Document Title:</label>
                        <input type="text" id="docTitle" class="search-input" required>
                    </div>
                    <div class="form-group">
                        <label for="docContent">Document Content:</label>
                        <textarea id="docContent" placeholder="Paste your document content here..." required></textarea>
                    </div>
                    <button type="submit" class="button">Add Document</button>
                </form>
                <div id="addResult"></div>
            </div>
        </div>

        <!-- Statistics Tab -->
        <div id="stats" class="tab-content">
            <div class="card">
                <h2>📊 System Statistics</h2>
                <button class="button" onclick="loadStats()">Refresh Stats</button>
                <div id="statsContent" class="stats-grid"></div>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = '{api_base_url}';

        // Tab switching
        function showTab(tabName) {{
            // Hide all tabs
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.classList.remove('active'));

            const tabButtons = document.querySelectorAll('.tab');
            tabButtons.forEach(btn => btn.classList.remove('active'));

            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }}

        // Search functionality
        async function performSearch() {{
            const query = document.getElementById('searchQuery').value.trim();
            if (!query) return;

            const resultsDiv = document.getElementById('searchResults');
            resultsDiv.innerHTML = '<div class="loading">Searching...</div>';

            try {{
                const response = await fetch(`${{API_BASE}}/search`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ query: query, limit: 10 }})
                }});

                const data = await response.json();

                if (data.results && data.results.length > 0) {{
                    let html = `<h3>Found ${{data.total_results}} results (${{data.processing_time.toFixed(2)}}s)</h3>`;
                    data.results.forEach(result => {{
                        html += `
                            <div class="result-item">
                                <div class="result-score">Score: ${{result.score.toFixed(3)}}</div>
                                <div class="result-content">${{result.content}}</div>
                                <div class="result-meta">
                                    ${{{{result.document_title || 'Unknown'}}}} + (result.source_type ? ` (${{{{result.source_type}}}})` : '')}}
                                </div>
                            </div>
                        `;
                    }});
                    resultsDiv.innerHTML = html;
                }} else {{
                    resultsDiv.innerHTML = '<div class="error">No results found for your query.</div>';
                }}
            }} catch (error) {{
                resultsDiv.innerHTML = `<div class="error">Search failed: ${{error.message}}</div>`;
            }}
        }}

        // AI Question answering
        async function askAI() {{
            const query = document.getElementById('askQuery').value.trim();
            if (!query) return;

            const responseDiv = document.getElementById('aiResponse');
            responseDiv.innerHTML = '<div class="loading">AI is thinking...</div>';

            try {{
                const response = await fetch(`${{API_BASE}}/generate`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ query: query }})
                }});

                const data = await response.json();

                let html = `
                    <div class="result-item">
                        <h3>🤖 AI Response (Confidence: ${{data.confidence_score}})</h3>
                        <div class="result-content">${{data.answer}}</div>
                        <div class="result-meta">
                            Tokens used: ${{data.token_usage.total_tokens}} |
                            Processing time: ${{data.processing_time.toFixed(2)}}s
                        </div>
                    </div>
                `;

                if (data.sources && data.sources.length > 0) {{
                    html += '<h4>Sources:</h4>';
                    data.sources.forEach(source => {{
                        html += `
                            <div class="result-item">
                                <div class="result-meta">${{source.title}} (Score: ${{source.score.toFixed(3)}})</div>
                                <div class="result-content">${{source.content}}</div>
                            </div>
                        `;
                    }});
                }}

                responseDiv.innerHTML = html;
            }} catch (error) {{
                responseDiv.innerHTML = `<div class="error">AI response failed: ${{error.message}}</div>`;
            }}
        }}

        // Add document
        async function addDocument(event) {{
            event.preventDefault();

            const title = document.getElementById('docTitle').value;
            const content = document.getElementById('docContent').value;

            const resultDiv = document.getElementById('addResult');
            resultDiv.innerHTML = '<div class="loading">Adding document...</div>';

            try {{
                const response = await fetch(`${{API_BASE}}/ingest`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        title: title,
                        content: content,
                        source_type: 'manual'
                    }})
                }});

                const data = await response.json();

                if (data.success) {{
                    resultDiv.innerHTML = `<div class="success">✅ Document added successfully! Created ${{data.chunks_created}} chunks.</div>`;
                    document.getElementById('docTitle').value = '';
                    document.getElementById('docContent').value = '';
                }} else {{
                    resultDiv.innerHTML = `<div class="error">❌ Failed to add document: ${{data.message}}</div>`;
                }}
            }} catch (error) {{
                resultDiv.innerHTML = `<div class="error">❌ Failed to add document: ${{error.message}}</div>`;
            }}
        }}

        // Load statistics
        async function loadStats() {{
            const statsDiv = document.getElementById('statsContent');
            statsDiv.innerHTML = '<div class="loading">Loading statistics...</div>';

            try {{
                const response = await fetch(`${{API_BASE}}/stats`);
                const data = await response.json();

                const stats = [
                    {{ label: 'Total Documents', value: data.documents.total_count }},
                    {{ label: 'Total Chunks', value: data.chunks.total_count }},
                    {{ label: 'Embedded Chunks', value: data.embeddings.embedded_chunks }},
                    {{ label: 'Total Searches', value: data.search.total_searches }},
                    {{ label: 'AI Generations', value: data.generation.total_generations }}
                ];

                let html = '';
                stats.forEach(stat => {{
                    html += `
                        <div class="stat-card">
                            <div class="stat-number">${{stat.value || 0}}</div>
                            <div class="stat-label">${{stat.label}}</div>
                        </div>
                    `;
                }});

                statsDiv.innerHTML = html;
            }} catch (error) {{
                statsDiv.innerHTML = `<div class="error">Failed to load statistics: ${{error.message}}</div>`;
            }}
        }}

        // Keyboard shortcuts
        document.addEventListener('keydown', function(event) {{
            if (event.ctrlKey && event.key === 'k') {{
                event.preventDefault();
                document.getElementById('searchQuery').focus();
            }}
        }});

        // Load initial stats
        loadStats();
    </script>
</body>
</html>"""

    return html_content


def save_kb_interface(file_path: str, api_base_url: str = "http://localhost:8000") -> None:
    """Save the knowledge base interface to a file."""
    html_content = create_kb_interface(api_base_url)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Knowledge Base interface saved to: {file_path}")


if __name__ == "__main__":
    # Save interface for development
    save_kb_interface("kb_interface.html")
