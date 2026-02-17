import React, { useState } from 'react';
import { HouseThemedCard, WizardButton, SpellboundInput } from '../components';
import { useHouse, useTheme } from '../contexts';
import { ALL_HOUSES, HOUSE_NAMES } from '../types';

export const Settings: React.FC = () => {
  const { activeHouse, setActiveHouse, houseTheme } = useHouse();
  const { darkMode, setDarkMode } = useTheme();
  const { colors } = houseTheme;

  const [apiBaseUrl, setApiBaseUrl] = useState<string>(
    import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'
  );

  const handleSaveSettings = () => {
    // Save settings to localStorage or backend (for Phase 4)
    localStorage.setItem('apiBaseUrl', apiBaseUrl);
    alert('Settings saved! (Note: API URL changes require app restart)');
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="mb-6">
        <h2 className="text-3xl font-bold mb-2" style={{ color: colors.primary }}>
          Settings
        </h2>
        <p className="text-gray-400">Configure your preferences</p>
      </div>

      {/* House Selection */}
      <HouseThemedCard>
        <h3 className="text-lg font-semibold mb-4" style={{ color: colors.text }}>
          House Selection
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: colors.text }}>
              Active House
            </label>
            <select
              value={activeHouse}
              onChange={(e) => setActiveHouse(e.target.value as typeof activeHouse)}
              className="w-full px-4 py-2 rounded-lg bg-gray-800 border text-gray-100 focus:outline-none focus:ring-2"
              style={{
                borderColor: colors.border,
                '--focus-ring-color': colors.primary,
              } as React.CSSProperties}
            >
              {ALL_HOUSES.map((house) => (
                <option key={house} value={house}>
                  {HOUSE_NAMES[house]}
                </option>
              ))}
            </select>
            <p className="mt-2 text-sm text-gray-400">{houseTheme.description}</p>
          </div>
        </div>
      </HouseThemedCard>

      {/* Theme Settings */}
      <HouseThemedCard>
        <h3 className="text-lg font-semibold mb-4" style={{ color: colors.text }}>
          Theme Settings
        </h3>
        <div className="space-y-4">
          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={darkMode}
              onChange={(e) => setDarkMode(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm" style={{ color: colors.text }}>
              Dark Mode
            </span>
          </label>
        </div>
      </HouseThemedCard>

      {/* API Configuration */}
      <HouseThemedCard>
        <h3 className="text-lg font-semibold mb-4" style={{ color: colors.text }}>
          API Configuration
        </h3>
        <div className="space-y-4">
          <SpellboundInput
            label="API Base URL"
            type="text"
            value={apiBaseUrl}
            onChange={(e) => setApiBaseUrl(e.target.value)}
            placeholder="http://localhost:8080"
          />
          <p className="text-sm text-gray-400">
            Current backend endpoint for API calls. Changes require app restart.
          </p>
          <WizardButton onClick={handleSaveSettings}>Save Settings</WizardButton>
        </div>
      </HouseThemedCard>

      {/* Info */}
      <HouseThemedCard>
        <h3 className="text-lg font-semibold mb-4" style={{ color: colors.text }}>
          Application Info
        </h3>
        <div className="space-y-2 text-sm text-gray-400">
          <p>Version: 0.1.0</p>
          <p>Environment: {import.meta.env.MODE}</p>
          <p>API URL: {import.meta.env.VITE_API_BASE_URL || 'Not configured'}</p>
        </div>
      </HouseThemedCard>
    </div>
  );
};

export default Settings;
