import {
  Bot,
  Building2,
  Calendar,
  Clock,
  LayoutDashboard,
  Settings,
  Users,
  Wallet,
  UserCog,
  Bell,
  Shield,
  BarChart3,
} from 'lucide-react'
import { UserRole } from '@/lib/api/types'
import { RoleGroups } from '@/lib/rbac'

interface NavLink {
  title: string
  url: string
  icon?: React.ElementType
  badge?: string
  roles?: readonly UserRole[] // If undefined, accessible to all
}

interface NavCollapsible {
  title: string
  icon?: React.ElementType
  badge?: string
  items: NavLink[]
  roles?: readonly UserRole[] // If undefined, accessible to all
}

type NavItem = NavLink | NavCollapsible

interface NavGroup {
  title: string
  items: NavItem[]
  roles?: readonly UserRole[] // If undefined, accessible to all
}

export const sidebarData: { navGroups: NavGroup[] } = {
  navGroups: [
    // Platform Admin (super_admin only)
    {
      title: 'Platform',
      roles: RoleGroups.PLATFORM_ADMIN,
      items: [
        {
          title: 'Platform Stats',
          url: '/platform',
          icon: BarChart3,
          roles: RoleGroups.PLATFORM_ADMIN,
        },
        {
          title: 'Tenants',
          url: '/platform/tenants',
          icon: Shield,
          roles: RoleGroups.PLATFORM_ADMIN,
        },
      ],
    },
    // Main navigation
    {
      title: 'Main',
      items: [
        {
          title: 'Dashboard',
          url: '/dashboard',
          icon: LayoutDashboard,
        },
        {
          title: 'Employees',
          url: '/employees',
          icon: Users,
          roles: RoleGroups.HR_TEAM,
        },
        {
          title: 'Departments',
          url: '/departments',
          icon: Building2,
          roles: RoleGroups.HR_TEAM,
        },
        {
          title: 'Attendance',
          url: '/attendance',
          icon: Clock,
          roles: RoleGroups.MANAGEMENT,
        },
        {
          title: 'Leave',
          url: '/leave',
          icon: Calendar,
        },
        {
          title: 'Payroll',
          url: '/payroll',
          icon: Wallet,
          roles: RoleGroups.HR_TEAM,
        },
      ],
    },
    {
      title: 'Tools',
      items: [
        {
          title: 'AI Assistant',
          url: '/ai-assistant',
          icon: Bot,
        },
      ],
    },
    {
      title: 'Settings',
      items: [
        {
          title: 'Settings',
          icon: Settings,
          items: [
            {
              title: 'Profile',
              url: '/profile',
              icon: UserCog,
            },
            {
              title: 'Preferences',
              url: '/settings',
              icon: Bell,
              roles: RoleGroups.TENANT_ADMIN,
            },
          ],
        },
      ],
    },
  ],
}

/**
 * Filter sidebar data based on user roles
 */
export function filterSidebarByRoles(
  data: typeof sidebarData,
  userRoles: string[],
): typeof sidebarData {
  const hasAccess = (roles?: readonly UserRole[]) => {
    if (!roles) return true
    return roles.some((role) => userRoles.includes(role))
  }

  const filteredGroups = data.navGroups
    .filter((group) => hasAccess(group.roles))
    .map((group) => ({
      ...group,
      items: group.items
        .filter((item) => hasAccess(item.roles))
        .map((item) => {
          if ('items' in item) {
            return {
              ...item,
              items: item.items.filter((subItem) => hasAccess(subItem.roles)),
            }
          }
          return item
        })
        .filter((item) => {
          // Remove collapsibles with no items
          if ('items' in item && item.items.length === 0) return false
          return true
        }),
    }))
    .filter((group) => group.items.length > 0)

  return { navGroups: filteredGroups }
}
