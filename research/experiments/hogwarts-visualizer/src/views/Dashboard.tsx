import React from 'react';
import { HouseThemedCard } from '../components';
import { HousePointsChart } from '../components/charts';
import { useHouse } from '../contexts';

export const Dashboard: React.FC = () => {
  const { houseTheme } = useHouse();
  const { colors } = houseTheme;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="mb-6">
        <h2 className="text-3xl font-bold mb-2" style={{ color: colors.primary }}>
          Welcome to {houseTheme.name} Common Room
        </h2>
        <p className="text-gray-400">{houseTheme.description}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <HouseThemedCard>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold" style={{ color: colors.text }}>
              Navigation Plans
            </h3>
            <p className="text-gray-400 text-sm">
              Create and view your path optimization plans
            </p>
            <div className="text-2xl font-bold" style={{ color: colors.primary }}>
              0
            </div>
          </div>
        </HouseThemedCard>

        <HouseThemedCard>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold" style={{ color: colors.text }}>
              Success Rate
            </h3>
            <p className="text-gray-400 text-sm">Overall plan success rate</p>
            <div className="text-2xl font-bold" style={{ color: colors.secondary }}>
              --
            </div>
          </div>
        </HouseThemedCard>

        <HouseThemedCard>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold" style={{ color: colors.text }}>
              Total Time Saved
            </h3>
            <p className="text-gray-400 text-sm">Estimated time saved through optimization</p>
            <div className="text-2xl font-bold" style={{ color: colors.primary }}>
              --
            </div>
          </div>
        </HouseThemedCard>
      </div>

      <HouseThemedCard className="mt-6">
        <HousePointsChart />
      </HouseThemedCard>
    </div>
  );
};

export default Dashboard;
