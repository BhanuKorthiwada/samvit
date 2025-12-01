/**
 * Platform Admin - Tenants Management
 */

import { Link, createFileRoute } from '@tanstack/react-router'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import {
  Building2,
  ExternalLink,
  Eye,
  MoreHorizontal,
  Pause,
  Play,
  RefreshCw,
  Search,
  Trash2,
} from 'lucide-react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import apiClient from '@/lib/api/client'

export const Route = createFileRoute('/_authenticated/platform/tenants')({
  component: TenantsManagement,
})

interface Tenant {
  id: string
  name: string
  domain: string
  email: string
  plan: string
  status: string
  is_active: boolean
  created_at: string
  max_employees: number
  max_users: number
}

interface TenantsResponse {
  items: Array<Tenant>
  total: number
  page: number
  page_size: number
  total_pages: number
}

function TenantsManagement() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null)
  const [actionType, setActionType] = useState<
    'suspend' | 'activate' | 'delete' | null
  >(null)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['platform', 'tenants', page, search],
    queryFn: () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: '20',
      })
      if (search) {
        return apiClient.get<TenantsResponse>(
          `/platform/tenants/search?q=${encodeURIComponent(search)}&${params}`,
        )
      }
      return apiClient.get<TenantsResponse>(`/platform/tenants?${params}`)
    },
  })

  const suspendMutation = useMutation({
    mutationFn: (tenantId: string) =>
      apiClient.post(`/platform/tenants/${tenantId}/suspend`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['platform', 'tenants'] })
      queryClient.invalidateQueries({ queryKey: ['platform', 'stats'] })
      setSelectedTenant(null)
      setActionType(null)
    },
  })

  const activateMutation = useMutation({
    mutationFn: (tenantId: string) =>
      apiClient.post(`/platform/tenants/${tenantId}/activate`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['platform', 'tenants'] })
      queryClient.invalidateQueries({ queryKey: ['platform', 'stats'] })
      setSelectedTenant(null)
      setActionType(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (tenantId: string) =>
      apiClient.delete(`/platform/tenants/${tenantId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['platform', 'tenants'] })
      queryClient.invalidateQueries({ queryKey: ['platform', 'stats'] })
      setSelectedTenant(null)
      setActionType(null)
    },
  })

  const handleAction = () => {
    if (!selectedTenant || !actionType) return

    switch (actionType) {
      case 'suspend':
        suspendMutation.mutate(selectedTenant.id)
        break
      case 'activate':
        activateMutation.mutate(selectedTenant.id)
        break
      case 'delete':
        deleteMutation.mutate(selectedTenant.id)
        break
    }
  }

  const getStatusBadge = (status: string, isActive: boolean) => {
    if (!isActive || status === 'suspended') {
      return <Badge variant="destructive">Suspended</Badge>
    }
    if (status === 'active') {
      return <Badge variant="default">Active</Badge>
    }
    return <Badge variant="secondary">{status}</Badge>
  }

  const getPlanBadge = (plan: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'outline'> = {
      enterprise: 'default',
      professional: 'default',
      starter: 'secondary',
      free: 'outline',
    }
    return <Badge variant={variants[plan] ?? 'outline'}>{plan}</Badge>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Tenants</h1>
          <p className="text-muted-foreground">
            Manage all organizations on the platform
          </p>
        </div>
        <Button onClick={() => refetch()} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Search */}
      <Card>
        <CardHeader>
          <CardTitle>Search Tenants</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search by name, domain, or email..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value)
                  setPage(1)
                }}
                className="pl-9"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tenants Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Tenants</CardTitle>
          <CardDescription>{data?.total ?? 0} total tenants</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Domain</TableHead>
                    <TableHead>Plan</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Limits</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="w-[50px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data?.items.map((tenant) => (
                    <TableRow key={tenant.id}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <Building2 className="h-4 w-4 text-muted-foreground" />
                          {tenant.name}
                        </div>
                      </TableCell>
                      <TableCell>
                        <a
                          href={`https://${tenant.domain}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-primary hover:underline"
                        >
                          {tenant.domain}
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </TableCell>
                      <TableCell>{getPlanBadge(tenant.plan)}</TableCell>
                      <TableCell>
                        {getStatusBadge(tenant.status, tenant.is_active)}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {tenant.max_employees} emp / {tenant.max_users} users
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(tenant.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem asChild>
                              <Link
                                to="/platform/tenants/$tenantId"
                                params={{ tenantId: tenant.id }}
                              >
                                <Eye className="h-4 w-4 mr-2" />
                                View Details
                              </Link>
                            </DropdownMenuItem>
                            {tenant.is_active &&
                            tenant.status !== 'suspended' ? (
                              <DropdownMenuItem
                                onClick={() => {
                                  setSelectedTenant(tenant)
                                  setActionType('suspend')
                                }}
                                className="text-orange-600"
                              >
                                <Pause className="h-4 w-4 mr-2" />
                                Suspend
                              </DropdownMenuItem>
                            ) : (
                              <DropdownMenuItem
                                onClick={() => {
                                  setSelectedTenant(tenant)
                                  setActionType('activate')
                                }}
                                className="text-green-600"
                              >
                                <Play className="h-4 w-4 mr-2" />
                                Activate
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => {
                                setSelectedTenant(tenant)
                                setActionType('delete')
                              }}
                              className="text-destructive"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                  {(!data?.items || data.items.length === 0) && (
                    <TableRow>
                      <TableCell
                        colSpan={7}
                        className="text-center py-8 text-muted-foreground"
                      >
                        No tenants found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>

              {/* Pagination */}
              {data && data.total_pages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm text-muted-foreground">
                    Page {data.page} of {data.total_pages}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => p + 1)}
                      disabled={page >= data.total_pages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Confirmation Dialog */}
      <AlertDialog
        open={!!actionType && !!selectedTenant}
        onOpenChange={() => {
          setActionType(null)
          setSelectedTenant(null)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {actionType === 'suspend' && 'Suspend Tenant'}
              {actionType === 'activate' && 'Activate Tenant'}
              {actionType === 'delete' && 'Delete Tenant'}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {actionType === 'suspend' && (
                <>
                  Are you sure you want to suspend{' '}
                  <strong>{selectedTenant?.name}</strong>? All users will be
                  unable to access the system.
                </>
              )}
              {actionType === 'activate' && (
                <>
                  Are you sure you want to activate{' '}
                  <strong>{selectedTenant?.name}</strong>? All users will regain
                  access to the system.
                </>
              )}
              {actionType === 'delete' && (
                <>
                  Are you sure you want to delete{' '}
                  <strong>{selectedTenant?.name}</strong>? This action cannot be
                  undone and all data will be permanently removed.
                </>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleAction}
              className={
                actionType === 'delete'
                  ? 'bg-destructive hover:bg-destructive/90'
                  : ''
              }
            >
              {actionType === 'suspend' && 'Suspend'}
              {actionType === 'activate' && 'Activate'}
              {actionType === 'delete' && 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
