import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import Dashboard from "./pages/Dashboard";
import Appointments from "./pages/Appointments";
import Clients from "./pages/Clients";
import ExtensionLeads from "./pages/ExtensionLeads";
import Inventory from "./pages/Inventory";
import Chat from "./pages/Chat";
import Aftercare from "./pages/Aftercare";
import Reports from "./pages/Reports";

export default function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/appointments" element={<Appointments />} />
          <Route path="/clients" element={<Clients />} />
          <Route path="/leads" element={<ExtensionLeads />} />
          <Route path="/inventory" element={<Inventory />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/aftercare" element={<Aftercare />} />
          <Route path="/reports" element={<Reports />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
}
