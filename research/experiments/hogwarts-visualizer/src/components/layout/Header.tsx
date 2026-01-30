import React from 'react';
import { useHouse, ALL_HOUSES, HOUSE_NAMES } from '../../contexts/HouseContext';

export const Header: React.FC = () => {
  const { activeHouse, setActiveHouse, houseTheme } = useHouse();

  return (
    <header
      className="sticky top-0 z-50 w-full border-b-2 backdrop-blur-md bg-gray-900/80"
      style={{ borderColor: houseTheme.colors.border }}
    >
      <div className="container mx-auto px-4 py-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold" style={{ color: houseTheme.colors.primary }}>
            Hogwarts Visualizer
          </h1>
          <span className="text-sm text-gray-400">Path Optimization</span>
        </div>

        <nav className="flex items-center space-x-2">
          <label className="text-sm font-medium mr-2" style={{ color: houseTheme.colors.text }}>
            House:
          </label>
          <select
            value={activeHouse}
            onChange={(e) => setActiveHouse(e.target.value as typeof activeHouse)}
            className="px-3 py-1.5 rounded-lg bg-gray-800 border text-gray-100 focus:outline-none focus:ring-2"
            style={{
              borderColor: houseTheme.colors.border,
              '--focus-ring-color': houseTheme.colors.primary,
            } as React.CSSProperties}
          >
            {ALL_HOUSES.map((house) => (
              <option key={house} value={house}>
                {HOUSE_NAMES[house]}
              </option>
            ))}
          </select>
        </nav>
      </div>
    </header>
  );
};

export default Header;
