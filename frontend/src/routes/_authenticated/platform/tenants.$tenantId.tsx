/**
 * Platform Admin - Tenant Details
 */

import { Link, createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowLeft,
  Building2,
  Calendar,
  Clock,
  Globe,
  Mail,
  MapPin,
  Phone,
  UserCheck,
  Users,
} from 'lucide-react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import apiClient from '@/lib/api/client'

export const Route = createFileRoute(
  '/_authenticated/platform/tenants/$tenantId',
)({
  component: TenantDetails,
})

interface TenantDetail {
  id: string
  name: string
  domain: string
  email: string
  phone: string | null
  address: string | null
  city: string | null
  state: string | null
  country: string
  postal_code: string | null
  plan: string
  status: string
  is_active: boolean
  max_employees: number
  max_users: number
  timezone: string
  currency: string
  date_format: string
  logo_url: string | null
  primary_color: string
  created_at: string
  updated_at: string
}

interface TenantStats {
  total_users: number
  active_users: number
  total_employees: number
  total_departments: number
}

function TenantDetails() {
  const { tenantId } = Route.useParams()

  const { data: tenant, isLoading: loadingTenant } = useQuery({
    queryKey: ['platform', 'tenant', tenantId],
    queryFn: () => apiClient.get<TenantDetail>(`/platform/tenants/${tenantId}`),
  })

  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ['platform', 'tenant', tenantId, 'stats'],
    queryFn: () =>
      apiClient.get<TenantStats>(`/platform/tenants/${tenantId}/stats`),
  })

  if (loadingTenant) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (!tenant) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold">Tenant Not Found</h2>
          <p className="text-muted-foreground mt-2">
            The tenant you're looking for doesn't exist.
          </p>
          <Button asChild className="mt-4">
            <Link to="/platform/tenants">Back to Tenants</Link>
          </Button>
        </div>
      </div>
    )
  }

  const getStatusBadge = () => {
    if (!tenant.is_active || tenant.status === 'suspended') {
      return <Badge variant="destructive">Suspended</Badge>
    }
    if (tenant.status === 'active') {
      return <Badge variant="default">Active</Badge>
    }
    return <Badge variant="secondary">{tenant.status}</Badge>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button asChild variant="ghost" size="icon">
          <Link to="/platform/tenants">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight">{tenant.name}</h1>
            {getStatusBadge()}
            <Badge variant="outline">{tenant.plan}</Badge>
          </div>
          <p className="text-muted-foreground">{tenant.domain}</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loadingStats ? '...' : (stats?.total_users ?? 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Max: {tenant.max_users}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <UserCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loadingStats ? '...' : (stats?.active_users ?? 0)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Employees</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loadingStats ? '...' : (stats?.total_employees ?? 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Max: {tenant.max_employees}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Departments</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loadingStats ? '...' : (stats?.total_departments ?? 0)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Details Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Basic Info */}
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              <Building2 className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Company Name</p>
                <p className="font-medium">{tenant.name}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Globe className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Domain</p>
                <a
                  href={`https://${tenant.domain}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-primary hover:underline"
                >
                  {tenant.domain}
                </a>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Mail className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Email</p>
                <p className="font-medium">{tenant.email}</p>
              </div>
            </div>
            {tenant.phone && (
              <div className="flex items-center gap-3">
                <Phone className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Phone</p>
                  <p className="font-medium">{tenant.phone}</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Location */}
        <Card>
          <CardHeader>
            <CardTitle>Location & Settings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              <MapPin className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Address</p>
                <p className="font-medium">
                  {[tenant.address, tenant.city, tenant.state, tenant.country]
                    .filter(Boolean)
                    .join(', ') || 'Not set'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Timezone</p>
                <p className="font-medium">{tenant.timezone}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Created</p>
                <p className="font-medium">
                  {new Date(tenant.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div
                className="h-4 w-4 rounded"
                style={{ backgroundColor: tenant.primary_color }}
              />
              <div>
                <p className="text-sm text-muted-foreground">Primary Color</p>
                <p className="font-medium">{tenant.primary_color}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Subscription */}
      <Card>
        <CardHeader>
          <CardTitle>Subscription & Limits</CardTitle>
          <CardDescription>Current plan and resource limits</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <p className="text-sm text-muted-foreground">Plan</p>
              <Badge className="mt-1">{tenant.plan}</Badge>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Max Employees</p>
              <p className="font-medium">{tenant.max_employees}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Max Users</p>
              <p className="font-medium">{tenant.max_users}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Currency</p>
              <p className="font-medium">{tenant.currency}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
