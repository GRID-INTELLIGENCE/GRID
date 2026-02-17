import React, { useState, useEffect } from 'react';
import { HouseProvider, ThemeProvider, AuthProvider, useAuth } from './contexts';
import { ErrorBoundary, AppLayout } from './components';
import { Dashboard, NavigationPlanView, Settings, Login } from './views';
import './styles/globals.css';

const AppContent: React.FC = () => {
  const [currentView, setCurrentView] = useState<string>('dashboard');
  const { isAuthenticated, loading } = useAuth();

  useEffect(() => {
    if (!isAuthenticated && !loading) {
      setCurrentView('login');
    } else if (isAuthenticated && currentView === 'login') {
      setCurrentView('dashboard');
    }
  }, [isAuthenticated, loading, currentView]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="relative w-24 h-24">
          <div className="absolute inset-0 border-4 border-white/20 rounded-full"></div>
          <div className="absolute inset-0 border-4 border-indigo-500 rounded-full border-t-transparent animate-spin"></div>
        </div>
      </div>
    );
  }

  const renderView = () => {
    if (!isAuthenticated) {
      return <Login />;
    }

    switch (currentView) {
      case 'dashboard':
        return <Dashboard />;
      case 'navigation':
        return <NavigationPlanView />;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <HouseProvider defaultHouse="gryffindor">
      <ThemeProvider>
        {isAuthenticated ? (
          <AppLayout currentView={currentView} onViewChange={setCurrentView}>
            {renderView()}
          </AppLayout>
        ) : (
          renderView()
        )}
      </ThemeProvider>
    </HouseProvider>
  );
};

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ErrorBoundary>
  );
};

export default App;
