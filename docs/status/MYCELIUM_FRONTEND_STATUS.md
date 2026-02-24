# Mycelium Frontend — Technical Status Report

**Date**: 2026-02-24
**Scope**: All frontend files related to the Mycelium module
**Audit Method**: Line-by-line code analysis of 10 files, ~1,800 lines total

---

## 1. Architecture Overview

```
                      ┌──────────────────────┐
                      │   MyceliumPage.tsx    │  Main interactive page
                      │      (299 lines)     │
                      └──────────┬───────────┘
                                 │ uses
                      ┌──────────▼───────────┐
                      │   use-mycelium.ts     │  State + IPC bridge hook
                      │      (323 lines)     │
                      └──────────┬───────────┘
                                 │ dispatches to
                      ┌──────────▼───────────┐
                      │    useReducer FSM     │  9 action types
                      │  (MyceliumState)      │
                      └──────────────────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           │                     │                     │
  ┌────────▼─────────┐  ┌───────▼────────┐   ┌───────▼────────┐
  │  OutputDisplay   │  │   LensCard     │   │  SensoryPicker │
  │   (114 lines)    │  │   (87 lines)   │   │   (63 lines)   │
  └────────┬─────────┘  └────────────────┘   └────────────────┘
           │
  ┌────────▼─────────┐  ┌────────────────┐   ┌────────────────┐
  │  HighlightPill   │  │  FeedbackBar   │   │  DepthControl  │
  │   (38 lines)     │  │   (63 lines)   │   │   (46 lines)   │
  └──────────────────┘  └────────────────┘   └────────────────┘

  Standalone:
  ┌────────────────────────────────────────────────────────────┐
  │ MyceliumDemo.tsx — Self-contained presentation page        │
  │ (450 lines, no external data deps, client-side synthesis)  │
  └────────────────────────────────────────────────────────────┘
```

### File Inventory

| File | Lines | Role | Quality |
|------|------:|------|---------|
| `pages/MyceliumPage.tsx` | 299 | Main page — input, synthesis, concept explorer | ✅ Solid |
| `pages/MyceliumDemo.tsx` | 450 | Standalone presentation demo | ✅ Good |
| `hooks/use-mycelium.ts` | 323 | State management + IPC bridge + local fallback | ⚠️ Issues |
| `components/mycelium/OutputDisplay.tsx` | 114 | Renders synthesis results | ✅ Good |
| `components/mycelium/LensCard.tsx` | 87 | Concept exploration card | ✅ Good |
| `components/mycelium/HighlightPill.tsx` | 38 | Keyword pill component | ✅ Good |
| `components/mycelium/FeedbackBar.tsx` | 63 | Simpler/Deeper feedback buttons | ✅ Good |
| `components/mycelium/DepthControl.tsx` | 46 | Espresso/Americano/Cold Brew selector | ✅ Good |
| `components/mycelium/SensoryPicker.tsx` | 63 | Accessibility profile selector | ✅ Good |
| `types/mycelium.ts` | 79 | Type definitions | ✅ Complete |
| `__tests__/MyceliumPage.test.tsx` | 151 | 10 test cases | ⚠️ Coverage gaps |

---

## 2. Current Strengths

### ✅ Solid Architecture
- **useReducer pattern** is the right choice for this state shape. 9 action types cover all transitions cleanly.
- **Bridge abstraction** (`getBridge()`) provides clean separation between Electron IPC and browser fallback.
- **Component granularity** is excellent — 6 focused, reusable components averaging 68 lines each.

### ✅ Accessibility
- All interactive elements have `aria-label`, `aria-expanded`, `role`, `aria-checked`.
- `DepthControl` and `SensoryPicker` both use `fieldset/legend` with `role="radio"` — correct ARIA pattern.
- `aria-live="polite"` on the gist output for screen reader announcements.
- Focus-visible ring styling on every interactive element.

### ✅ Progressive Disclosure
- Settings panel is hidden by default, toggleable.
- Full explanation is behind an expand/collapse control.
- Concept library is a secondary action, not cluttering the main view.
- Feedback bar appears only after synthesis.

### ✅ Keyboard Support
- `Ctrl+Enter` shortcut for synthesis.
- All custom buttons are `type="button"` (no accidental form submissions).

### ✅ Type Safety
- All types in `types/mycelium.ts` are well-defined with proper union types.
- `Highlight["priority"]` is correctly used as a constraint key in `HighlightPill`.
- No `any` types anywhere.

---

## 3. Issues Found

### 🔴 Critical: Bridge Instance Recreated Every Render

**File**: `use-mycelium.ts`, line 212
**Code**: `const bridge = getBridge();`

```typescript
export function useMycelium() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const bridge = getBridge(); // ← Called on EVERY render
```

**Problem**: `getBridge()` is called on every render of the component. When `window.mycelium` is undefined (browser mode), `createLocalBridge()` creates a new object every render. This means:
1. Every `useCallback` that depends on `bridge` (synthesize, feedback, explore, tryDifferent, loadConcepts, setSensory) has `bridge` in its dependency array — so **all callbacks are recreated every render**, defeating memoization.
2. The child components (`FeedbackBar`, `LensCard`, etc.) receive new function references every render, causing unnecessary re-renders.

**Impact**: Performance degradation, especially with frequent state changes. Every keystroke in the textarea triggers `setInput` → dispatch → re-render → new bridge → new callbacks.

**Fix**: Memoize the bridge with `useRef` or `useMemo`:
```typescript
const bridge = useMemo(() => getBridge(), []); // Created once
```

---

### 🔴 Critical: `eslint-disable` Masking a Real Bug

**File**: `MyceliumPage.tsx`, lines 27-30

```typescript
useEffect(() => {
  m.loadConcepts();
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, []);
```

**Problem**: `m.loadConcepts` is NOT stable — it changes every render (see bridge issue above). The `eslint-disable` hides a real issue: this effect's dependency is stale. Because the bridge is recreated every render but the effect only runs once, it captures the initial bridge instance. In Electron mode (where `window.mycelium` exists), this works by accident because the bridge object is the same. In browser mode, the local bridge is recreated but the effect already has a closure over the first one — which is fine functionally but architecturally fragile.

**Fix**: Make `loadConcepts` stable by fixing the bridge memoization (see above), then remove the eslint-disable.

---

### 🟡 Medium: `handleInput` useCallback Depends on Unstable `m`

**File**: `MyceliumPage.tsx`, line 41

```typescript
const handleInput = useCallback(
  (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    m.setInput(e.target.value);
    ...
  },
  [m], // ← m changes every render
);
```

**Problem**: The entire return value of `useMycelium()` is spread as `m`, so `m` is a new object every render. Using `[m]` as a dependency means `handleInput` is recreated every render — the `useCallback` is doing nothing.

**Fix**: Destructure what's needed: `const { setInput, synthesize, ... } = useMycelium()` and depend on individual stable functions.

---

### 🟡 Medium: No Debounce on Textarea Auto-Resize

**File**: `MyceliumPage.tsx`, lines 36-38

```typescript
el.style.height = "auto";
el.style.height = Math.min(el.scrollHeight, 320) + "px";
```

**Problem**: Direct DOM manipulation (`el.style.height`) on every keystroke triggers layout reflow. For large text inputs with rapid typing, this creates a layout thrash pattern: set height → browser reflows → measure scrollHeight → set height again. Two forced reflows per keystroke.

**Impact**: Noticeable jank on slower machines or when pasting large text blocks.

**Fix**: Debounce the resize, or use `requestAnimationFrame` to batch:
```typescript
requestAnimationFrame(() => {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 320) + "px";
});
```

---

### 🟡 Medium: `filteredConcepts` Recomputed Every Render

**File**: `MyceliumPage.tsx`, lines 62-64

```typescript
const filteredConcepts = m.concepts.filter((c) =>
  c.toLowerCase().includes(conceptSearch.toLowerCase()),
);
```

**Problem**: This runs on every render, not just when `concepts` or `conceptSearch` change. With 16+ concepts this is negligible, but it's a pattern issue — it should be `useMemo`.

**Fix**:
```typescript
const filteredConcepts = useMemo(
  () => m.concepts.filter((c) =>
    c.toLowerCase().includes(conceptSearch.toLowerCase())
  ),
  [m.concepts, conceptSearch]
);
```

---

### 🟡 Medium: Missing `window.mycelium` in Browser Shim

**File**: `lib/browser-shim.ts`

**Problem**: The browser shim provides `window.grid`, `window.ollama`, and `window.tools`, but does NOT provide `window.mycelium`. The Mycelium page works because `use-mycelium.ts` has its own fallback (`createLocalBridge`), but this creates an inconsistency:
- Grid/Ollama pages: browser shim → realistic demo data
- Mycelium page: separate local bridge → different mock patterns

This means two independent fallback systems coexist with different design patterns and different data quality.

**Fix**: Add `window.mycelium` to the browser shim, consolidating fallback logic in one place. Keep `createLocalBridge` as a safety net but have the shim take priority.

---

### 🟡 Medium: Duplicate Keyword Extraction Logic

**Problem**: Keyword extraction (stop-word removal + frequency counting) exists in THREE places:
1. `use-mycelium.ts` → `extractHighlights()` (lines 94-116)
2. `MyceliumDemo.tsx` → `extractKeywords()` (lines 146-153)
3. `MyceliumDemo.tsx` → `STOP` set (lines 139-144)

Each has slightly different stop-word lists, different minimum word lengths, and different output formats. This violates DRY and creates inconsistency.

**Fix**: Extract a shared `extractKeywords(text, topN)` utility into `lib/text-utils.ts`.

---

### 🟢 Minor: `OutputDisplay` Has Stale `id` for Explanation

**File**: `OutputDisplay.tsx`, line 97

```html
<div id="mycelium-explanation" ...>
```

**Problem**: If multiple `OutputDisplay` instances were ever rendered (unlikely currently, but possible in future), they'd share the same `id`, violating HTML spec. The `aria-controls="mycelium-explanation"` would reference ambiguously.

**Fix**: Use `useId()` from React 18+:
```typescript
const explanationId = useId();
```

---

### 🟢 Minor: `explore("")` Used as Close Mechanism

**File**: `MyceliumPage.tsx`, line 230

```typescript
onClose={() => m.explore("")}
```

**Problem**: Calling `explore("")` triggers an async IPC call to the backend with an empty concept string, just to close the card. The backend receives a meaningless request. This should be a simple dispatch instead.

**Fix**: Add a `clearExplored` action:
```typescript
const clearExplored = useCallback(() => {
  dispatch({ type: "SET_EXPLORED", payload: null });
}, []);
```

---

### 🟢 Minor: Missing `login` Route in JSON Config

**File**: `app.config.json`

There's a `register` route entry but `login` is only defined as a `RouteKey` in `app-schema.ts` — the JSON config has `register` with empty `navLabel` and `icon` but no corresponding `login` entry. This is a pre-existing issue, not Mycelium-specific, but it will cause a runtime error if the login route is rendered.

---

## 4. Test Coverage Analysis

### Current Coverage (10 tests)

| Test | Coverage Area | Status |
|------|-------------|--------|
| Renders page header and input area | Basic render | ✅ |
| Synthesize button disabled when empty | Input validation | ✅ |
| Enables button when text entered | Input enabling | ✅ |
| Character count display | UI feedback | ✅ |
| Calls synthesize and displays gist | Core flow | ✅ |
| Displays highlights after synthesis | Keyword rendering | ✅ |
| Depth control with three options | Control rendering | ✅ |
| Switches depth on click | Control interaction | ✅ |
| Opens accessibility settings | Panel toggle | ✅ |
| Shows feedback bar after synthesis | Post-synthesis UI | ✅ |
| Clears input and results | Clear action | ✅ |
| Loads concepts on mount | Initialization | ✅ |

### ⚠️ Missing Test Coverage

| Missing Test | Risk Level | Notes |
|-------------|-----------|-------|
| **Ctrl+Enter keyboard shortcut** | High | Core UX shortcut, untested |
| **Error state rendering** | High | Error display path not verified |
| **Concept exploration flow** | High | Clicking keyword → LensCard → close |
| **"Try different lens" interaction** | Medium | `tryDifferent` callback untested |
| **Feedback (Simpler/Deeper)** | Medium | Only checks button exists, not click behavior |
| **Sensory profile switching** | Medium | SensoryPicker render untested |
| **Concept browser panel** | Medium | Panel open/search/select untested |
| **Large text input performance** | Low | No stress test for textarea resize |
| **MyceliumDemo page** | Low | No tests at all for demo page |

---

## 5. Improvement Opportunities (Prioritized)

### Priority 1 — Performance (Quick Wins)

| # | Fix | Impact | Effort |
|---|-----|--------|--------|
| P1.1 | Memoize `getBridge()` with `useMemo`/`useRef` | Eliminates callback churn across entire component tree | 5 min |
| P1.2 | Destructure `useMycelium()` return in `MyceliumPage` | Makes `useCallback` deps actually stable | 10 min |
| P1.3 | Wrap `filteredConcepts` in `useMemo` | Prevents unnecessary filter on every render | 2 min |
| P1.4 | Add `requestAnimationFrame` to textarea resize | Eliminates double-reflow per keystroke | 3 min |

### Priority 2 — Architecture (Code Quality)

| # | Fix | Impact | Effort |
|---|-----|--------|--------|
| P2.1 | Add `clearExplored` dispatch instead of `explore("")` | Eliminates wasteful IPC call on close | 5 min |
| P2.2 | Extract shared `extractKeywords` utility | Removes triple-duplicated logic | 15 min |
| P2.3 | Add `window.mycelium` to browser shim | Single source of truth for all fallback data | 20 min |
| P2.4 | Remove `eslint-disable` after fixing bridge stability | Removes tech debt | 1 min |

### Priority 3 — Test Coverage

| # | Fix | Impact | Effort |
|---|-----|--------|--------|
| P3.1 | Add Ctrl+Enter keyboard shortcut test | Validates core UX | 10 min |
| P3.2 | Add error state rendering test | Validates error path | 10 min |
| P3.3 | Add concept exploration flow test | Validates keyword → explore → close | 15 min |
| P3.4 | Add feedback button click behavior test | Validates depth adjustment | 15 min |

### Priority 4 — Feature Enhancements

| # | Enhancement | Value | Effort |
|---|------------|-------|--------|
| P4.1 | **Synthesis history**: Store last N results in `localStorage` with timestamps | Users can revisit past analyses without re-synthesizing | 30 min |
| P4.2 | **Copy-to-clipboard** button on gist/summary | Basic UX expectation for text tools | 10 min |
| P4.3 | **Animated transitions** between persona results on Demo page | Polish for presentations | 20 min |
| P4.4 | **Word count + reading time** estimate alongside char count | Useful context metric | 5 min |
| P4.5 | **Export as Markdown** button | Allows sharing synthesis results | 20 min |
| P4.6 | **Drag-and-drop file input** for text files | Convenience for longer documents | 30 min |
| P4.7 | **Compare mode** in Demo page: side-by-side 2 personas | Stronger demo impact | 45 min |

---

## 6. Dependency Map

```
MyceliumPage.tsx
├── use-mycelium.ts
│   ├── types/mycelium.ts (all types)
│   └── window.mycelium (Electron IPC) OR createLocalBridge()
├── components/mycelium/
│   ├── OutputDisplay.tsx
│   │   └── HighlightPill.tsx
│   ├── LensCard.tsx
│   ├── FeedbackBar.tsx (no deps)
│   ├── DepthControl.tsx
│   │   └── types/mycelium.ts (Depth)
│   └── SensoryPicker.tsx
│       └── types/mycelium.ts (SensoryProfile)
└── lib/utils.ts (cn)

MyceliumDemo.tsx
├── lib/utils.ts (cn)
└── lucide-react (icons)
   [No external data dependencies — fully self-contained]
```

### Electron IPC Path (when available):
```
MyceliumPage → use-mycelium.ts → window.mycelium.synthesize()
  → electron/preload.ts → ipcRenderer.invoke("mycelium:synthesize")
  → electron/main.ts → Python subprocess call
  → src/mycelium/instrument.py → SynthesisResult
```

**NOTE**: The `electron/preload.ts` file does NOT expose `window.mycelium`. This means
the Electron IPC path for Mycelium hasn't been wired yet. The `use-mycelium.ts` hook
correctly falls back to `createLocalBridge()` in all cases. **Mycelium currently runs
entirely client-side** regardless of Electron or browser mode.

---

## 7. Summary

**Overall Health**: 🟡 **Good with known performance issues**

The Mycelium frontend is well-structured, accessible, and feature-complete for its current scope. The main issue is **callback instability caused by bridge recreation on every render** (Priority 1.1), which cascades into unnecessary re-renders across the component tree. This is the single highest-impact fix.

The test suite covers happy-path rendering well but misses interaction flows (keyboard shortcuts, concept exploration, feedback behavior). The duplicate keyword extraction logic across three files is a maintenance risk that should be consolidated.

The Electron IPC bridge for Mycelium is not yet wired in `preload.ts`, meaning the module runs entirely on client-side heuristics. This is fine for the current local-first architecture but should be documented as an intentional design choice vs. a missing feature.

**Recommended immediate actions**: P1.1 (5 min) → P1.2 (10 min) → P2.1 (5 min) = 20 minutes for significant improvement.
