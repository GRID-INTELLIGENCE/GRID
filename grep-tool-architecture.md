# Grep Tool Architecture

```mermaid
graph TD
    subgraph Browser
        A[Web Page] -->|User selects text| B[Content Script]
        B -->|Show Context Menu| C[Context Menu]
        C -->|User clicks 'Grep Search'| D[Popup UI]
        D -->|Search Request| B
        B -->|Search in Selection| E[Search Engine]
        E -->|Results| B
        B -->|Display Results| F[Highlighted Matches]
        
        subgraph Extension
            B[Content Script]
            G[Background Script]
            H[Popup UI]
            I[Options Page]
            
            B <-->|Messaging| G
            H <-->|Messaging| G
            I <-->|Storage| G
        end
    end

    subgraph Data
        J[Search Patterns]
        K[Search History]
        L[Settings]
    end
    
    G <-->|Store/Load| J
    G <-->|Store/Load| K
    G <-->|Store/Load| L

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style C fill:#f96,stroke:#333,stroke-width:2px
    style D fill:#9f9,stroke:#333,stroke-width:2px
    style E fill:#f99,stroke:#333,stroke-width:2px
    style F fill:#9ff,stroke:#333,stroke-width:2px
    style G fill:#ff9,stroke:#333,stroke-width:2px
    style H fill:#9f9,stroke:#333,stroke-width:2px
    style I fill:#99f,stroke:#333,stroke-width:2px
    style J fill:#f9f,stroke:#333,stroke-width:2px
    style K fill:#f9f,stroke:#333,stroke-width:2px
    style L fill:#f9f,stroke:#333,stroke-width:2px
```

## Component Descriptions

1. **Web Page**
   - The target webpage where text is selected
   - Content script runs in this context

2. **Content Script**
   - Injects UI elements into the page
   - Listens for text selection events
   - Handles search execution on selected text
   - Manages highlighting of matches

3. **Context Menu**
   - Appears on right-click when text is selected
   - Triggers the grep search popup

4. **Popup UI**
   - Modal interface for entering search patterns
   - Displays search results
   - Provides search options (case sensitivity, regex, etc.)

5. **Search Engine**
   - Processes the selected text
   - Implements grep-like search functionality
   - Supports regex patterns
   - Returns matched lines with context

6. **Background Script**
   - Manages extension state
   - Handles communication between components
   - Manages storage for settings and history

7. **Options Page**
   - User preferences
   - Search history management
   - Export/import functionality

8. **Data Storage**
   - Search patterns (saved searches)
   - Search history
   - User settings and preferences
