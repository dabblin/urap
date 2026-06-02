import type { UrapTool } from './types.js';

const toolRegistry: UrapTool[] = [];

export function registerTool(tool: UrapTool): void {
  toolRegistry.push(tool);
}

export function getToolsByPillar(pillar: 'data' | 'engagement' | 'automation'): UrapTool[] {
  return toolRegistry.filter(t => t.pillar === pillar && !t.featureFlag);
}

export function getAllTools(): UrapTool[] {
  return [...toolRegistry];
}

// Sprint 0 seed — tools registered as sprints complete.
// Each sprint calls registerTool() for its deliverables. No hardcoded nav.
