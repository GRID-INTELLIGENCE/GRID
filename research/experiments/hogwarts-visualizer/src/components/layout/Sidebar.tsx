import React from 'react';
import { useHouse } from '../../contexts/HouseContext';
import { HOUSE_NAMES } from '../../types/house';

interface SidebarProps {
  currentView?: string;
  onViewChange?: (view: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentView, onViewChange }) => {
  const { houseTheme } = useHouse();
  const { colors } = houseTheme;

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '🏠' },
    { id: 'navigation', label: 'Navigation Plans', icon: '🧭' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
  ];

  return (
    <aside
      className="hidden md:block w-64 min-h-screen border-r-2 bg-gray-900/50 backdrop-blur-sm"
      style={{ borderColor: colors.border }}
    >
      <div className="p-4">
        <div className="mb-6">
          <h2 className="text-lg font-semibold" style={{ color: colors.primary }}>
            {HOUSE_NAMES[houseTheme.house]} Common Room
          </h2>
          <p className="text-xs text-gray-400 mt-1">{houseTheme.description}</p>
        </div>

        <nav className="space-y-2">
          {menuItems.map((item) => {
            const isActive = currentView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onViewChange?.(item.id)}
                className={`
                  w-full text-left px-4 py-2 rounded-lg
                  transition-all duration-200
                  ${isActive ? 'font-semibold' : 'hover:bg-gray-800/50'}
                `}
                style={{
                  backgroundColor: isActive ? `${colors.primary}20` : 'transparent',
                  color: isActive ? colors.text : 'inherit',
                  borderLeft: isActive ? `3px solid ${colors.primary}` : 'none',
                }}
              >
                <span className="mr-2">{item.icon}</span>
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>
    </aside>
  );
};

export default Sidebar;
