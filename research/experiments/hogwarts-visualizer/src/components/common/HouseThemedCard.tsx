import React, { ReactNode } from 'react';
import { useHouse } from '../../contexts/HouseContext';

interface HouseThemedCardProps {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}

export const HouseThemedCard: React.FC<HouseThemedCardProps> = ({
  children,
  className = '',
  onClick,
}) => {
  const { houseTheme } = useHouse();
  const { colors } = houseTheme;

  const baseClasses = `
    rounded-lg p-4 transition-house
    border-2
    bg-gray-800/50 backdrop-blur-sm
    ${onClick ? 'cursor-pointer hover:bg-gray-800/70' : ''}
    ${className}
  `;


  return (
    <div
      className={baseClasses}
      style={{
        borderColor: colors.border,
        color: colors.text,
      }}
      onClick={onClick}
      onKeyDown={(e) => {
        if (onClick && (e.key === 'Enter' || e.key === ' ')) {
          onClick();
        }
      }}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {children}
    </div>
  );
};

export default HouseThemedCard;
