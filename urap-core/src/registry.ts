import type { UrapTool } from './types.js';

const toolRegistry: UrapTool[] = [];

export function registerTool(tool: UrapTool): void {
  toolRegistry.push(tool);
}

export function getToolsByPillar(pillar: 'data' | 'engagement' | 'automation'): UrapTool[] {
  return toolRegistry.filter(t => t.pillar === pillar);
}

export function getAllTools(): UrapTool[] {
  return [...toolRegistry];
}

export function getToolById(id: string): UrapTool | undefined {
  return toolRegistry.find(t => t.id === id);
}
