import type {
  GridAPI,
  OllamaAPI,
  ToolsAPI,
  WindowAPI,
} from "../../electron/preload";

declare global {
  interface Window {
    grid: GridAPI;
    ollama: OllamaAPI;
    tools: ToolsAPI;
    windowControls: WindowAPI;
  }
}
