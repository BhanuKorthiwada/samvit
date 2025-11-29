/**
 * Tenant API Service
 */

import type { TenantCreate, TenantPublicInfo, TenantResponse } from '@/lib/api/types';
import apiClient from '@/lib/api/client';

export const tenantService = {
  /**
   * Get public tenant info based on current domain
   * Used for branding on login/signup pages
   */
  async getTenantInfo(): Promise<TenantPublicInfo> {
    return apiClient.get<TenantPublicInfo>('/tenants/info');
  },

  /**
   * Create a new tenant (company signup)
   */
  async createTenant(data: TenantCreate): Promise<TenantResponse> {
    return apiClient.post<TenantResponse>('/tenants', data);
  },

  /**
   * Get tenant by ID (admin)
   */
  async getTenant(tenantId: string): Promise<TenantResponse> {
    return apiClient.get<TenantResponse>(`/tenants/${tenantId}`);
  },

  /**
   * Check if domain is available
   */
  async checkDomainAvailability(domain: string): Promise<boolean> {
    try {
      await apiClient.get<TenantResponse>(`/tenants/domain/${domain}`);
      return false; // Domain exists, not available
    } catch {
      return true; // Domain doesn't exist, available
    }
  },
};

export default tenantService;
