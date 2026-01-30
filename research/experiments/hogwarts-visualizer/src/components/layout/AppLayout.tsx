import React, { ReactNode } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

interface AppLayoutProps {
  children: ReactNode;
  currentView?: string;
  onViewChange?: (view: string) => void;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  children,
  currentView = 'dashboard',
  onViewChange,
}) => {
  const [localView, setLocalView] = React.useState<string>(currentView);

  const handleViewChange = (view: string) => {
    setLocalView(view);
    onViewChange?.(view);
  };

  const activeView = currentView || localView;

  return (
    <div className="min-h-screen bg-gray-900">
      <Header />
      <div className="flex">
        <Sidebar currentView={activeView} onViewChange={handleViewChange} />
        <main className="flex-1 p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
