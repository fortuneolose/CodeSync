import { useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import Header from "./components/Header";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import EditorPage from "./pages/EditorPage";
import { useAuthStore } from "./store/authStore";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuthStore();
  const location = useLocation();
  if (loading) return null;
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  return <>{children}</>;
}

function Layout({ children, theme, onToggleTheme }: {
  children: React.ReactNode;
  theme: "vs-dark" | "vs";
  onToggleTheme: () => void;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <Header theme={theme} onToggleTheme={onToggleTheme} />
      <main style={{ flex: 1, overflow: "auto", minHeight: 0, display: "flex", flexDirection: "column" }}>
        {children}
      </main>
    </div>
  );
}

export default function App() {
  const [theme, setTheme] = useState<"vs-dark" | "vs">("vs-dark");
  const { hydrate } = useAuthStore();

  useEffect(() => { hydrate(); }, []);

  const toggleTheme = () => setTheme((t) => (t === "vs-dark" ? "vs" : "vs-dark"));

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/" element={
          <RequireAuth>
            <Layout theme={theme} onToggleTheme={toggleTheme}>
              <DashboardPage />
            </Layout>
          </RequireAuth>
        } />
        <Route path="/editor/:slug" element={
          <RequireAuth>
            <Layout theme={theme} onToggleTheme={toggleTheme}>
              <EditorPage theme={theme} />
            </Layout>
          </RequireAuth>
        } />
      </Routes>
    </BrowserRouter>
  );
}
