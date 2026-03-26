import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import AmbientBackground from './ui/components/AmbientBackground';
import Dashboard from './pages/Dashboard';
import Library from './pages/Library';
import QueryInterface from './pages/QueryInterface';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';

export default function App() {
  return (
    <>
      {/* Full-page ambient background — sits behind everything */}
      <AmbientBackground />

      <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
        {/* Fixed sidebar */}
        <Sidebar />

        {/* Main content column */}
        <div style={{
          flex: 1, minWidth: 0,
          display: 'flex', flexDirection: 'column',
          overflow: 'hidden',
        }}>
          {/* Sticky top bar */}
          <TopBar />

          {/* Page content */}
          <div
            className="scroll-area"
            style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden' }}
          >
            <Routes>
              <Route path="/"          element={<Dashboard />} />
              <Route path="/library"   element={<Library />} />
              <Route path="/query"     element={<QueryInterface />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/settings"  element={<Settings />} />
            </Routes>
          </div>
        </div>
      </div>
    </>
  );
}
