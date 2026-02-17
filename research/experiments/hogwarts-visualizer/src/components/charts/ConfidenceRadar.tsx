import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { NavigationPlan } from '../../types';
import { useHouse } from '../../contexts';
import { formatProcessingTime } from '../../utils';

interface ConfidenceRadarProps {
  plan: NavigationPlan;
  className?: string;
}

export const ConfidenceRadar: React.FC<ConfidenceRadarProps> = ({
  plan,
  className = '',
}) => {
  const { houseTheme } = useHouse();
  const { colors } = houseTheme;

  // Transform confidence scores for radar chart
  const radarData = Object.entries(plan.confidence_scores || {}).map(([key, value]) => ({
    metric: key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
    value: Math.round(value * 100),
    fullMark: 100,
  }));

  // Add overall confidence if not present
  if (!radarData.find((d) => d.metric === 'Overall')) {
    radarData.push({
      metric: 'Overall',
      value: Math.round((plan.recommended_path?.confidence || 0) * 100),
      fullMark: 100,
    });
  }

  return (
    <div className={`w-full h-full ${className}`}>
      <h3 className="text-lg font-semibold mb-4" style={{ color: colors.text }}>
        Confidence Metrics
      </h3>
      <ResponsiveContainer width="100%" height={400}>
        <RadarChart data={radarData}>
          <PolarGrid stroke="#374151" />
          <PolarAngleAxis
            dataKey="metric"
            tick={{ fill: colors.text, fontSize: 12 }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fill: colors.text, fontSize: 10 }}
          />
          <Radar
            name="Confidence"
            dataKey="value"
            stroke={colors.primary}
            fill={colors.primary}
            fillOpacity={0.6}
          />
          <Legend wrapperStyle={{ color: colors.text }} />
        </RadarChart>
      </ResponsiveContainer>
      <div className="mt-4 text-sm text-gray-400">
        <p>Request ID: {plan.request_id}</p>
        <p>Processing Time: {formatProcessingTime(plan.processing_time_ms)}</p>
      </div>
    </div>
  );
};

export default ConfidenceRadar;
