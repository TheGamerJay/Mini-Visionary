import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import NavBar from "./components/NavBar";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import Library from "./pages/Library";
import CreatePoster from "./pages/CreatePoster";
import Wallet from "./pages/Wallet";
import Profile from "./pages/Profile";
import Store from "./pages/Store";
import Login from "./pages/Login";
import RegisterPage from "./pages/RegisterPage";
import ForgotPage from "./pages/ForgotPage";
import TermsOfService from "./pages/TermsOfService";
import PrivacyPolicy from "./pages/PrivacyPolicy";
import StoreSuccess from "./pages/StoreSuccess";
import CheckoutSuccess from "./pages/CheckoutSuccess";
import CheckoutCancel from "./pages/CheckoutCancel";
import Settings from "./pages/Settings";
import Chat from "./pages/Chat";

// Check if user is authenticated
function isAuthenticated(): boolean {
  const token = localStorage.getItem('jwt_token');
  return !!token;
}

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  return isAuthenticated() ? children : <Navigate to="/login" replace />;
}

// Auth route wrapper (redirect to dashboard if already logged in)
function AuthRoute({ children }: { children: React.ReactNode }) {
  return isAuthenticated() ? <Navigate to="/dashboard" replace /> : children;
}

export default function App(){
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes - Landing page is login */}
        <Route path="/" element={<AuthRoute><Login /></AuthRoute>} />

        {/* Auth routes (redirect if already logged in) */}
        <Route path="/login" element={<AuthRoute><Login /></AuthRoute>} />
        <Route path="/home" element={<ProtectedRoute><><NavBar /><main className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900"><div className="max-w-7xl mx-auto px-4 py-8 pt-20"><Home /></div></main></></ProtectedRoute>} />
        <Route path="/register" element={<AuthRoute><RegisterPage /></AuthRoute>} />
        <Route path="/forgot-password" element={<AuthRoute><ForgotPage /></AuthRoute>} />
        <Route path="/terms-of-service" element={<TermsOfService />} />
        <Route path="/privacy-policy" element={<PrivacyPolicy />} />

        {/* Protected routes (require authentication) */}
        <Route path="/dashboard" element={<ProtectedRoute><><NavBar /><main className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900"><div className="max-w-7xl mx-auto px-4 py-8 pt-20"><Dashboard /></div></main></></ProtectedRoute>} />
        <Route path="/library" element={<ProtectedRoute><><NavBar /><main className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900"><div className="max-w-7xl mx-auto px-4 py-8 pt-20"><Library /></div></main></></ProtectedRoute>} />
        <Route path="/create" element={<ProtectedRoute><><NavBar /><main className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900"><div className="max-w-7xl mx-auto px-4 py-8 pt-20"><CreatePoster /></div></main></></ProtectedRoute>} />
        <Route path="/wallet" element={<ProtectedRoute><><NavBar /><main className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900"><div className="max-w-7xl mx-auto px-4 py-8 pt-20"><Wallet /></div></main></></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute><><NavBar /><main className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900"><div className="max-w-7xl mx-auto px-4 py-8 pt-20"><Profile /></div></main></></ProtectedRoute>} />
        <Route path="/store" element={<ProtectedRoute><><NavBar /><main className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900"><div className="max-w-7xl mx-auto px-4 py-8 pt-20"><Store /></div></main></></ProtectedRoute>} />
        <Route path="/store/success" element={<ProtectedRoute><><NavBar /><main className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900"><div className="max-w-7xl mx-auto px-4 py-8 pt-20"><StoreSuccess /></div></main></></ProtectedRoute>} />
        <Route path="/checkout/success" element={<ProtectedRoute><><NavBar /><main className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900"><div className="max-w-7xl mx-auto px-4 py-8 pt-20"><CheckoutSuccess /></div></main></></ProtectedRoute>} />
        <Route path="/checkout/cancel" element={<ProtectedRoute><><NavBar /><main className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900"><div className="max-w-7xl mx-auto px-4 py-8 pt-20"><CheckoutCancel /></div></main></></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><><NavBar /><main className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900"><div className="max-w-7xl mx-auto px-4 py-8 pt-20"><Settings /></div></main></></ProtectedRoute>} />
        <Route path="/chat" element={<ProtectedRoute><><NavBar /><main className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900"><div className="max-w-7xl mx-auto px-4 py-8 pt-20"><Chat /></div></main></></ProtectedRoute>} />

        {/* Catch-all route - redirect unknown paths to login */}
        <Route path="*" element={<AuthRoute><Login /></AuthRoute>} />
      </Routes>
    </BrowserRouter>
  );
}