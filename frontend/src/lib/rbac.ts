/**
 * Role-Based Access Control (RBAC) utilities
 *
 * Defines role hierarchy and permission checking for frontend route/menu protection.
 */

import { UserRole } from '@/lib/api/types'

/**
 * Role hierarchy - higher index = more permissions
 * super_admin > admin > hr_manager > hr_staff > manager > employee
 */
const ROLE_HIERARCHY: Record<UserRole, number> = {
  [UserRole.SUPER_ADMIN]: 100,
  [UserRole.ADMIN]: 80,
  [UserRole.HR_MANAGER]: 60,
  [UserRole.HR_STAFF]: 50,
  [UserRole.MANAGER]: 40,
  [UserRole.EMPLOYEE]: 10,
}

/**
 * Check if user has a specific role
 */
export function hasRole(userRoles: Array<string>, role: UserRole): boolean {
  return userRoles.includes(role)
}

/**
 * Check if user has any of the specified roles
 */
export function hasAnyRole(
  userRoles: Array<string>,
  roles: ReadonlyArray<UserRole>,
): boolean {
  return roles.some((role) => userRoles.includes(role))
}

/**
 * Check if user has all of the specified roles
 */
export function hasAllRoles(
  userRoles: Array<string>,
  roles: ReadonlyArray<UserRole>,
): boolean {
  return roles.every((role) => userRoles.includes(role))
}

/**
 * Check if user has at least the specified role level (using hierarchy)
 */
export function hasMinRole(
  userRoles: Array<string>,
  minRole: UserRole,
): boolean {
  const minLevel = ROLE_HIERARCHY[minRole]
  return userRoles.some((role) => {
    if (!(role in ROLE_HIERARCHY)) return false
    const level = ROLE_HIERARCHY[role as UserRole]
    return level >= minLevel
  })
}

/**
 * Get the highest role from user's roles
 */
export function getHighestRole(userRoles: Array<string>): UserRole | null {
  let highest: UserRole | null = null
  let highestLevel = -1

  for (const role of userRoles) {
    if (!(role in ROLE_HIERARCHY)) continue
    const level = ROLE_HIERARCHY[role as UserRole]
    if (level > highestLevel) {
      highest = role as UserRole
      highestLevel = level
    }
  }

  return highest
}

/**
 * Role groups for common access patterns
 */
export const RoleGroups = {
  // Platform-level access (cross-tenant)
  PLATFORM_ADMIN: [UserRole.SUPER_ADMIN],

  // Tenant-level admin access
  TENANT_ADMIN: [UserRole.SUPER_ADMIN, UserRole.ADMIN],

  // HR team access
  HR_TEAM: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.HR_MANAGER,
    UserRole.HR_STAFF,
  ],

  // Management access (HR + Managers)
  MANAGEMENT: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.HR_MANAGER,
    UserRole.HR_STAFF,
    UserRole.MANAGER,
  ],

  // All authenticated users
  ALL_USERS: [
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.HR_MANAGER,
    UserRole.HR_STAFF,
    UserRole.MANAGER,
    UserRole.EMPLOYEE,
  ],
} as const

/**
 * Route permission configuration
 */
export interface RoutePermission {
  path: string
  roles: ReadonlyArray<UserRole>
  exact?: boolean
}

/**
 * Define which routes require which roles
 */
export const ROUTE_PERMISSIONS: Array<RoutePermission> = [
  // Platform admin routes (super_admin only)
  { path: '/platform', roles: RoleGroups.PLATFORM_ADMIN },

  // Admin routes
  { path: '/settings', roles: RoleGroups.TENANT_ADMIN },

  // HR routes
  { path: '/employees', roles: RoleGroups.HR_TEAM },
  { path: '/departments', roles: RoleGroups.HR_TEAM },
  { path: '/payroll', roles: RoleGroups.HR_TEAM },

  // Management routes
  { path: '/attendance', roles: RoleGroups.MANAGEMENT },
  { path: '/leave', roles: RoleGroups.MANAGEMENT },

  // All authenticated users
  { path: '/dashboard', roles: RoleGroups.ALL_USERS },
  { path: '/profile', roles: RoleGroups.ALL_USERS },
  { path: '/ai-assistant', roles: RoleGroups.ALL_USERS },
]

/**
 * Check if user can access a specific route
 */
export function canAccessRoute(
  userRoles: Array<string>,
  path: string,
): boolean {
  // Find matching route permission
  const permission = ROUTE_PERMISSIONS.find((rp) => {
    if (rp.exact) {
      return path === rp.path
    }
    return path.startsWith(rp.path)
  })

  // If no permission defined, allow access (fail-open for undefined routes)
  if (!permission) {
    return true
  }

  return hasAnyRole(userRoles, permission.roles)
}

/**
 * Get accessible routes for a user
 */
export function getAccessibleRoutes(userRoles: Array<string>): Array<string> {
  return ROUTE_PERMISSIONS.filter((rp) => hasAnyRole(userRoles, rp.roles)).map(
    (rp) => rp.path,
  )
}

/**
 * Check common role conditions
 */
export const roleChecks = {
  isSuperAdmin: (roles: Array<string>) => hasRole(roles, UserRole.SUPER_ADMIN),
  isAdmin: (roles: Array<string>) =>
    hasAnyRole(roles, [UserRole.SUPER_ADMIN, UserRole.ADMIN]),
  isHR: (roles: Array<string>) => hasAnyRole(roles, RoleGroups.HR_TEAM),
  isManager: (roles: Array<string>) => hasAnyRole(roles, RoleGroups.MANAGEMENT),
  isEmployee: (roles: Array<string>) => roles.length > 0,
}
