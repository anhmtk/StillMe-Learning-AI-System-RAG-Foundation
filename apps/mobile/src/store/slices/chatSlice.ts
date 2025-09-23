// StillMe Mobile - Chat Slice
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Message, MessageType } from '../../../shared/types';

interface ChatMessage {
  id: string;
  type: MessageType;
  content: string;
  timestamp: number;
  isUser: boolean;
  status: 'sending' | 'sent' | 'delivered' | 'failed';
  metadata?: Record<string, any>;
}

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  isTyping: boolean;
  currentConversation: string | null;
  error: string | null;
  unreadCount: number;
}

const initialState: ChatState = {
  messages: [],
  isLoading: false,
  isTyping: false,
  currentConversation: null,
  error: null,
  unreadCount: 0,
};

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setTyping: (state, action: PayloadAction<boolean>) => {
      state.isTyping = action.payload;
    },
    setCurrentConversation: (state, action: PayloadAction<string | null>) => {
      state.currentConversation = action.payload;
    },
    addMessage: (state, action: PayloadAction<ChatMessage>) => {
      state.messages.push(action.payload);
      if (!action.payload.isUser) {
        state.unreadCount += 1;
      }
    },
    updateMessage: (state, action: PayloadAction<{ id: string; updates: Partial<ChatMessage> }>) => {
      const message = state.messages.find(msg => msg.id === action.payload.id);
      if (message) {
        Object.assign(message, action.payload.updates);
      }
    },
    removeMessage: (state, action: PayloadAction<string>) => {
      state.messages = state.messages.filter(msg => msg.id !== action.payload);
    },
    clearMessages: (state) => {
      state.messages = [];
      state.unreadCount = 0;
    },
    setMessages: (state, action: PayloadAction<ChatMessage[]>) => {
      state.messages = action.payload;
      state.unreadCount = action.payload.filter(msg => !msg.isUser).length;
    },
    markAsRead: (state) => {
      state.unreadCount = 0;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    resetChat: () => initialState,
  },
});

export const {
  setLoading,
  setTyping,
  setCurrentConversation,
  addMessage,
  updateMessage,
  removeMessage,
  clearMessages,
  setMessages,
  markAsRead,
  setError,
  clearError,
  resetChat,
} = chatSlice.actions;

export default chatSlice.reducer;
