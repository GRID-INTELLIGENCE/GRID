/**
 * House type definitions and constants for Hogwarts Visualizer.
 */

export type House = 'gryffindor' | 'slytherin' | 'hufflepuff' | 'ravenclaw';

export interface HouseColors {
  primary: string;
  secondary: string;
  accent: string;
  text: string;
  border: string;
}

export interface HouseTheme {
  house: House;
  colors: HouseColors;
  name: string;
  description: string;
}

export const HOUSE_COLORS: Record<House, HouseColors> = {
  gryffindor: {
    primary: '#ae0001',
    secondary: '#d3a625',
    accent: '#740001',
    text: '#d3a625',
    border: '#ae0001',
  },
  slytherin: {
    primary: '#2a623d',
    secondary: '#5d5d5d',
    accent: '#1a472a',
    text: '#aaaaaa',
    border: '#2a623d',
  },
  hufflepuff: {
    primary: '#ecb939',
    secondary: '#000000',
    accent: '#372e29',
    text: '#372e29',
    border: '#ecb939',
  },
  ravenclaw: {
    primary: '#0e4a99',
    secondary: '#946b2d',
    accent: '#222f5b',
    text: '#946b2d',
    border: '#0e4a99',
  },
};

export const HOUSE_NAMES: Record<House, string> = {
  gryffindor: 'Gryffindor',
  slytherin: 'Slytherin',
  hufflepuff: 'Hufflepuff',
  ravenclaw: 'Ravenclaw',
};

export const HOUSE_DESCRIPTIONS: Record<House, string> = {
  gryffindor: 'Bravery, courage, chivalry',
  slytherin: 'Ambition, cunning, resourcefulness',
  hufflepuff: 'Loyalty, patience, hard work',
  ravenclaw: 'Intelligence, wisdom, creativity',
};

export const HOUSE_THEMES: Record<House, HouseTheme> = {
  gryffindor: {
    house: 'gryffindor',
    colors: HOUSE_COLORS.gryffindor,
    name: HOUSE_NAMES.gryffindor,
    description: HOUSE_DESCRIPTIONS.gryffindor,
  },
  slytherin: {
    house: 'slytherin',
    colors: HOUSE_COLORS.slytherin,
    name: HOUSE_NAMES.slytherin,
    description: HOUSE_DESCRIPTIONS.slytherin,
  },
  hufflepuff: {
    house: 'hufflepuff',
    colors: HOUSE_COLORS.hufflepuff,
    name: HOUSE_NAMES.hufflepuff,
    description: HOUSE_DESCRIPTIONS.hufflepuff,
  },
  ravenclaw: {
    house: 'ravenclaw',
    colors: HOUSE_COLORS.ravenclaw,
    name: HOUSE_NAMES.ravenclaw,
    description: HOUSE_DESCRIPTIONS.ravenclaw,
  },
};

export const ALL_HOUSES: House[] = ['gryffindor', 'slytherin', 'hufflepuff', 'ravenclaw'];
