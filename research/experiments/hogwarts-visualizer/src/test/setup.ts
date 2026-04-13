/**
 * Vitest setup file
 */
import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

// Node 22+ exposes its own localStorage global backed by --localstorage-file.
// When no valid file path is provided the object exists but getItem/setItem are
// non-functions, breaking any component that calls localStorage in useEffect.
// Override with an in-memory implementation so tests run cleanly in jsdom.
const _localStorageStore: Record<string, string> = {};
Object.defineProperty(globalThis, 'localStorage', {
  value: {
    getItem: (key: string): string | null => _localStorageStore[key] ?? null,
    setItem: (key: string, value: string): void => { _localStorageStore[key] = value; },
    removeItem: (key: string): void => { delete _localStorageStore[key]; },
    clear: (): void => { Object.keys(_localStorageStore).forEach((k) => delete _localStorageStore[k]); },
    get length(): number { return Object.keys(_localStorageStore).length; },
    key: (index: number): string | null => Object.keys(_localStorageStore)[index] ?? null,
  } satisfies Storage,
  writable: true,
  configurable: true,
});

// Cleanup after each test
afterEach(() => {
  cleanup();
});
