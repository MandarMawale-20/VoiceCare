import React, { useEffect, ReactNode, useState } from 'react'; // Removed unused createContext, useContext
import { create, StateCreator } from 'zustand';

interface User {
  id: string;
  email: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  setUserAndToken: (user: User | null, token: string | null) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
}

// This will be replaced by actual API calls to the Python backend
const TEMP_USERS_DB_FOR_MOCKING = [
  { id: '1', email: 'test@example.com', password: 'password123', token: 'fake-jwt-token-example' }
];

const authStateCreator: StateCreator<AuthState> = (set) => ({
  user: null,
  token: null,
  loading: true, // Initially true until session is checked or first login attempt
  setUserAndToken: (user, token) => set({ user, token, loading: false }),
  setLoading: (loadingStatus) => set({ loading: loadingStatus }),
  logout: () => set({ user: null, token: null, loading: false }),
});

export const useAuthStore = create<AuthState>(authStateCreator);

// AuthProvider Component
interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const { setLoading } = useAuthStore();

  // Simulate initial session check or setup
  useEffect(() => {
    // In a real app, you might check localStorage for a token
    // or make a silent refresh API call.
    // For now, just set loading to false after initial setup.
    setLoading(false);
  }, [setLoading]);

  // The AuthProvider's main role here is to ensure the store is initialized
  // and to be a conventional place for auth-related setup logic that needs
  // to run when the app loads (like the useEffect above).
  // It doesn't need to provide a React context if Zustand is used for state management.
  return <>{children}</>;
};

// Hook to use auth state and actions
export function useAuth() {
  const { setUserAndToken, logout: storeLogout, setLoading } = useAuthStore();
  const [user, setUser] = useState<any>(null);

  // These functions will call your Python backend.
  // The current implementation is a mock.
  const login = async (email: string, password: string): Promise<{ user: User; token: string }> => {
    setLoading(true);
    const res = await fetch('http://localhost:5000/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) {
      setLoading(false); // Important: set loading to false on failure
      throw new Error(data.message || 'Login failed');
    }
    const userData = { id: data.user.id, email: data.user.email };
    setUserAndToken(userData, data.token);
    setUser(data.user);
    return data.user;
  };

  const signup = async (email: string, password: string): Promise<{ user: User; token: string }> => {
    setLoading(true);
    const res = await fetch('http://localhost:5000/api/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) {
      setLoading(false);
      throw new Error(data.message || 'Signup failed');
    }
    const userData = { id: data.user.id, email: data.user.email };
    setUserAndToken(userData, data.token);
    setUser(data.user);
    return data.user;
  };

  const logout = () => {
    // Future: Call backend to invalidate token if necessary
    storeLogout();
    // Clear any other user-specific state if needed
  };

  return { user, login, signup, logout };
};