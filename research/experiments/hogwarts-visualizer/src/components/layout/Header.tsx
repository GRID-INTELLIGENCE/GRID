import React from 'react';
import { useHouse } from '../../contexts/HouseContext';
import { ALL_HOUSES, HOUSE_NAMES } from '../../types/house';
import { useAuth } from '../../contexts';

export const Header: React.FC = () => {
  const { activeHouse, setActiveHouse, houseTheme } = useHouse();
  const { user, logout } = useAuth();

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

        <div className="flex items-center space-x-6">
          {user && (
            <div className="hidden lg:flex items-center space-x-2 mr-4">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-xs font-bold text-white uppercase">
                {user.email?.substring(0, 1) || 'W'}
              </div>
              <span className="text-sm font-medium text-gray-300">
                {user.email}
              </span>
            </div>
          )}

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
                '--tw-ring-color': houseTheme.colors.primary,
              } as React.CSSProperties}
            >
              {ALL_HOUSES.map((house) => (
                <option key={house} value={house}>
                  {HOUSE_NAMES[house]}
                </option>
              ))}
            </select>
          </nav>

          <button
            onClick={logout}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-bold text-white/70 hover:text-white hover:bg-white/10 transition-all border border-white/10"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span>Depart</span>
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
