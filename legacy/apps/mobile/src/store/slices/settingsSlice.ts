// StillMe Mobile - Settings Slice
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { UserPreferences } from '../../../shared/types';

interface SettingsState {
  preferences: UserPreferences;
  biometricEnabled: boolean;
  autoSync: boolean;
  cacheSize: number;
  lastSync: number | null;
  error: string | null;
}

const initialState: SettingsState = {
  preferences: {
    theme: 'auto',
    language: 'en',
    notifications: {
      enabled: true,
      sound: true,
      vibration: true,
      categories: {
        general: true,
        chat: true,
        system: true,
        updates: true,
      },
    },
    privacy: {
      data_collection: true,
      analytics: true,
      crash_reporting: true,
      personalized_ads: false,
    },
    accessibility: {
      high_contrast: false,
      large_text: false,
      screen_reader: false,
      reduced_motion: false,
    },
  },
  biometricEnabled: false,
  autoSync: true,
  cacheSize: 0,
  lastSync: null,
  error: null,
};

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    setPreferences: (state, action: PayloadAction<UserPreferences>) => {
      state.preferences = action.payload;
    },
    setTheme: (state, action: PayloadAction<'light' | 'dark' | 'auto'>) => {
      state.preferences.theme = action.payload;
    },
    setLanguage: (state, action: PayloadAction<string>) => {
      state.preferences.language = action.payload;
    },
    setNotificationPreferences: (state, action: PayloadAction<Partial<UserPreferences['notifications']>>) => {
      state.preferences.notifications = { ...state.preferences.notifications, ...action.payload };
    },
    setPrivacyPreferences: (state, action: PayloadAction<Partial<UserPreferences['privacy']>>) => {
      state.preferences.privacy = { ...state.preferences.privacy, ...action.payload };
    },
    setAccessibilityPreferences: (state, action: PayloadAction<Partial<UserPreferences['accessibility']>>) => {
      state.preferences.accessibility = { ...state.preferences.accessibility, ...action.payload };
    },
    setBiometricEnabled: (state, action: PayloadAction<boolean>) => {
      state.biometricEnabled = action.payload;
    },
    setAutoSync: (state, action: PayloadAction<boolean>) => {
      state.autoSync = action.payload;
    },
    setCacheSize: (state, action: PayloadAction<number>) => {
      state.cacheSize = action.payload;
    },
    setLastSync: (state, action: PayloadAction<number>) => {
      state.lastSync = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    resetSettings: () => initialState,
  },
});

export const {
  setPreferences,
  setTheme,
  setLanguage,
  setNotificationPreferences,
  setPrivacyPreferences,
  setAccessibilityPreferences,
  setBiometricEnabled,
  setAutoSync,
  setCacheSize,
  setLastSync,
  setError,
  clearError,
  resetSettings,
} = settingsSlice.actions;

export default settingsSlice.reducer;
