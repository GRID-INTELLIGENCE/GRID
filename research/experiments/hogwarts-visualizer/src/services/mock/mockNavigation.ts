import { NavigationPlanResponse, NavigationPlan, NavigationPath, NavigationStep } from '../../types/navigation';

/**
 * Mock navigation service for offline development and testing.
 */
export const mockFetchNavigationPlan = async (
  goal: string,
  context?: Record<string, unknown>
): Promise<NavigationPlanResponse> => {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 500));

  const mockSteps: NavigationStep[] = [
    {
      id: 'step-1',
      name: 'Define Goal',
      description: `Clarify and define the goal: ${goal}`,
      estimated_time_seconds: 60,
      dependencies: [],
      outputs: ['defined-goal'],
      confidence: 0.95,
    },
    {
      id: 'step-2',
      name: 'Analyze Context',
      description: 'Analyze the current context and constraints',
      estimated_time_seconds: 120,
      dependencies: ['step-1'],
      outputs: ['context-analysis'],
      confidence: 0.85,
    },
    {
      id: 'step-3',
      name: 'Generate Paths',
      description: 'Generate possible navigation paths',
      estimated_time_seconds: 180,
      dependencies: ['step-2'],
      outputs: ['navigation-paths'],
      confidence: 0.80,
    },
    {
      id: 'step-4',
      name: 'Select Optimal Path',
      description: 'Select the most optimal path based on criteria',
      estimated_time_seconds: 90,
      dependencies: ['step-3'],
      outputs: ['selected-path'],
      confidence: 0.90,
    },
  ];

  const mockPath: NavigationPath = {
    id: 'path-1',
    name: 'Optimal Path',
    description: `Best path to achieve: ${goal}`,
    steps: mockSteps,
    complexity: 'medium',
    estimated_total_time: 450,
    confidence: 0.85,
    recommendation_score: 0.9,
    reasoning: 'This path provides the best balance of speed and reliability.',
    metadata: {
      context: context || {},
    },
  };

  const mockPlan: NavigationPlan = {
    request_id: `mock-${Date.now()}`,
    reasoning: `Generated mock navigation plan for goal: ${goal}`,
    processing_time_ms: 500,
    learning_applied: false,
    adaptation_triggered: false,
    recommended_path: mockPath,
    paths: [mockPath],
    confidence_scores: {
      overall: 0.85,
      goal_clarity: 0.95,
      path_quality: 0.80,
    },
    metadata: {
      source: 'mock',
      generated_at: new Date().toISOString(),
    },
  };

  return {
    success: true,
    data: mockPlan,
    meta: {
      request_id: mockPlan.request_id,
      timestamp: new Date().toISOString(),
      version: '1.0.0',
    },
  };
};

export default {
  fetchNavigationPlan: mockFetchNavigationPlan,
};
