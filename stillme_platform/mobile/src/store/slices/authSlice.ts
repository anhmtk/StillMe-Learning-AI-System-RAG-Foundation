// StillMe Mobile - Auth Slice
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { User } from '../../../shared/types';

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  biometricEnabled: boolean;
  lastLogin: number | null;
}

const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  token: null,
  isLoading: false,
  error: null,
  biometricEnabled: false,
  lastLogin: null,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setAuthenticated: (state, action: PayloadAction<boolean>) => {
      state.isAuthenticated = action.payload;
      if (!action.payload) {
        state.user = null;
        state.token = null;
        state.lastLogin = null;
      }
    },
    setUser: (state, action: PayloadAction<User | null>) => {
      state.user = action.payload;
    },
    setToken: (state, action: PayloadAction<string | null>) => {
      state.token = action.payload;
    },
    setBiometricEnabled: (state, action: PayloadAction<boolean>) => {
      state.biometricEnabled = action.payload;
    },
    setLastLogin: (state, action: PayloadAction<number>) => {
      state.lastLogin = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    loginSuccess: (state, action: PayloadAction<{ user: User; token: string }>) => {
      state.isAuthenticated = true;
      state.user = action.payload.user;
      state.token = action.payload.token;
      state.lastLogin = Date.now();
      state.error = null;
      state.isLoading = false;
    },
    logout: (state) => {
      state.isAuthenticated = false;
      state.user = null;
      state.token = null;
      state.lastLogin = null;
      state.error = null;
      state.isLoading = false;
    },
    resetAuth: () => initialState,
  },
});

export const {
  setLoading,
  setAuthenticated,
  setUser,
  setToken,
  setBiometricEnabled,
  setLastLogin,
  setError,
  clearError,
  loginSuccess,
  logout,
  resetAuth,
} = authSlice.actions;

export default authSlice.reducer;
