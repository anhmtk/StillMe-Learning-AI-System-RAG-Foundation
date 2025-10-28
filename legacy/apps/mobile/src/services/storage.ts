// StillMe Mobile - Storage Service
import AsyncStorage from '@react-native-async-storage/async-storage';
import { EventEmitter } from 'events';

// Types
import { User, UserPreferences, AppConfig } from '../../../shared/types';

interface StorageKeys {
  USER_DATA: string;
  USER_PREFERENCES: string;
  APP_CONFIG: string;
  AUTH_TOKEN: string;
  AUTH_STATUS: string;
  DEVICE_INFO: string;
  CHAT_HISTORY: string;
  SETTINGS: string;
  CACHE: string;
}

const STORAGE_KEYS: StorageKeys = {
  USER_DATA: 'user_data',
  USER_PREFERENCES: 'user_preferences',
  APP_CONFIG: 'app_config',
  AUTH_TOKEN: 'auth_token',
  AUTH_STATUS: 'auth_status',
  DEVICE_INFO: 'device_info',
  CHAT_HISTORY: 'chat_history',
  SETTINGS: 'settings',
  CACHE: 'cache',
};

interface CacheItem<T = any> {
  key: string;
  value: T;
  timestamp: number;
  ttl: number;
}

export class StorageService extends EventEmitter {
  private static instance: StorageService;
  private cache: Map<string, CacheItem> = new Map();
  private isInitialized = false;

  private constructor() {
    super();
  }

  static getInstance(): StorageService {
    if (!StorageService.instance) {
      StorageService.instance = new StorageService();
    }
    return StorageService.instance;
  }

  async initialize(): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    try {
      // Load cache from storage
      await this.loadCache();
      
      // Clean expired cache items
      this.cleanExpiredCache();
      
      this.isInitialized = true;
      console.log('Storage service initialized');
    } catch (error) {
      console.error('Failed to initialize storage service:', error);
      this.emit('error', error);
    }
  }

  // User Data
  async saveUserData(user: User): Promise<void> {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(user));
      this.emit('user_data_saved', user);
    } catch (error) {
      console.error('Failed to save user data:', error);
      this.emit('error', error);
      throw error;
    }
  }

  async getUserData(): Promise<User | null> {
    try {
      const userData = await AsyncStorage.getItem(STORAGE_KEYS.USER_DATA);
      return userData ? JSON.parse(userData) : null;
    } catch (error) {
      console.error('Failed to get user data:', error);
      this.emit('error', error);
      return null;
    }
  }

  async clearUserData(): Promise<void> {
    try {
      await AsyncStorage.removeItem(STORAGE_KEYS.USER_DATA);
      this.emit('user_data_cleared');
    } catch (error) {
      console.error('Failed to clear user data:', error);
      this.emit('error', error);
    }
  }

  // User Preferences
  async saveUserPreferences(preferences: UserPreferences): Promise<void> {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.USER_PREFERENCES, JSON.stringify(preferences));
      this.emit('preferences_saved', preferences);
    } catch (error) {
      console.error('Failed to save user preferences:', error);
      this.emit('error', error);
      throw error;
    }
  }

  async getUserPreferences(): Promise<UserPreferences | null> {
    try {
      const preferences = await AsyncStorage.getItem(STORAGE_KEYS.USER_PREFERENCES);
      return preferences ? JSON.parse(preferences) : null;
    } catch (error) {
      console.error('Failed to get user preferences:', error);
      this.emit('error', error);
      return null;
    }
  }

  // App Configuration
  async saveAppConfig(config: AppConfig): Promise<void> {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.APP_CONFIG, JSON.stringify(config));
      this.emit('config_saved', config);
    } catch (error) {
      console.error('Failed to save app config:', error);
      this.emit('error', error);
      throw error;
    }
  }

  async getAppConfig(): Promise<AppConfig | null> {
    try {
      const config = await AsyncStorage.getItem(STORAGE_KEYS.APP_CONFIG);
      return config ? JSON.parse(config) : null;
    } catch (error) {
      console.error('Failed to get app config:', error);
      this.emit('error', error);
      return null;
    }
  }

  // Authentication
  async saveAuthToken(token: string): Promise<void> {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, token);
      this.emit('auth_token_saved');
    } catch (error) {
      console.error('Failed to save auth token:', error);
      this.emit('error', error);
      throw error;
    }
  }

  async getAuthToken(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
    } catch (error) {
      console.error('Failed to get auth token:', error);
      this.emit('error', error);
      return null;
    }
  }

  async clearAuthToken(): Promise<void> {
    try {
      await AsyncStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
      this.emit('auth_token_cleared');
    } catch (error) {
      console.error('Failed to clear auth token:', error);
      this.emit('error', error);
    }
  }

  async saveAuthStatus(isAuthenticated: boolean): Promise<void> {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.AUTH_STATUS, JSON.stringify(isAuthenticated));
      this.emit('auth_status_saved', isAuthenticated);
    } catch (error) {
      console.error('Failed to save auth status:', error);
      this.emit('error', error);
      throw error;
    }
  }

  async getAuthStatus(): Promise<boolean> {
    try {
      const status = await AsyncStorage.getItem(STORAGE_KEYS.AUTH_STATUS);
      return status ? JSON.parse(status) : false;
    } catch (error) {
      console.error('Failed to get auth status:', error);
      this.emit('error', error);
      return false;
    }
  }

  // Device Info
  async saveDeviceInfo(deviceInfo: Record<string, any>): Promise<void> {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.DEVICE_INFO, JSON.stringify(deviceInfo));
      this.emit('device_info_saved', deviceInfo);
    } catch (error) {
      console.error('Failed to save device info:', error);
      this.emit('error', error);
      throw error;
    }
  }

  async getDeviceInfo(): Promise<Record<string, any> | null> {
    try {
      const deviceInfo = await AsyncStorage.getItem(STORAGE_KEYS.DEVICE_INFO);
      return deviceInfo ? JSON.parse(deviceInfo) : null;
    } catch (error) {
      console.error('Failed to get device info:', error);
      this.emit('error', error);
      return null;
    }
  }

  // Chat History
  async saveChatHistory(chatHistory: any[]): Promise<void> {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.CHAT_HISTORY, JSON.stringify(chatHistory));
      this.emit('chat_history_saved', chatHistory);
    } catch (error) {
      console.error('Failed to save chat history:', error);
      this.emit('error', error);
      throw error;
    }
  }

  async getChatHistory(): Promise<any[]> {
    try {
      const chatHistory = await AsyncStorage.getItem(STORAGE_KEYS.CHAT_HISTORY);
      return chatHistory ? JSON.parse(chatHistory) : [];
    } catch (error) {
      console.error('Failed to get chat history:', error);
      this.emit('error', error);
      return [];
    }
  }

  async clearChatHistory(): Promise<void> {
    try {
      await AsyncStorage.removeItem(STORAGE_KEYS.CHAT_HISTORY);
      this.emit('chat_history_cleared');
    } catch (error) {
      console.error('Failed to clear chat history:', error);
      this.emit('error', error);
    }
  }

  // Settings
  async saveSettings(settings: Record<string, any>): Promise<void> {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.SETTINGS, JSON.stringify(settings));
      this.emit('settings_saved', settings);
    } catch (error) {
      console.error('Failed to save settings:', error);
      this.emit('error', error);
      throw error;
    }
  }

  async getSettings(): Promise<Record<string, any>> {
    try {
      const settings = await AsyncStorage.getItem(STORAGE_KEYS.SETTINGS);
      return settings ? JSON.parse(settings) : {};
    } catch (error) {
      console.error('Failed to get settings:', error);
      this.emit('error', error);
      return {};
    }
  }

  // Cache Management
  async setCacheItem<T>(key: string, value: T, ttl: number = 3600000): Promise<void> {
    try {
      const cacheItem: CacheItem<T> = {
        key,
        value,
        timestamp: Date.now(),
        ttl,
      };

      this.cache.set(key, cacheItem);
      await this.saveCache();
      this.emit('cache_item_set', { key, value, ttl });
    } catch (error) {
      console.error('Failed to set cache item:', error);
      this.emit('error', error);
    }
  }

  async getCacheItem<T>(key: string): Promise<T | null> {
    try {
      const cacheItem = this.cache.get(key);
      
      if (!cacheItem) {
        return null;
      }

      // Check if expired
      if (Date.now() - cacheItem.timestamp > cacheItem.ttl) {
        this.cache.delete(key);
        await this.saveCache();
        return null;
      }

      return cacheItem.value as T;
    } catch (error) {
      console.error('Failed to get cache item:', error);
      this.emit('error', error);
      return null;
    }
  }

  async removeCacheItem(key: string): Promise<void> {
    try {
      this.cache.delete(key);
      await this.saveCache();
      this.emit('cache_item_removed', key);
    } catch (error) {
      console.error('Failed to remove cache item:', error);
      this.emit('error', error);
    }
  }

  async clearCache(): Promise<void> {
    try {
      this.cache.clear();
      await this.saveCache();
      this.emit('cache_cleared');
    } catch (error) {
      console.error('Failed to clear cache:', error);
      this.emit('error', error);
    }
  }

  // Generic Storage Methods
  async setItem(key: string, value: any): Promise<void> {
    try {
      await AsyncStorage.setItem(key, JSON.stringify(value));
      this.emit('item_saved', { key, value });
    } catch (error) {
      console.error('Failed to set item:', error);
      this.emit('error', error);
      throw error;
    }
  }

  async getItem<T>(key: string): Promise<T | null> {
    try {
      const item = await AsyncStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    } catch (error) {
      console.error('Failed to get item:', error);
      this.emit('error', error);
      return null;
    }
  }

  async removeItem(key: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(key);
      this.emit('item_removed', key);
    } catch (error) {
      console.error('Failed to remove item:', error);
      this.emit('error', error);
    }
  }

  async clearAll(): Promise<void> {
    try {
      await AsyncStorage.clear();
      this.cache.clear();
      this.emit('storage_cleared');
    } catch (error) {
      console.error('Failed to clear all storage:', error);
      this.emit('error', error);
    }
  }

  // Private Methods
  private async loadCache(): Promise<void> {
    try {
      const cacheData = await AsyncStorage.getItem(STORAGE_KEYS.CACHE);
      if (cacheData) {
        const cacheItems = JSON.parse(cacheData);
        this.cache = new Map(Object.entries(cacheItems));
      }
    } catch (error) {
      console.error('Failed to load cache:', error);
    }
  }

  private async saveCache(): Promise<void> {
    try {
      const cacheObject = Object.fromEntries(this.cache);
      await AsyncStorage.setItem(STORAGE_KEYS.CACHE, JSON.stringify(cacheObject));
    } catch (error) {
      console.error('Failed to save cache:', error);
    }
  }

  private cleanExpiredCache(): void {
    const now = Date.now();
    for (const [key, item] of this.cache.entries()) {
      if (now - item.timestamp > item.ttl) {
        this.cache.delete(key);
      }
    }
  }

  // Utility Methods
  async getStorageSize(): Promise<{ used: number; available: number }> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      let used = 0;
      
      for (const key of keys) {
        const value = await AsyncStorage.getItem(key);
        if (value) {
          used += value.length;
        }
      }

      // Estimate available space (this is approximate)
      const available = 50 * 1024 * 1024 - used; // Assume 50MB total

      return { used, available: Math.max(0, available) };
    } catch (error) {
      console.error('Failed to get storage size:', error);
      return { used: 0, available: 0 };
    }
  }

  async getAllKeys(): Promise<string[]> {
    try {
      return await AsyncStorage.getAllKeys();
    } catch (error) {
      console.error('Failed to get all keys:', error);
      return [];
    }
  }

  // Getters
  getCacheSize(): number {
    return this.cache.size;
  }

  isServiceInitialized(): boolean {
    return this.isInitialized;
  }
}
