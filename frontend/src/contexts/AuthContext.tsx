/**
 * Authentication Context and Provider
 */

import {  createContext, useCallback, useContext, useEffect, useState } from 'react';
import type {ReactNode} from 'react';
import type {CurrentUserResponse} from '@/lib/api';
import {  authService } from '@/lib/api';
import { apiClient } from '@/lib/api/client';

interface AuthContextType {
  user: CurrentUserResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  setTenantId: (tenantId: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<CurrentUserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const userData = await authService.getCurrentUser();
      setUser(userData);
      // Set tenant ID for subsequent API calls
      apiClient.setTenantId(userData.tenant_id);
    } catch {
      setUser(null);
      authService.logout();
    }
  }, []);

  // Check for existing auth on mount
  useEffect(() => {
    const initAuth = async () => {
      if (authService.isAuthenticated()) {
        await refreshUser();
      }
      setIsLoading(false);
    };
    initAuth();
  }, [refreshUser]);

  const login = async (email: string, password: string) => {
    await authService.login({ email, password });
    await refreshUser();
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    apiClient.setTenantId(null);
    window.location.href = '/login';
  };

  const setTenantId = (tenantId: string) => {
    apiClient.setTenantId(tenantId);
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    refreshUser,
    setTenantId,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
