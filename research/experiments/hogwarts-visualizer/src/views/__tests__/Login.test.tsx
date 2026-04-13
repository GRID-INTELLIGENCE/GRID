import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { AuthProvider } from '../../contexts/AuthContext';
import { HouseProvider } from '../../contexts/HouseContext';
import { Login } from '../Login';

vi.mock('../../services/api/auth', () => ({
  authService: {
    validate: vi.fn().mockResolvedValue({ success: false, data: { valid: false } }),
    login: vi.fn(),
    logout: vi.fn(),
  },
}));

describe('Login View', () => {
  it('renders login form correctly', () => {
    render(
      <HouseProvider>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </HouseProvider>
    );

    expect(screen.getByText('Hogwarts Registry')).toBeInTheDocument();
    expect(screen.getByLabelText('Wizard Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Secret Incantation')).toBeInTheDocument();
  });
});
