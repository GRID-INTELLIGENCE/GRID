import React, { InputHTMLAttributes, forwardRef } from 'react';
import { useHouse } from '../../contexts/HouseContext';

interface SpellboundInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const SpellboundInput = forwardRef<HTMLInputElement, SpellboundInputProps>(
  ({ label, error, className = '', ...props }, ref) => {
    const { houseTheme } = useHouse();
    const { colors } = houseTheme;

    return (
      <div className="w-full">
        {label && (
          <label
            className="block text-sm font-medium mb-1.5"
            style={{ color: colors.text }}
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={`
            w-full px-4 py-2
            bg-gray-800/50 border-2 rounded-lg
            text-gray-100
            focus:outline-none focus:ring-2 focus:ring-offset-2
            transition-all duration-200
            ${error ? 'border-red-500' : ''}
            ${className}
          `}
          style={{
            borderColor: error ? '#ef4444' : colors.border,
            '--focus-ring-color': colors.primary,
          } as React.CSSProperties}
          {...props}
        />
        {error && (
          <p className="mt-1 text-sm text-red-500">{error}</p>
        )}
      </div>
    );
  }
);

SpellboundInput.displayName = 'SpellboundInput';

export default SpellboundInput;
