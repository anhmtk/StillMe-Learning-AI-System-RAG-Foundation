// StillMe Mobile - App Slice
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ConnectionStatus } from '../../../shared/types';

interface AppState {
  isLoading: boolean;
  isInitialized: boolean;
  connectionStatus: ConnectionStatus;
  theme: 'light' | 'dark' | 'auto';
  language: string;
  lastActivity: number;
  error: string | null;
}

const initialState: AppState = {
  isLoading: true,
  isInitialized: false,
  connectionStatus: ConnectionStatus.DISCONNECTED,
  theme: 'auto',
  language: 'en',
  lastActivity: Date.now(),
  error: null,
};

const appSlice = createSlice({
  name: 'app',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setInitialized: (state, action: PayloadAction<boolean>) => {
      state.isInitialized = action.payload;
    },
    setConnectionStatus: (state, action: PayloadAction<ConnectionStatus>) => {
      state.connectionStatus = action.payload;
    },
    setTheme: (state, action: PayloadAction<'light' | 'dark' | 'auto'>) => {
      state.theme = action.payload;
    },
    setLanguage: (state, action: PayloadAction<string>) => {
      state.language = action.payload;
    },
    updateLastActivity: (state) => {
      state.lastActivity = Date.now();
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    resetApp: () => initialState,
  },
});

export const {
  setLoading,
  setInitialized,
  setConnectionStatus,
  setTheme,
  setLanguage,
  updateLastActivity,
  setError,
  clearError,
  resetApp,
} = appSlice.actions;

export default appSlice.reducer;
