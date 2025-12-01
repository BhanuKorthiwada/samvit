/**
 * Platform Admin routes layout
 * Only accessible to super_admin users
 */

import { Outlet, createFileRoute } from '@tanstack/react-router'
import { RequireSuperAdmin } from '@/components/auth'

export const Route = createFileRoute('/_authenticated/platform')({
  component: PlatformLayout,
})

function PlatformLayout() {
  return (
    <RequireSuperAdmin
      fallback={
        <div className="flex h-[50vh] items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-destructive">
              Access Denied
            </h2>
            <p className="text-muted-foreground mt-2">
              You don't have permission to access the platform admin area.
            </p>
          </div>
        </div>
      }
    >
      <Outlet />
    </RequireSuperAdmin>
  )
}
