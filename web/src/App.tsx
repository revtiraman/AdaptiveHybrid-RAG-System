import React, { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Library from './pages/Library';
import QueryInterface from './pages/QueryInterface';
import Settings from './pages/Settings';

export default function App() {
  const [uploadModalOpen, setUploadModalOpen] = useState(false);

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: 'var(--bg-base)' }}>
      {/* Fixed left sidebar */}
      <Sidebar
        uploadModalOpen={uploadModalOpen}
        setUploadModalOpen={setUploadModalOpen}
      />

      {/* Main content */}
      <div
        className="scroll-area"
        style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column', minWidth: 0 }}
      >
        <Routes>
          <Route path="/" element={<Dashboard onUploadClick={() => setUploadModalOpen(true)} />} />
          <Route
            path="/library"
            element={
              <Library
                uploadModalOpen={uploadModalOpen}
                setUploadModalOpen={setUploadModalOpen}
              />
            }
          />
          <Route path="/query" element={<QueryInterface />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </div>
    </div>
  );
}
