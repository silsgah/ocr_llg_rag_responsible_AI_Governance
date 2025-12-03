'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load token and user from localStorage on mount
  useEffect(() => {
    const loadAuth = async () => {
      const storedToken = localStorage.getItem('auth_token');
      if (storedToken) {
        setToken(storedToken);
        try {
          // Fetch current user
          const response = await fetch(`${API_BASE}/users/me`, {
            headers: {
              'Authorization': `Bearer ${storedToken}`,
            },
          });
          if (response.ok) {
            const userData = await response.json();
            setUser(userData);
          } else {
            // Token invalid, clear it
            localStorage.removeItem('auth_token');
            setToken(null);
          }
        } catch (error) {
          console.error('Failed to fetch user:', error);
          localStorage.removeItem('auth_token');
          setToken(null);
        }
      }
      setIsLoading(false);
    };

    loadAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    const accessToken = data.access_token;

    // Store token
    localStorage.setItem('auth_token', accessToken);
    setToken(accessToken);

    // Fetch user data
    const userResponse = await fetch(`${API_BASE}/users/me`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });

    if (userResponse.ok) {
      const userData = await userResponse.json();
      setUser(userData);
    }
  };

  const register = async (email: string, password: string, fullName: string) => {
    const response = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Registration failed' }));
      throw new Error(error.detail || 'Registration failed');
    }

    // After successful registration, log the user in
    await login(email, password);
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        register,
        logout,
        isAuthenticated: !!token && !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
