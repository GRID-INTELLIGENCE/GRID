import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Login } from '../Login';
import { AuthProvider } from '../../contexts/AuthContext';
import { HouseProvider } from '../../contexts/HouseContext';

// Mock the auth service
// Mock the auth service

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
