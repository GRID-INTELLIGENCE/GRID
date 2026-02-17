import apiClient from './client';
import { NavigationRequest, NavigationPlanResponse } from '../../types/navigation';

/**
 * Fetch navigation plan from backend API.
 */
export const fetchNavigationPlan = async (
  goal: string | Record<string, unknown>,
  context?: Record<string, unknown>
): Promise<NavigationPlanResponse> => {
  const request: NavigationRequest = {
    goal,
    context: context || {},
    max_alternatives: 3,
    enable_learning: true,
    source: 'hogwarts-visualizer',
  };

  const response = await apiClient.post<NavigationPlanResponse>('/navigation/plan', request);
  return response.data;
};

export default {
  fetchNavigationPlan,
};
