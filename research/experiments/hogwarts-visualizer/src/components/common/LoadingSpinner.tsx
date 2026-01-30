import React from 'react';
import { useHouse } from '../../contexts/HouseContext';

interface LoadingSpinnerProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading...',
  size = 'md',
}) => {
  const { houseTheme } = useHouse();
  const { colors } = houseTheme;

  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div className="flex flex-col items-center justify-center p-8">
      <div
        className={`${sizeClasses[size]} border-4 rounded-full animate-spin`}
        style={{
          borderColor: `${colors.primary}20`,
          borderTopColor: colors.primary,
        }}
      />
      {message && (
        <p className="mt-4 text-sm" style={{ color: colors.text }}>
          {message}
        </p>
      )}
    </div>
  );
};

export default LoadingSpinner;
