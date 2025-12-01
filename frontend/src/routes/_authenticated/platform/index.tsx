/**
 * Platform Admin Dashboard - Stats Overview
 */

import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  AlertTriangle,
  Building2,
  TrendingUp,
  Users,
} from 'lucide-react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import apiClient from '@/lib/api/client'

export const Route = createFileRoute('/_authenticated/platform/')({
  component: PlatformDashboard,
})

interface PlatformStats {
  total_tenants: number
  active_tenants: number
  suspended_tenants: number
  total_users: number
  active_users: number
  tenants_by_plan: Record<string, number>
  recent_signups: number
}

function PlatformDashboard() {
  const {
    data: stats,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['platform', 'stats'],
    queryFn: () => apiClient.get<PlatformStats>('/platform/stats'),
  })

  if (isLoading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <div className="text-center text-destructive">
          <AlertTriangle className="h-12 w-12 mx-auto mb-4" />
          <p>Failed to load platform stats</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Platform Admin</h1>
        <p className="text-muted-foreground">
          Monitor and manage all tenants across the platform
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tenants</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.total_tenants ?? 0}
            </div>
            <p className="text-xs text-muted-foreground">
              {stats?.active_tenants ?? 0} active,{' '}
              {stats?.suspended_tenants ?? 0} suspended
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_users ?? 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.active_users ?? 0} active users
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Recent Signups
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.recent_signups ?? 0}
            </div>
            <p className="text-xs text-muted-foreground">Last 30 days</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Rate</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.total_tenants
                ? Math.round((stats.active_tenants / stats.total_tenants) * 100)
                : 0}
              %
            </div>
            <p className="text-xs text-muted-foreground">
              Tenant activity rate
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Plans Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Tenants by Plan</CardTitle>
          <CardDescription>
            Distribution of tenants across subscription plans
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            {stats?.tenants_by_plan &&
              Object.entries(stats.tenants_by_plan).map(([plan, count]) => (
                <div key={plan} className="flex items-center gap-2">
                  <Badge
                    variant={plan === 'enterprise' ? 'default' : 'secondary'}
                  >
                    {plan}
                  </Badge>
                  <span className="text-sm font-medium">{count}</span>
                </div>
              ))}
            {(!stats?.tenants_by_plan ||
              Object.keys(stats.tenants_by_plan).length === 0) && (
              <p className="text-sm text-muted-foreground">
                No plan data available
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-4">
          <a
            href="/platform/tenants"
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Building2 className="h-4 w-4" />
            Manage Tenants
          </a>
        </CardContent>
      </Card>
    </div>
  )
}
