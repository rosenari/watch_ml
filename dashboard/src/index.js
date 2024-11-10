import React from 'react';
import ReactDOM from 'react-dom/client';
import Dashboard from './Dashboard';
import { BrowserRouter as Router } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';

const queryClient = new QueryClient();

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <QueryClientProvider client={queryClient}>
    <Router>
      <Dashboard />
    </Router>
  </QueryClientProvider>
);