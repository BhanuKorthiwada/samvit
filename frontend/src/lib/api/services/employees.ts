/**
 * Employee API Service
 */

import type {
  DepartmentCreate,
  DepartmentResponse,
  DepartmentSummary,
  DepartmentUpdate,
  EmployeeCreate,
  EmployeeResponse,
  EmployeeStats,
  EmployeeSummary,
  EmployeeUpdate,
  PaginatedResponse,
  PositionCreate,
  PositionResponse,
  PositionSummary,
  PositionUpdate,
  SuccessResponse,
} from '../types'
import apiClient from '@/lib/api/client'

export const departmentService = {
  /**
   * Create a new department
   */
  async create(data: DepartmentCreate): Promise<DepartmentResponse> {
    return apiClient.post<DepartmentResponse>('/departments', data)
  },

  /**
   * List all departments
   */
  async list(
    page = 1,
    pageSize = 20,
  ): Promise<PaginatedResponse<DepartmentSummary>> {
    return apiClient.get<PaginatedResponse<DepartmentSummary>>('/departments', {
      page,
      page_size: pageSize,
    })
  },

  /**
   * Get department by ID
   */
  async get(id: string): Promise<DepartmentResponse> {
    return apiClient.get<DepartmentResponse>(`/departments/${id}`)
  },

  /**
   * Update a department
   */
  async update(
    id: string,
    data: DepartmentUpdate,
  ): Promise<DepartmentResponse> {
    return apiClient.patch<DepartmentResponse>(`/departments/${id}`, data)
  },

  /**
   * Delete a department
   */
  async delete(id: string): Promise<SuccessResponse> {
    return apiClient.delete<SuccessResponse>(`/departments/${id}`)
  },
}

export const positionService = {
  /**
   * Create a new position
   */
  async create(data: PositionCreate): Promise<PositionResponse> {
    return apiClient.post<PositionResponse>('/positions', data)
  },

  /**
   * List all positions
   */
  async list(
    page = 1,
    pageSize = 20,
  ): Promise<PaginatedResponse<PositionSummary>> {
    return apiClient.get<PaginatedResponse<PositionSummary>>('/positions', {
      page,
      page_size: pageSize,
    })
  },

  /**
   * Get position by ID
   */
  async get(id: string): Promise<PositionResponse> {
    return apiClient.get<PositionResponse>(`/positions/${id}`)
  },

  /**
   * Update a position
   */
  async update(id: string, data: PositionUpdate): Promise<PositionResponse> {
    return apiClient.patch<PositionResponse>(`/positions/${id}`, data)
  },

  /**
   * Delete a position
   */
  async delete(id: string): Promise<SuccessResponse> {
    return apiClient.delete<SuccessResponse>(`/positions/${id}`)
  },
}

export const employeeService = {
  /**
   * Create a new employee
   */
  async create(data: EmployeeCreate): Promise<EmployeeResponse> {
    return apiClient.post<EmployeeResponse>('/employees', data)
  },

  /**
   * List employees with optional filters
   */
  async list(
    page = 1,
    pageSize = 20,
    departmentId?: string,
  ): Promise<PaginatedResponse<EmployeeSummary>> {
    return apiClient.get<PaginatedResponse<EmployeeSummary>>('/employees', {
      page,
      page_size: pageSize,
      department_id: departmentId,
    })
  },

  /**
   * Search employees by name, email, or code
   */
  async search(query: string, limit = 20): Promise<Array<EmployeeSummary>> {
    return apiClient.get<Array<EmployeeSummary>>('/employees/search', {
      q: query,
      limit,
    })
  },

  /**
   * Get employee statistics
   */
  async getStats(): Promise<EmployeeStats> {
    return apiClient.get<EmployeeStats>('/employees/stats')
  },

  /**
   * Get employee by ID
   */
  async get(id: string): Promise<EmployeeResponse> {
    return apiClient.get<EmployeeResponse>(`/employees/${id}`)
  },

  /**
   * Update an employee
   */
  async update(id: string, data: EmployeeUpdate): Promise<EmployeeResponse> {
    return apiClient.patch<EmployeeResponse>(`/employees/${id}`, data)
  },

  /**
   * Get direct reports for an employee
   */
  async getDirectReports(id: string): Promise<Array<EmployeeSummary>> {
    return apiClient.get<Array<EmployeeSummary>>(
      `/employees/${id}/direct-reports`,
    )
  },

  /**
   * Deactivate an employee
   */
  async deactivate(id: string): Promise<EmployeeResponse> {
    return apiClient.post<EmployeeResponse>(`/employees/${id}/deactivate`)
  },
}
