import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { LanguageProvider } from "./i18n/LanguageContext";

const root = document.getElementById("root");
createRoot(root).render(
    <LanguageProvider>
  <BrowserRouter>
    <App />
  </BrowserRouter>
   </LanguageProvider>
);
