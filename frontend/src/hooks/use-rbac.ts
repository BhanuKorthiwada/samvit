/**
 * RBAC Hook for role-based access control
 *
 * Provides easy access to role checking functions within React components.
 */

import { useMemo } from 'react'
import type { UserRole } from '@/lib/api/types'
import { useAuth } from '@/contexts/AuthContext'
import {
  RoleGroups,
  canAccessRoute,
  getHighestRole,
  hasAnyRole,
  hasMinRole,
  hasRole,
  roleChecks,
} from '@/lib/rbac'

export function useRBAC() {
  const { user } = useAuth()
  const roles = user?.roles ?? []

  return useMemo(
    () => ({
      // Current user's roles
      roles,

      // Role checking functions
      hasRole: (role: UserRole) => hasRole(roles, role),
      hasAnyRole: (checkRoles: ReadonlyArray<UserRole>) =>
        hasAnyRole(roles, checkRoles),
      hasMinRole: (minRole: UserRole) => hasMinRole(roles, minRole),
      canAccessRoute: (path: string) => canAccessRoute(roles, path),

      // Computed properties
      highestRole: getHighestRole(roles),

      // Common role checks
      isSuperAdmin: roleChecks.isSuperAdmin(roles),
      isAdmin: roleChecks.isAdmin(roles),
      isHR: roleChecks.isHR(roles),
      isManager: roleChecks.isManager(roles),
      isEmployee: roleChecks.isEmployee(roles),

      // Role groups for UI
      canAccessPlatform: hasAnyRole(roles, RoleGroups.PLATFORM_ADMIN),
      canAccessAdmin: hasAnyRole(roles, RoleGroups.TENANT_ADMIN),
      canAccessHR: hasAnyRole(roles, RoleGroups.HR_TEAM),
      canAccessManagement: hasAnyRole(roles, RoleGroups.MANAGEMENT),
    }),
    [roles],
  )
}

export type RBACContext = ReturnType<typeof useRBAC>
