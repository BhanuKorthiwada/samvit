/**
 * Route protection components for RBAC
 */

import { Navigate } from '@tanstack/react-router'
import type { ReactNode } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { UserRole } from '@/lib/api/types'
import { hasAnyRole, RoleGroups } from '@/lib/rbac'

interface RequireRoleProps {
  children: ReactNode
  roles: readonly UserRole[]
  fallback?: ReactNode
  redirectTo?: string
}

/**
 * Protect a route/component by required roles
 */
export function RequireRole({
  children,
  roles,
  fallback,
  redirectTo = '/dashboard',
}: RequireRoleProps) {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" />
  }

  const hasAccess = hasAnyRole(user.roles, roles)

  if (!hasAccess) {
    if (fallback) {
      return <>{fallback}</>
    }
    return <Navigate to={redirectTo} />
  }

  return <>{children}</>
}

/**
 * Pre-configured role guards
 */
export function RequireSuperAdmin({
  children,
  fallback,
}: {
  children: ReactNode
  fallback?: ReactNode
}) {
  return (
    <RequireRole roles={RoleGroups.PLATFORM_ADMIN} fallback={fallback}>
      {children}
    </RequireRole>
  )
}

export function RequireAdmin({
  children,
  fallback,
}: {
  children: ReactNode
  fallback?: ReactNode
}) {
  return (
    <RequireRole roles={RoleGroups.TENANT_ADMIN} fallback={fallback}>
      {children}
    </RequireRole>
  )
}

export function RequireHR({
  children,
  fallback,
}: {
  children: ReactNode
  fallback?: ReactNode
}) {
  return (
    <RequireRole roles={RoleGroups.HR_TEAM} fallback={fallback}>
      {children}
    </RequireRole>
  )
}

export function RequireManagement({
  children,
  fallback,
}: {
  children: ReactNode
  fallback?: ReactNode
}) {
  return (
    <RequireRole roles={RoleGroups.MANAGEMENT} fallback={fallback}>
      {children}
    </RequireRole>
  )
}

/**
 * Hide content if user doesn't have required role
 */
interface ShowForRoleProps {
  children: ReactNode
  roles: readonly UserRole[]
}

export function ShowForRole({ children, roles }: ShowForRoleProps) {
  const { user } = useAuth()

  if (!user) return null

  const hasAccess = hasAnyRole(user.roles, roles)

  if (!hasAccess) return null

  return <>{children}</>
}

/**
 * Pre-configured show components
 */
export function ShowForSuperAdmin({ children }: { children: ReactNode }) {
  return <ShowForRole roles={RoleGroups.PLATFORM_ADMIN}>{children}</ShowForRole>
}

export function ShowForAdmin({ children }: { children: ReactNode }) {
  return <ShowForRole roles={RoleGroups.TENANT_ADMIN}>{children}</ShowForRole>
}

export function ShowForHR({ children }: { children: ReactNode }) {
  return <ShowForRole roles={RoleGroups.HR_TEAM}>{children}</ShowForRole>
}

export function ShowForManagement({ children }: { children: ReactNode }) {
  return <ShowForRole roles={RoleGroups.MANAGEMENT}>{children}</ShowForRole>
}
