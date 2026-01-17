import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';

const pageTitles: Record<string, string> = {
  '/valuations': 'Valuations',
  '/valuations/new': 'New Valuation',
};

export function Layout() {
  const location = useLocation();

  // Get page title from path, handling dynamic routes
  const getPageTitle = () => {
    if (location.pathname.match(/^\/valuations\/[a-f0-9-]+$/i)) {
      return 'Valuation Details';
    }
    return pageTitles[location.pathname] || 'VC Audit Tool';
  };

  return (
    <div className="flex h-screen bg-neutral-50">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-neutral-200 shadow-sm px-8 py-4">
          <h1 className="text-2xl font-bold text-default-font">{getPageTitle()}</h1>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-auto p-8">
          <div className="max-w-6xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
