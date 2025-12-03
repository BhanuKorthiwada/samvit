/**
 * Policy Management API Service
 */

import type {
  PaginatedResponse,
  PolicyCategory,
  PolicyChatRequest,
  PolicyChatResponse,
  PolicyCreate,
  PolicyIndexResponse,
  PolicyQueryRequest,
  PolicyQueryResponse,
  PolicyResponse,
  PolicySummary,
  PolicyUpdate,
  SuccessResponse,
} from '@/lib/api/types'
import apiClient from '@/lib/api/client'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

export const policyService = {
  /**
   * Create a new policy
   */
  async create(data: PolicyCreate): Promise<PolicyResponse> {
    return apiClient.post<PolicyResponse>('/policies', data)
  },

  /**
   * List all policies with pagination
   */
  async list(options?: {
    page?: number
    pageSize?: number
    category?: PolicyCategory
    includeArchived?: boolean
  }): Promise<PaginatedResponse<PolicySummary>> {
    return apiClient.get<PaginatedResponse<PolicySummary>>('/policies', {
      page: options?.page || 1,
      page_size: options?.pageSize || 20,
      category: options?.category,
      include_archived: options?.includeArchived,
    })
  },

  /**
   * Get policy by ID
   */
  async get(id: string): Promise<PolicyResponse> {
    return apiClient.get<PolicyResponse>(`/policies/${id}`)
  },

  /**
   * Update a policy
   */
  async update(id: string, data: PolicyUpdate): Promise<PolicyResponse> {
    return apiClient.patch<PolicyResponse>(`/policies/${id}`, data)
  },

  /**
   * Delete a policy
   */
  async delete(id: string): Promise<SuccessResponse> {
    return apiClient.delete<SuccessResponse>(`/policies/${id}`)
  },

  /**
   * Upload a policy file
   */
  async upload(
    file: File,
    metadata: {
      name: string
      category: string
      description?: string
      version?: string
    },
  ): Promise<PolicyResponse> {
    const token = localStorage.getItem('access_token')
    const formData = new FormData()
    formData.append('file', file)
    formData.append('name', metadata.name)
    formData.append('category', metadata.category)
    if (metadata.description) {
      formData.append('description', metadata.description)
    }
    if (metadata.version) {
      formData.append('version', metadata.version)
    }

    const response = await fetch(`${API_BASE_URL}/policies/upload`, {
      method: 'POST',
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.detail || 'Failed to upload policy')
    }

    return response.json()
  },

  /**
   * Index a policy for RAG search
   */
  async index(id: string, force = false): Promise<PolicyIndexResponse> {
    return apiClient.post<PolicyIndexResponse>(
      `/policies/${id}/index?force=${force}`,
    )
  },

  /**
   * Index multiple policies (or all if not specified)
   */
  async indexAll(
    policyIds?: Array<string>,
    force = true,
  ): Promise<PolicyIndexResponse> {
    return apiClient.post<PolicyIndexResponse>('/policies/index', {
      policy_ids: policyIds || null,
      force,
    })
  },

  /**
   * Query policies using RAG
   */
  async query(request: PolicyQueryRequest): Promise<PolicyQueryResponse> {
    return apiClient.post<PolicyQueryResponse>('/policies/query', request)
  },
}

export const policyChatService = {
  /**
   * Chat with the policy AI agent
   */
  async chat(
    question: string,
    conversationId?: string,
  ): Promise<PolicyChatResponse> {
    const request: PolicyChatRequest = {
      question,
      conversation_id: conversationId,
    }
    return apiClient.post<PolicyChatResponse>('/ai/policy-chat', request)
  },
}

export default policyService
