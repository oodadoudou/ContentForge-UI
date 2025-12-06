import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './layouts/AppLayout';
import { Dashboard } from './pages/Dashboard';
import { ConfigProvider, theme } from 'antd';
import useWebSocket from 'react-use-websocket';
import { WS_URL } from './api/config';
import { useStore } from './store/useStore';

import { Downloaders } from './pages/Downloaders';
import { SettingsPage } from './pages/Settings';
import { ComicProcessing } from './pages/ComicProcessing';
import { EbookWorkshop } from './pages/EbookWorkshop';
import { FileOrganization } from './pages/FileOrganization';

const App: React.FC = () => {
  const addLog = useStore((state) => state.addLog);

  // WebSocket Setup
  const { lastMessage } = useWebSocket(WS_URL, {
    onOpen: () => addLog('[SYSTEM] Connected to Backend'),
    onClose: () => addLog('[SYSTEM] Disconnected from Backend'),
    shouldReconnect: () => true,
  });

  useEffect(() => {
    if (lastMessage !== null) {
      addLog(lastMessage.data);
    }
  }, [lastMessage, addLog]);

  return (
    <ConfigProvider theme={{ algorithm: theme.darkAlgorithm }}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="comic" element={<ComicProcessing />} />
            <Route path="ebook" element={<EbookWorkshop />} />
            <Route path="org" element={<FileOrganization />} />
            <Route path="downloaders" element={<Downloaders />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
