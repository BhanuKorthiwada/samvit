/**
 * Tenant API Service
 *
 * Public endpoints: /tenants/* (no auth required)
 * Admin endpoints: /platform/tenants/* (super_admin only)
 */

import type {
  TenantCreate,
  TenantPublicInfo,
  TenantResponse,
} from '@/lib/api/types'
import apiClient from '@/lib/api/client'

export const tenantService = {
  /**
   * Get public tenant info based on current domain.
   * Used for branding on login/signup pages.
   * NO AUTH REQUIRED.
   */
  async getTenantInfo(): Promise<TenantPublicInfo> {
    return apiClient.get<TenantPublicInfo>('/tenants/info')
  },
}

/**
 * Platform Admin API - requires super_admin role
 */
export const platformTenantService = {
  /**
   * Create a new tenant (platform admin only)
   */
  async createTenant(data: TenantCreate): Promise<TenantResponse> {
    return apiClient.post<TenantResponse>('/platform/tenants', data)
  },

  /**
   * Get tenant by ID (platform admin only)
   */
  async getTenant(tenantId: string): Promise<TenantResponse> {
    return apiClient.get<TenantResponse>(`/platform/tenants/${tenantId}`)
  },

  /**
   * Check if domain is available
   */
  async checkDomainAvailability(domain: string): Promise<boolean> {
    try {
      await apiClient.get<TenantResponse>(`/platform/tenants/domain/${domain}`)
      return false // Domain exists, not available
    } catch {
      return true // Domain doesn't exist, available
    }
  },

  /**
   * List all tenants (paginated)
   */
  async listTenants(page = 1, pageSize = 20): Promise<Array<TenantResponse>> {
    return apiClient.get<Array<TenantResponse>>(
      `/platform/tenants?page=${page}&page_size=${pageSize}`,
    )
  },

  /**
   * Search tenants
   */
  async searchTenants(query: string): Promise<Array<TenantResponse>> {
    return apiClient.get<Array<TenantResponse>>(
      `/platform/tenants/search?q=${encodeURIComponent(query)}`,
    )
  },

  /**
   * Suspend a tenant
   */
  async suspendTenant(tenantId: string): Promise<TenantResponse> {
    return apiClient.post<TenantResponse>(
      `/platform/tenants/${tenantId}/suspend`,
    )
  },

  /**
   * Activate a tenant
   */
  async activateTenant(tenantId: string): Promise<TenantResponse> {
    return apiClient.post<TenantResponse>(
      `/platform/tenants/${tenantId}/activate`,
    )
  },
}

export default tenantService
