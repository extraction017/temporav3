import React from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.jsx';  // Updated to .jsx and named import style (optional, but matches Vite default)

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);