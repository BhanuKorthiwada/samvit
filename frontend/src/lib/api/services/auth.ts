/**
 * Auth API Service
 */

import type {
  ChangePasswordRequest,
  CompanyRegisterRequest,
  CompanyRegisterResponse,
  CurrentUserResponse,
  LoginRequest,
  PaginatedResponse,
  RegisterRequest,
  SuccessResponse,
  TokenResponse,
  UserResponse,
  UserSummary,
} from '@/lib/api/types'
import apiClient from '@/lib/api/client'

export const authService = {
  /**
   * Register a new user (within existing tenant)
   */
  async register(data: RegisterRequest): Promise<UserResponse> {
    return apiClient.post<UserResponse>('/auth/register', data)
  },

  /**
   * Register a new company (creates tenant + admin user)
   * This is the company signup flow.
   */
  async registerCompany(
    data: CompanyRegisterRequest,
  ): Promise<CompanyRegisterResponse> {
    const response = await apiClient.post<CompanyRegisterResponse>(
      '/auth/register/company',
      data,
    )

    // Store tokens after successful registration
    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('refresh_token', response.refresh_token)

    return response
  },

  /**
   * Login and get access tokens
   */
  async login(data: LoginRequest): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/auth/login', data)

    // Store tokens
    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('refresh_token', response.refresh_token)

    return response
  },

  /**
   * Logout - clear tokens
   */
  logout(): void {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  },

  /**
   * Refresh access token
   */
  async refreshTokens(): Promise<TokenResponse> {
    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }

    const response = await apiClient.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    })

    // Update stored tokens
    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('refresh_token', response.refresh_token)

    return response
  },

  /**
   * Get current authenticated user
   */
  async getCurrentUser(): Promise<CurrentUserResponse> {
    return apiClient.get<CurrentUserResponse>('/auth/me')
  },

  /**
   * Update current user's profile
   */
  async updateProfile(data: Partial<UserResponse>): Promise<UserResponse> {
    return apiClient.patch<UserResponse>('/auth/me', data)
  },

  /**
   * Change password
   */
  async changePassword(data: ChangePasswordRequest): Promise<SuccessResponse> {
    return apiClient.post<SuccessResponse>('/auth/change-password', data)
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token')
  },

  /**
   * List users (admin only)
   */
  async listUsers(
    page = 1,
    pageSize = 20,
  ): Promise<PaginatedResponse<UserSummary>> {
    return apiClient.get<PaginatedResponse<UserSummary>>('/users', {
      page,
      page_size: pageSize,
    })
  },
}

export default authService
