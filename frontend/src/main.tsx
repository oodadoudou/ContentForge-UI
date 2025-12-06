import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import 'antd/dist/reset.css'; // or just rely on ConfigProvider? AntD v5 handles styles automatically. But reset.css is good.
// Actually AntD v5 doesn't need dist/antd.css, but reset might be useful.
// Let's just import App.

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
