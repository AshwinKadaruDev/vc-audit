import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { ValuationsListPage } from './pages/ValuationsListPage';
import { ValuationDetailPage } from './pages/ValuationDetailPage';
import { NewValuationPage } from './pages/NewValuationPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/valuations" replace />} />
        <Route element={<Layout />}>
          <Route path="/valuations" element={<ValuationsListPage />} />
          <Route path="/valuations/new" element={<NewValuationPage />} />
          <Route path="/valuations/:id" element={<ValuationDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
