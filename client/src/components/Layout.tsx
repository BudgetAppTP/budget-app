import React from "react";
import Navbar from "./Navbar";

type Props = { children: React.ReactNode };

export default function Layout({ children }: Props) {
  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Navbar />
      <main style={{ flex: 1, padding: "16px" }}>{children}</main>
    </div>
  );
}
