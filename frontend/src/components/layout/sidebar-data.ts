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
} from 'lucide-react'

interface NavLink {
  title: string
  url: string
  icon?: React.ElementType
  badge?: string
}

interface NavCollapsible {
  title: string
  icon?: React.ElementType
  badge?: string
  items: NavLink[]
}

type NavItem = NavLink | NavCollapsible

interface NavGroup {
  title: string
  items: NavItem[]
}

export const sidebarData: { navGroups: NavGroup[] } = {
  navGroups: [
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
        },
        {
          title: 'Departments',
          url: '/departments',
          icon: Building2,
        },
        {
          title: 'Attendance',
          url: '/attendance',
          icon: Clock,
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
            },
          ],
        },
      ],
    },
  ],
}
