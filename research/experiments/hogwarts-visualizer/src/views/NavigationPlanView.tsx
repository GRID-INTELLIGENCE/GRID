import React, { useState } from 'react';
import { HouseThemedCard, WizardButton, SpellboundInput, LoadingSpinner } from '../components';
import { NavigationPathChart, ConfidenceRadar } from '../components/charts';
import { useHouse } from '../contexts';
import { NavigationPath, NavigationStep } from '../types';
import { useNavigationPlan } from '../hooks';
import { formatTime, formatConfidence, formatProcessingTime } from '../utils';

export const NavigationPlanView: React.FC = () => {
  const { houseTheme } = useHouse();
  const { colors } = houseTheme;
  const [goal, setGoal] = useState<string>('');
  const [useMock, setUseMock] = useState<boolean>(true);

  const { plan, loading, error, generatePlan } = useNavigationPlan({ useMock });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!goal.trim()) {
      return;
    }
    await generatePlan(goal);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="mb-6">
        <h2 className="text-3xl font-bold mb-2" style={{ color: colors.primary }}>
          Navigation Plan Generator
        </h2>
        <p className="text-gray-400">Create intelligent navigation plans for your goals</p>
      </div>

      <HouseThemedCard>
        <form onSubmit={handleSubmit} className="space-y-4">
          <SpellboundInput
            label="Navigation Goal"
            type="text"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="Enter your goal (e.g., 'Optimize user onboarding flow')"
            disabled={loading}
          />

          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={useMock}
                onChange={(e) => setUseMock(e.target.checked)}
                className="rounded"
                disabled={loading}
              />
              <span className="text-sm text-gray-400">Use mock data (offline mode)</span>
            </label>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-red-900/20 border border-red-500 text-red-400">
              {error}
            </div>
          )}

          <WizardButton type="submit" disabled={loading}>
            {loading ? 'Generating Plan...' : 'Generate Navigation Plan'}
          </WizardButton>
        </form>
      </HouseThemedCard>

      {loading && (
        <HouseThemedCard>
          <LoadingSpinner message="Generating your navigation plan..." />
        </HouseThemedCard>
      )}

      {plan && !loading && (
        <div className="space-y-6">
          {/* Plan Overview */}
          <HouseThemedCard>
            <div className="space-y-4">
              <div>
                <h3 className="text-xl font-semibold mb-2" style={{ color: colors.text }}>
                  Plan Overview
                </h3>
                <p className="text-gray-400">{plan.reasoning}</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Processing Time:</span>
                  <span className="ml-2" style={{ color: colors.text }}>
                    {formatProcessingTime(plan.processing_time_ms)}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Learning Applied:</span>
                  <span className="ml-2" style={{ color: colors.text }}>
                    {plan.learning_applied ? 'Yes' : 'No'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Adaptation Triggered:</span>
                  <span className="ml-2" style={{ color: colors.text }}>
                    {plan.adaptation_triggered ? 'Yes' : 'No'}
                  </span>
                </div>
              </div>
            </div>
          </HouseThemedCard>

          {/* Confidence Radar */}
          {Object.keys(plan.confidence_scores || {}).length > 0 && (
            <HouseThemedCard>
              <ConfidenceRadar plan={plan} />
            </HouseThemedCard>
          )}

          {/* Recommended Path */}
          {plan.recommended_path && (
            <HouseThemedCard>
              <NavigationPathChart path={plan.recommended_path} />
            </HouseThemedCard>
          )}

          {/* Alternative Paths */}
          {plan.paths.length > 1 && (
            <HouseThemedCard>
              <h3 className="text-xl font-semibold mb-4" style={{ color: colors.text }}>
                Alternative Paths ({plan.paths.length - 1})
              </h3>
              <div className="space-y-4">
                {plan.paths
                  .filter((p) => p.id !== plan.recommended_path?.id)
                  .map((path: NavigationPath) => (
                    <div key={path.id} className="border-t border-gray-700 pt-4">
                      <div className="mb-2">
                        <h4 className="font-semibold" style={{ color: colors.text }}>
                          {path.name}
                        </h4>
                        <p className="text-sm text-gray-400">{path.description}</p>
                      </div>
                      <div className="text-sm text-gray-400 space-y-1">
                        <p>
                          Time: {formatTime(path.estimated_total_time)} | Confidence:{' '}
                          {formatConfidence(path.confidence)} | Score:{' '}
                          {formatConfidence(path.recommendation_score)}
                        </p>
                        {path.reasoning && <p className="italic">{path.reasoning}</p>}
                      </div>
                      <div className="mt-2 space-y-1">
                        {path.steps.map((step: NavigationStep, index: number) => (
                          <div key={step.id} className="text-sm text-gray-300 pl-4">
                            {index + 1}. {step.name} ({formatTime(step.estimated_time_seconds)})
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
              </div>
            </HouseThemedCard>
          )}
        </div>
      )}
    </div>
  );
};

export default NavigationPlanView;
