import React, { createContext, useContext, useState, ReactNode } from 'react';
import { House, HOUSE_THEMES } from '../types/house';

interface HouseContextType {
  activeHouse: House;
  setActiveHouse: (house: House) => void;
  houseTheme: typeof HOUSE_THEMES[keyof typeof HOUSE_THEMES];
}

const HouseContext = createContext<HouseContextType | undefined>(undefined);

interface HouseProviderProps {
  children: ReactNode;
  defaultHouse?: House;
}

export const HouseProvider: React.FC<HouseProviderProps> = ({
  children,
  defaultHouse = 'gryffindor',
}) => {
  const [activeHouse, setActiveHouse] = useState<House>(defaultHouse);

  const houseTheme = HOUSE_THEMES[activeHouse];

  return (
    <HouseContext.Provider value={{ activeHouse, setActiveHouse, houseTheme }}>
      {children}
    </HouseContext.Provider>
  );
};

export const useHouse = (): HouseContextType => {
  const context = useContext(HouseContext);
  if (!context) {
    throw new Error('useHouse must be used within a HouseProvider');
  }
  return context;
};
