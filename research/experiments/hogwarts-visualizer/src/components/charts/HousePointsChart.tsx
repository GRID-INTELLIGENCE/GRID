import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { useHouse } from '../../contexts/HouseContext';
import { ALL_HOUSES, HOUSE_NAMES } from '../../types/house';

interface HousePointsChartProps {
  className?: string;
  data?: Record<string, number>;
}

// Mock house points data - can be replaced with real data later
const defaultHousePoints: Record<string, number> = {
  gryffindor: 350,
  slytherin: 380,
  hufflepuff: 290,
  ravenclaw: 340,
};

export const HousePointsChart: React.FC<HousePointsChartProps> = ({
  className = '',
  data = defaultHousePoints,
}) => {
  const { houseTheme } = useHouse();
  const { colors } = houseTheme;

  // Transform data for chart
  const chartData = ALL_HOUSES.map((house) => ({
    house: HOUSE_NAMES[house],
    points: data[house] || 0,
    isActive: houseTheme.house === house,
  }));

  // Sort by points descending
  chartData.sort((a, b) => b.points - a.points);

  return (
    <div className={`w-full h-full ${className}`}>
      <h3 className="text-lg font-semibold mb-4" style={{ color: colors.text }}>
        House Points Leaderboard
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="house"
            stroke={colors.text}
            tick={{ fill: colors.text }}
          />
          <YAxis
            label={{ value: 'Points', angle: -90, position: 'insideLeft' }}
            stroke={colors.text}
            tick={{ fill: colors.text }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: `1px solid ${colors.border}`,
              borderRadius: '8px',
            }}
            labelStyle={{ color: colors.text }}
          />
          <Bar dataKey="points" radius={[8, 8, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.isActive ? colors.primary : colors.secondary}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default HousePointsChart;
