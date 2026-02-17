import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { NavigationPath, NavigationStep } from '../../types';
import { useHouse } from '../../contexts';
import { formatTime, formatConfidence } from '../../utils';

interface NavigationPathChartProps {
  path: NavigationPath;
  className?: string;
}

export const NavigationPathChart: React.FC<NavigationPathChartProps> = ({
  path,
  className = '',
}) => {
  const { houseTheme } = useHouse();
  const { colors } = houseTheme;

  // Transform steps for chart display
  const chartData = path.steps.map((step: NavigationStep, index: number) => ({
    name: step.name.length > 20 ? `${step.name.substring(0, 20)}...` : step.name,
    fullName: step.name,
    time: step.estimated_time_seconds,
    confidence: Math.round(step.confidence * 100),
    step: index + 1,
  }));

  return (
    <div className={`w-full h-full ${className}`}>
      <h3 className="text-lg font-semibold mb-4" style={{ color: colors.text }}>
        Navigation Path: {path.name}
      </h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="name"
            angle={-45}
            textAnchor="end"
            height={100}
            stroke={colors.text}
            tick={{ fill: colors.text }}
          />
          <YAxis
            yAxisId="left"
            label={{ value: 'Time (seconds)', angle: -90, position: 'insideLeft' }}
            stroke={colors.text}
            tick={{ fill: colors.text }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            label={{ value: 'Confidence (%)', angle: 90, position: 'insideRight' }}
            stroke={colors.secondary}
            tick={{ fill: colors.secondary }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: `1px solid ${colors.border}`,
              borderRadius: '8px',
            }}
            labelStyle={{ color: colors.text }}
          />
          <Legend wrapperStyle={{ color: colors.text }} />
          <Bar
            yAxisId="left"
            dataKey="time"
            fill={colors.primary}
            name="Estimated Time (s)"
            radius={[8, 8, 0, 0]}
          />
          <Bar
            yAxisId="right"
            dataKey="confidence"
            fill={colors.secondary}
            name="Confidence (%)"
            radius={[8, 8, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-4 text-sm text-gray-400">
        <p>Total Estimated Time: {formatTime(path.estimated_total_time)}</p>
        <p>Overall Confidence: {formatConfidence(path.confidence)}</p>
      </div>
    </div>
  );
};

export default NavigationPathChart;
