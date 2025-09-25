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
import Signup from "./pages/Signup";
import Forgot from "./pages/Forgot";
import StoreSuccess from "./pages/StoreSuccess";
import ResetPassword from "./pages/ResetPassword";
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
        {/* Public routes */}
        <Route path="/" element={<><NavBar /><main className="max-w-7xl mx-auto px-4 py-6"><Home /></main></>} />

        {/* Auth routes (redirect if already logged in) */}
        <Route path="/login" element={<AuthRoute><Login /></AuthRoute>} />
        <Route path="/signup" element={<AuthRoute><Signup /></AuthRoute>} />
        <Route path="/forgot" element={<AuthRoute><Forgot /></AuthRoute>} />
        <Route path="/reset-password" element={<AuthRoute><ResetPassword /></AuthRoute>} />

        {/* Protected routes (require authentication) */}
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/library" element={<ProtectedRoute><><NavBar /><main className="max-w-7xl mx-auto px-4 py-6"><Library /></main></></ProtectedRoute>} />
        <Route path="/create" element={<ProtectedRoute><><NavBar /><main className="max-w-7xl mx-auto px-4 py-6"><CreatePoster /></main></></ProtectedRoute>} />
        <Route path="/wallet" element={<ProtectedRoute><><NavBar /><main className="max-w-7xl mx-auto px-4 py-6"><Wallet /></main></></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute><><NavBar /><main className="max-w-7xl mx-auto px-4 py-6"><Profile /></main></></ProtectedRoute>} />
        <Route path="/store" element={<ProtectedRoute><><NavBar /><main className="max-w-7xl mx-auto px-4 py-6"><Store /></main></></ProtectedRoute>} />
        <Route path="/store/success" element={<ProtectedRoute><><NavBar /><main className="max-w-7xl mx-auto px-4 py-6"><StoreSuccess /></main></></ProtectedRoute>} />
        <Route path="/checkout/success" element={<ProtectedRoute><><NavBar /><main className="max-w-7xl mx-auto px-4 py-6"><CheckoutSuccess /></main></></ProtectedRoute>} />
        <Route path="/checkout/cancel" element={<ProtectedRoute><><NavBar /><main className="max-w-7xl mx-auto px-4 py-6"><CheckoutCancel /></main></></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><><NavBar /><main className="max-w-7xl mx-auto px-4 py-6"><Settings /></main></></ProtectedRoute>} />
        <Route path="/chat" element={<ProtectedRoute><><NavBar /><main className="max-w-7xl mx-auto px-4 py-6"><Chat /></main></></ProtectedRoute>} />
      </Routes>
    </BrowserRouter>
  );
}