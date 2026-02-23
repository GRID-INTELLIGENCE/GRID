/**
 * In-memory tool registry — stores Tool instances for the executor and UI.
 */

import type { Tool, ToolMetadata } from "@/schema/tools";

class ToolRegistry {
  private _tools = new Map<string, Tool>();

  get size(): number {
    return this._tools.size;
  }

  register(tool: Tool): void {
    if (this._tools.has(tool.id)) {
      throw new Error(`Tool "${tool.id}" is already registered`);
    }
    this._tools.set(tool.id, tool);
  }

  unregister(id: string): boolean {
    return this._tools.delete(id);
  }

  get(id: string): Tool | undefined {
    return this._tools.get(id);
  }

  has(id: string): boolean {
    return this._tools.has(id);
  }

  getAll(): Tool[] {
    return [...this._tools.values()];
  }

  getByCategory(category: string): Tool[] {
    return this.getAll().filter((t) => t.category === category);
  }

  getMetadata(): ToolMetadata[] {
    return this.getAll().map((t) => ({
      id: t.id,
      name: t.name,
      description: t.description,
      category: t.category,
    }));
  }

  clear(): void {
    this._tools.clear();
  }
}

export const toolRegistry = new ToolRegistry();
