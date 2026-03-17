import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { LanguageProvider } from "./i18n/LanguageContext";
import {GoogleOAuthProvider} from "@react-oauth/google";

const root = document.getElementById("root");
const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;
createRoot(root).render(
  <GoogleOAuthProvider clientId={CLIENT_ID}>
    <LanguageProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </LanguageProvider>
  </GoogleOAuthProvider>
);