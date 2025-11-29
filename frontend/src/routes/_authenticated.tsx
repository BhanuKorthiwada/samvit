import { Outlet, createFileRoute, redirect } from '@tanstack/react-router'
import { SidebarInset, SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar'
import { AppSidebar } from '@/components/layout/app-sidebar'
import { Separator } from '@/components/ui/separator'
import { ThemeToggle } from '@/components/layout/theme-toggle'

export const Route = createFileRoute('/_authenticated')({
  beforeLoad: () => {
    if (!localStorage.getItem('access_token')) {
      throw redirect({ to: '/login' })
    }
  },
  component: AuthenticatedLayout,
})

function AuthenticatedLayout() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className='flex h-16 shrink-0 items-center gap-2 border-b'>
          <div className='flex items-center gap-2 px-4'>
            <SidebarTrigger className='-ml-1' />
            <Separator orientation='vertical' className='mr-2 h-4' />
          </div>
          <div className='ml-auto flex items-center gap-2 px-4'>
            <ThemeToggle />
          </div>
        </header>
        <main className='flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-8'>
          <Outlet />
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
