/**
 * Leave Management API Service
 */

import type {
  HolidayCreate,
  HolidayResponse,
  LeaveApproval,
  LeaveBalanceResponse,
  LeavePolicyCreate,
  LeavePolicyResponse,
  LeavePolicyUpdate,
  LeaveRequestCreate,
  LeaveRequestResponse,
  LeaveStatus,
} from '@/lib/api/types';
import apiClient from '@/lib/api/client';

export const leavePolicyService = {
  /**
   * Create a new leave policy
   */
  async create(data: LeavePolicyCreate): Promise<LeavePolicyResponse> {
    return apiClient.post<LeavePolicyResponse>('/leave/policies', data);
  },

  /**
   * List all leave policies
   */
  async list(activeOnly = true): Promise<Array<LeavePolicyResponse>> {
    return apiClient.get<Array<LeavePolicyResponse>>('/leave/policies', {
      active_only: activeOnly,
    });
  },

  /**
   * Get leave policy by ID
   */
  async get(id: string): Promise<LeavePolicyResponse> {
    return apiClient.get<LeavePolicyResponse>(`/leave/policies/${id}`);
  },

  /**
   * Update a leave policy
   */
  async update(id: string, data: LeavePolicyUpdate): Promise<LeavePolicyResponse> {
    return apiClient.patch<LeavePolicyResponse>(`/leave/policies/${id}`, data);
  },
};

export const leaveBalanceService = {
  /**
   * Get current user's leave balances
   */
  async getMyBalances(year?: number): Promise<Array<LeaveBalanceResponse>> {
    return apiClient.get<Array<LeaveBalanceResponse>>('/leave/balances/me', { year });
  },

  /**
   * Get an employee's leave balances
   */
  async getEmployeeBalances(employeeId: string, year?: number): Promise<Array<LeaveBalanceResponse>> {
    return apiClient.get<Array<LeaveBalanceResponse>>(`/leave/balances/${employeeId}`, { year });
  },

  /**
   * Initialize leave balances for an employee
   */
  async initializeBalances(employeeId: string, year?: number): Promise<Array<LeaveBalanceResponse>> {
    const params = year ? `?year=${year}` : '';
    return apiClient.post<Array<LeaveBalanceResponse>>(
      `/leave/balances/${employeeId}/initialize${params}`,
      undefined
    );
  },
};

export const leaveRequestService = {
  /**
   * Create a new leave request
   */
  async create(data: LeaveRequestCreate): Promise<LeaveRequestResponse> {
    return apiClient.post<LeaveRequestResponse>('/leave/requests', data);
  },

  /**
   * Get current user's leave requests
   */
  async getMyRequests(status?: LeaveStatus, year?: number): Promise<Array<LeaveRequestResponse>> {
    return apiClient.get<Array<LeaveRequestResponse>>('/leave/requests/me', { status, year });
  },

  /**
   * Get pending leave requests for approval
   */
  async getPendingApprovals(): Promise<Array<LeaveRequestResponse>> {
    return apiClient.get<Array<LeaveRequestResponse>>('/leave/requests/pending');
  },

  /**
   * Get leave request by ID
   */
  async get(id: string): Promise<LeaveRequestResponse> {
    return apiClient.get<LeaveRequestResponse>(`/leave/requests/${id}`);
  },

  /**
   * Approve or reject a leave request
   */
  async processApproval(id: string, data: LeaveApproval): Promise<LeaveRequestResponse> {
    return apiClient.post<LeaveRequestResponse>(`/leave/requests/${id}/approve`, data);
  },

  /**
   * Cancel a leave request
   */
  async cancel(id: string): Promise<LeaveRequestResponse> {
    return apiClient.post<LeaveRequestResponse>(`/leave/requests/${id}/cancel`);
  },
};

export const holidayService = {
  /**
   * Create a new holiday
   */
  async create(data: HolidayCreate): Promise<HolidayResponse> {
    return apiClient.post<HolidayResponse>('/leave/holidays', data);
  },

  /**
   * List holidays for a year
   */
  async list(year?: number): Promise<Array<HolidayResponse>> {
    return apiClient.get<Array<HolidayResponse>>('/leave/holidays', { year });
  },
};
