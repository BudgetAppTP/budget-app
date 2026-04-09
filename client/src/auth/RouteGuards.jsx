import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";

function AuthLoading() {
  return <div style={{ padding: "2rem", textAlign: "center" }}>Loading...</div>;
}

export function ProtectedRoute({ children }) {
  const { status } = useAuth();
  const location = useLocation();

  if (status === "loading") {
    return <AuthLoading />;
  }
  if (status !== "authenticated") {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return children;
}

export function PublicOnlyRoute({ children }) {
  const { status } = useAuth();

  if (status === "loading") {
    return <AuthLoading />;
  }
  if (status === "authenticated") {
    return <Navigate to="/" replace />;
  }
  return children;
}
