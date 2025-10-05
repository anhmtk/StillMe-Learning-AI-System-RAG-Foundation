// StillMe Mobile - Notification Slice
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { NotificationMessage } from '../../../shared/types';

interface NotificationData {
  id: string;
  title: string;
  body: string;
  category: string;
  timestamp: number;
  read: boolean;
  actions?: Record<string, string>;
  action_url?: string;
  metadata?: Record<string, any>;
}

interface NotificationState {
  notifications: NotificationData[];
  unreadCount: number;
  isEnabled: boolean;
  sound: boolean;
  vibration: boolean;
  categories: Record<string, boolean>;
  error: string | null;
}

const initialState: NotificationState = {
  notifications: [],
  unreadCount: 0,
  isEnabled: true,
  sound: true,
  vibration: true,
  categories: {
    general: true,
    chat: true,
    system: true,
    updates: true,
  },
  error: null,
};

const notificationSlice = createSlice({
  name: 'notifications',
  initialState,
  reducers: {
    addNotification: (state, action: PayloadAction<NotificationData>) => {
      state.notifications.unshift(action.payload);
      if (!action.payload.read) {
        state.unreadCount += 1;
      }
    },
    markAsRead: (state, action: PayloadAction<string>) => {
      const notification = state.notifications.find(n => n.id === action.payload);
      if (notification && !notification.read) {
        notification.read = true;
        state.unreadCount = Math.max(0, state.unreadCount - 1);
      }
    },
    markAllAsRead: (state) => {
      state.notifications.forEach(notification => {
        notification.read = true;
      });
      state.unreadCount = 0;
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      const notification = state.notifications.find(n => n.id === action.payload);
      if (notification && !notification.read) {
        state.unreadCount = Math.max(0, state.unreadCount - 1);
      }
      state.notifications = state.notifications.filter(n => n.id !== action.payload);
    },
    clearNotifications: (state) => {
      state.notifications = [];
      state.unreadCount = 0;
    },
    setNotifications: (state, action: PayloadAction<NotificationData[]>) => {
      state.notifications = action.payload;
      state.unreadCount = action.payload.filter(n => !n.read).length;
    },
    setEnabled: (state, action: PayloadAction<boolean>) => {
      state.isEnabled = action.payload;
    },
    setSound: (state, action: PayloadAction<boolean>) => {
      state.sound = action.payload;
    },
    setVibration: (state, action: PayloadAction<boolean>) => {
      state.vibration = action.payload;
    },
    setCategoryEnabled: (state, action: PayloadAction<{ category: string; enabled: boolean }>) => {
      state.categories[action.payload.category] = action.payload.enabled;
    },
    setCategories: (state, action: PayloadAction<Record<string, boolean>>) => {
      state.categories = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    resetNotifications: () => initialState,
  },
});

export const {
  addNotification,
  markAsRead,
  markAllAsRead,
  removeNotification,
  clearNotifications,
  setNotifications,
  setEnabled,
  setSound,
  setVibration,
  setCategoryEnabled,
  setCategories,
  setError,
  clearError,
  resetNotifications,
} = notificationSlice.actions;

export default notificationSlice.reducer;
