import React, { useState } from 'react';
import { HouseProvider, ThemeProvider } from './contexts';
import { ErrorBoundary, AppLayout } from './components';
import { Dashboard, NavigationPlanView, Settings } from './views';
import './styles/globals.css';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<string>('dashboard');

  const renderView = () => {
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
    <ErrorBoundary>
      <HouseProvider defaultHouse="gryffindor">
        <ThemeProvider>
          <AppLayout currentView={currentView} onViewChange={setCurrentView}>
            {renderView()}
          </AppLayout>
        </ThemeProvider>
      </HouseProvider>
    </ErrorBoundary>
  );
};

export default App;
