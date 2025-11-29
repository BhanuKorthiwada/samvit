import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from '@/components/ui/sidebar'
import { Building2 } from 'lucide-react'
import { sidebarData } from './sidebar-data'
import { NavGroup } from './nav-group'
import { NavUser } from './nav-user'

export function AppSidebar() {
  return (
    <Sidebar collapsible='icon'>
      <SidebarHeader>
        <div className='flex items-center gap-3 px-2 py-2'>
          <div className='flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10'>
            <Building2 className='h-6 w-6 text-primary' />
          </div>
          <span className='text-xl font-bold group-data-[collapsible=icon]:hidden'>
            SAMVIT
          </span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        {sidebarData.navGroups.map((props) => (
          <NavGroup key={props.title} {...props} />
        ))}
      </SidebarContent>
      <SidebarFooter>
        <NavUser />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
