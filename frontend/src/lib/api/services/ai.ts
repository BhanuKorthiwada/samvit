/**
 * AI Assistant API Service
 */

import type {
  AgentInfo,
  ChatRequest,
  ChatResponse,
  SuggestedPromptsResponse,
} from '@/lib/api/types';
import apiClient from '@/lib/api/client';

export const aiService = {
  /**
   * Send a chat message to the HR Assistant
   */
  async chat(message: string, conversationId?: string): Promise<ChatResponse> {
    const request: ChatRequest = {
      message,
      conversation_id: conversationId,
    };
    return apiClient.post<ChatResponse>('/ai/chat', request);
  },

  /**
   * Get list of available AI agents
   */
  async listAgents(): Promise<{ agents: Array<AgentInfo> }> {
    return apiClient.get<{ agents: Array<AgentInfo> }>('/ai/agents');
  },

  /**
   * Get suggested prompts for the chat interface
   */
  async getSuggestedPrompts(): Promise<SuggestedPromptsResponse> {
    return apiClient.get<SuggestedPromptsResponse>('/ai/suggested-prompts');
  },
};

export default aiService;
