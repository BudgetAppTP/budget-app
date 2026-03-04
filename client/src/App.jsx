import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Expenses from "./pages/Expenses";
import Incomes from "./pages/Incomes";
import Budgets from "./pages/Budgets";
import Savings from "./pages/Savings";
import Needs from "./pages/Needs";
import Ekasa from "./pages/EKasa";
import Comparison from "./pages/Comparison";
import Organisation from "./pages/Organisation";
import Login from "./pages/Login";
import Signin from "./pages/Signin";

import { LanguageProvider } from "./i18n/LanguageContext";

export default function App() {
  return (
    <LanguageProvider>
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/expenses" element={<Expenses/>} />
        <Route path="/incomes" element={<Incomes/>} />
        <Route path="/budgets" element={<Budgets/>} />
        <Route path="/savings" element={<Savings/>} />
        <Route path="/needs" element={<Needs/>} />
        <Route path="/organisation" element={<Organisation/>} />
        <Route path="/Ekasa" element={<Ekasa/>} />
        <Route path="/comparison" element={<Comparison/>} />
        <Route path="/login" element={<Login/>} />
        <Route path="/signin" element={<Signin/>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
    </LanguageProvider>
  );
}
