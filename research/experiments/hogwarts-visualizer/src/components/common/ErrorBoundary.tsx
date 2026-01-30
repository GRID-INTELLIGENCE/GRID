import React, { Component, ErrorInfo, ReactNode } from 'react';
import { HouseThemedCard } from './HouseThemedCard';
import { WizardButton } from './WizardButton';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-6 bg-gray-900">
          <HouseThemedCard className="max-w-md w-full">
            <div className="space-y-4">
              <h2 className="text-2xl font-bold text-red-500">Something went wrong</h2>
              <p className="text-gray-400">
                {this.state.error?.message || 'An unexpected error occurred'}
              </p>
              <WizardButton
                onClick={() => {
                  this.setState({ hasError: false, error: null });
                  window.location.reload();
                }}
              >
                Reload Page
              </WizardButton>
            </div>
          </HouseThemedCard>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
