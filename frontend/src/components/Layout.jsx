import React from "react";
import { Header } from "./Header";
export const Layout = ({ children, title, className, noHeader }) => {
  return (
    <div className="w-screen min-h-screen flex flex-col">
      {!noHeader && <Header />}
      <main
        className={`flex flex-col items-center justify-center p-8 ${className}`}
      >
        <h1 className="text-3xl font-bold mb-4">{title}</h1>
        {children}
      </main>
    </div>
  );
};
