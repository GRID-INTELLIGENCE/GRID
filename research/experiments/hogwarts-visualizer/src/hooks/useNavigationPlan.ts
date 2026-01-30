import { useState, useCallback } from 'react';
import { NavigationPlan } from '../types/navigation';
import { fetchNavigationPlan } from '../services/api/navigation';
import { mockFetchNavigationPlan } from '../services/mock/mockNavigation';

interface UseNavigationPlanOptions {
  useMock?: boolean;
}

interface UseNavigationPlanReturn {
  plan: NavigationPlan | null;
  loading: boolean;
  error: string | null;
  generatePlan: (goal: string, context?: Record<string, unknown>) => Promise<void>;
  clearPlan: () => void;
}

export const useNavigationPlan = (
  options: UseNavigationPlanOptions = {}
): UseNavigationPlanReturn => {
  const { useMock = true } = options;
  const [plan, setPlan] = useState<NavigationPlan | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const generatePlan = useCallback(
    async (goal: string, context?: Record<string, unknown>) => {
      setLoading(true);
      setError(null);

      try {
        const response = useMock
          ? await mockFetchNavigationPlan(goal, context)
          : await fetchNavigationPlan(goal, context);

        if (response.success && response.data) {
          setPlan(response.data);
        } else {
          setError(response.error?.message || 'Failed to fetch navigation plan');
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred';
        setError(errorMessage);
        console.error('Navigation plan error:', err);
      } finally {
        setLoading(false);
      }
    },
    [useMock]
  );

  const clearPlan = useCallback(() => {
    setPlan(null);
    setError(null);
  }, []);

  return { plan, loading, error, generatePlan, clearPlan };
};
