//F:\nodebase_final_pro\src\app\(dashboard)\(rest)\layout.tsx
import { AppHeader } from "@/components/app-header";
import React from "react";

const Layout = ({ children }: { children: React.ReactNode }) => {
  return (
    <>
    <AppHeader/>
      <main className="flex-1">{children}</main>
    </>
  );
};

export default Layout;
