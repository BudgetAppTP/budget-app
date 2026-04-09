import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Expenses from "./pages/Expenses";
import Incomes from "./pages/Incomes";
import Budgets from "./pages/Budgets";
import Savings from "./pages/Savings";
import Needs from "./pages/Needs";
import Ekasa from "./pages/Ekasa";
import Comparison from "./pages/Comparison";
import Organisation from "./pages/Organisation";
import Login from "./pages/Login";
import Signin from "./pages/Signin";

import { LanguageProvider } from "./i18n/LanguageContext";
import { AuthProvider } from "./auth/AuthContext";
import { ProtectedRoute, PublicOnlyRoute } from "./auth/RouteGuards";

export default function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/expenses" element={<ProtectedRoute><Expenses /></ProtectedRoute>} />
            <Route path="/incomes" element={<ProtectedRoute><Incomes /></ProtectedRoute>} />
            <Route path="/budgets" element={<ProtectedRoute><Budgets /></ProtectedRoute>} />
            <Route path="/savings" element={<ProtectedRoute><Savings /></ProtectedRoute>} />
            <Route path="/needs" element={<ProtectedRoute><Needs /></ProtectedRoute>} />
            <Route path="/organisation" element={<ProtectedRoute><Organisation /></ProtectedRoute>} />
            <Route path="/Ekasa" element={<ProtectedRoute><Ekasa /></ProtectedRoute>} />
            <Route path="/comparison" element={<ProtectedRoute><Comparison /></ProtectedRoute>} />
            <Route path="/login" element={<PublicOnlyRoute><Login /></PublicOnlyRoute>} />
            <Route path="/signin" element={<PublicOnlyRoute><Signin /></PublicOnlyRoute>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </AuthProvider>
    </LanguageProvider>
  );
}
