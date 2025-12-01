/**
 * Authentication Context and Provider
 *
 * Multi-tenancy is handled via domain-based identification.
 * Users access their tenant via subdomain (e.g., acme.samvit.bhanu.dev).
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react'
import type { ReactNode } from 'react'
import type { CurrentUserResponse } from '@/lib/api'
import { authService } from '@/lib/api'

interface AuthContextType {
  user: CurrentUserResponse | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<CurrentUserResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    try {
      const userData = await authService.getCurrentUser()
      setUser(userData)
    } catch {
      setUser(null)
      authService.logout()
    }
  }, [])

  // Check for existing auth on mount
  useEffect(() => {
    const initAuth = async () => {
      if (authService.isAuthenticated()) {
        await refreshUser()
      }
      setIsLoading(false)
    }
    initAuth()
  }, [refreshUser])

  const login = async (email: string, password: string) => {
    await authService.login({ email, password })
    await refreshUser()
  }

  const logout = () => {
    authService.logout()
    setUser(null)
    window.location.href = '/login'
  }

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
