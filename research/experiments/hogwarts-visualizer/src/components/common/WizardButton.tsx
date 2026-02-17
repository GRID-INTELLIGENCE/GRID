import React, { ButtonHTMLAttributes, ReactNode } from 'react';
import { useHouse } from '../../contexts/HouseContext';

interface WizardButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
}

export const WizardButton: React.FC<WizardButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  disabled,
  ...props
}) => {
  const { houseTheme } = useHouse();
  const { colors } = houseTheme;

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  const variantClasses = {
    primary: `bg-[${colors.primary}] hover:opacity-90 text-white`,
    secondary: `bg-[${colors.secondary}] hover:opacity-90 text-gray-900`,
    outline: `border-2 border-[${colors.border}] hover:bg-[${colors.primary}]/20 text-[${colors.text}]`,
  };

  return (
    <button
      className={`
        ${sizeClasses[size]}
        ${variantClasses[variant]}
        rounded-lg font-medium
        transition-all duration-200
        disabled:opacity-50 disabled:cursor-not-allowed
        focus:outline-none focus:ring-2 focus:ring-offset-2
        ${className}
      `}
      style={{
        ...(variant === 'primary' && { backgroundColor: colors.primary }),
        ...(variant === 'secondary' && { backgroundColor: colors.secondary }),
        ...(variant === 'outline' && {
          borderColor: colors.border,
          color: colors.text,
        }),
        ...(variant === 'outline' && {
          '--focus-ring-color': colors.primary,
        } as React.CSSProperties),
      }}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};

export default WizardButton;
