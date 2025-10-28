// StillMe Mobile - Notification Service
import { Platform, Alert, Linking } from 'react-native';
import messaging from '@react-native-firebase/messaging';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { EventEmitter } from 'events';

// Types
import { NotificationMessage, MessageType } from '../../../shared/types';

interface NotificationConfig {
  enabled: boolean;
  sound: boolean;
  vibration: boolean;
  categories: Record<string, boolean>;
}

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

export class NotificationService extends EventEmitter {
  private config: NotificationConfig;
  private notifications: NotificationData[] = [];
  private fcmToken: string | null = null;

  constructor() {
    super();
    this.config = {
      enabled: true,
      sound: true,
      vibration: true,
      categories: {
        general: true,
        chat: true,
        system: true,
        updates: true,
      },
    };
  }

  async initialize(): Promise<void> {
    try {
      // Load config from storage
      await this.loadConfig();

      // Request notification permissions
      await this.requestPermissions();

      // Setup Firebase messaging
      await this.setupFirebaseMessaging();

      // Load stored notifications
      await this.loadNotifications();

      console.log('Notification service initialized');
    } catch (error) {
      console.error('Failed to initialize notification service:', error);
      this.emit('error', error);
    }
  }

  private async loadConfig(): Promise<void> {
    try {
      const savedConfig = await AsyncStorage.getItem('notification_config');
      if (savedConfig) {
        this.config = { ...this.config, ...JSON.parse(savedConfig) };
      }
    } catch (error) {
      console.error('Failed to load notification config:', error);
    }
  }

  private async saveConfig(): Promise<void> {
    try {
      await AsyncStorage.setItem('notification_config', JSON.stringify(this.config));
    } catch (error) {
      console.error('Failed to save notification config:', error);
    }
  }

  private async requestPermissions(): Promise<void> {
    try {
      if (Platform.OS === 'ios') {
        const authStatus = await messaging().requestPermission();
        const enabled =
          authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
          authStatus === messaging.AuthorizationStatus.PROVISIONAL;

        if (!enabled) {
          console.log('Notification permission denied');
          this.config.enabled = false;
        }
      } else {
        // Android permissions are handled in AndroidManifest.xml
        const authStatus = await messaging().requestPermission();
        if (authStatus === messaging.AuthorizationStatus.DENIED) {
          console.log('Notification permission denied');
          this.config.enabled = false;
        }
      }
    } catch (error) {
      console.error('Failed to request notification permissions:', error);
    }
  }

  private async setupFirebaseMessaging(): Promise<void> {
    try {
      // Get FCM token
      this.fcmToken = await messaging().getToken();
      console.log('FCM Token:', this.fcmToken);

      // Save token to storage
      await AsyncStorage.setItem('fcm_token', this.fcmToken);

      // Listen for token refresh
      messaging().onTokenRefresh(async (token) => {
        console.log('FCM Token refreshed:', token);
        this.fcmToken = token;
        await AsyncStorage.setItem('fcm_token', token);
        this.emit('token_refreshed', token);
      });

      // Handle foreground messages
      const unsubscribeForeground = messaging().onMessage(async (remoteMessage) => {
        console.log('Foreground message received:', remoteMessage);
        await this.handleRemoteMessage(remoteMessage);
      });

      // Handle background messages
      messaging().setBackgroundMessageHandler(async (remoteMessage) => {
        console.log('Background message received:', remoteMessage);
        await this.handleRemoteMessage(remoteMessage);
      });

      // Handle notification opened app
      messaging().onNotificationOpenedApp((remoteMessage) => {
        console.log('Notification opened app:', remoteMessage);
        this.handleNotificationOpened(remoteMessage);
      });

      // Check if app was opened from a notification
      const initialNotification = await messaging().getInitialNotification();
      if (initialNotification) {
        console.log('App opened from notification:', initialNotification);
        this.handleNotificationOpened(initialNotification);
      }

    } catch (error) {
      console.error('Failed to setup Firebase messaging:', error);
    }
  }

  private async loadNotifications(): Promise<void> {
    try {
      const savedNotifications = await AsyncStorage.getItem('notifications');
      if (savedNotifications) {
        this.notifications = JSON.parse(savedNotifications);
      }
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  }

  private async saveNotifications(): Promise<void> {
    try {
      await AsyncStorage.setItem('notifications', JSON.stringify(this.notifications));
    } catch (error) {
      console.error('Failed to save notifications:', error);
    }
  }

  private async handleRemoteMessage(remoteMessage: any): Promise<void> {
    try {
      const notificationData: NotificationData = {
        id: remoteMessage.messageId || `notif_${Date.now()}`,
        title: remoteMessage.notification?.title || 'StillMe',
        body: remoteMessage.notification?.body || '',
        category: remoteMessage.data?.category || 'general',
        timestamp: Date.now(),
        read: false,
        actions: remoteMessage.data?.actions ? JSON.parse(remoteMessage.data.actions) : undefined,
        action_url: remoteMessage.data?.action_url,
        metadata: remoteMessage.data,
      };

      // Add to local notifications
      this.notifications.unshift(notificationData);
      
      // Keep only last 100 notifications
      if (this.notifications.length > 100) {
        this.notifications = this.notifications.slice(0, 100);
      }

      // Save to storage
      await this.saveNotifications();

      // Emit event
      this.emit('notification_received', notificationData);

      // Show local notification if app is in foreground
      if (this.config.enabled) {
        this.showLocalNotification(notificationData);
      }

    } catch (error) {
      console.error('Failed to handle remote message:', error);
    }
  }

  private handleNotificationOpened(remoteMessage: any): void {
    try {
      const notificationData: NotificationData = {
        id: remoteMessage.messageId || `notif_${Date.now()}`,
        title: remoteMessage.notification?.title || 'StillMe',
        body: remoteMessage.notification?.body || '',
        category: remoteMessage.data?.category || 'general',
        timestamp: Date.now(),
        read: true,
        actions: remoteMessage.data?.actions ? JSON.parse(remoteMessage.data.actions) : undefined,
        action_url: remoteMessage.data?.action_url,
        metadata: remoteMessage.data,
      };

      this.emit('notification_opened', notificationData);

      // Handle action URL if present
      if (notificationData.action_url) {
        this.handleActionUrl(notificationData.action_url);
      }

    } catch (error) {
      console.error('Failed to handle notification opened:', error);
    }
  }

  private showLocalNotification(notification: NotificationData): void {
    if (Platform.OS === 'ios') {
      // iOS local notifications are handled by Firebase
      return;
    }

    // For Android, we can show a custom alert
    Alert.alert(
      notification.title,
      notification.body,
      [
        {
          text: 'OK',
          onPress: () => {
            this.emit('notification_tapped', notification);
          },
        },
        ...(notification.actions ? Object.entries(notification.actions).map(([key, value]) => ({
          text: value,
          onPress: () => {
            this.emit('notification_action', { notification, action: key });
          },
        })) : []),
      ]
    );
  }

  private async handleActionUrl(url: string): Promise<void> {
    try {
      const canOpen = await Linking.canOpenURL(url);
      if (canOpen) {
        await Linking.openURL(url);
      }
    } catch (error) {
      console.error('Failed to open action URL:', error);
    }
  }

  // Public methods
  async showNotification(
    title: string,
    body: string,
    category: string = 'general',
    actions?: Record<string, string>,
    actionUrl?: string
  ): Promise<void> {
    if (!this.config.enabled) {
      return;
    }

    const notification: NotificationData = {
      id: `local_${Date.now()}`,
      title,
      body,
      category,
      timestamp: Date.now(),
      read: false,
      actions,
      action_url: actionUrl,
    };

    this.notifications.unshift(notification);
    await this.saveNotifications();
    this.emit('notification_received', notification);
    this.showLocalNotification(notification);
  }

  async markAsRead(notificationId: string): Promise<void> {
    const notification = this.notifications.find(n => n.id === notificationId);
    if (notification) {
      notification.read = true;
      await this.saveNotifications();
      this.emit('notification_read', notification);
    }
  }

  async markAllAsRead(): Promise<void> {
    this.notifications.forEach(notification => {
      notification.read = true;
    });
    await this.saveNotifications();
    this.emit('all_notifications_read');
  }

  async clearNotifications(): Promise<void> {
    this.notifications = [];
    await this.saveNotifications();
    this.emit('notifications_cleared');
  }

  async updateConfig(newConfig: Partial<NotificationConfig>): Promise<void> {
    this.config = { ...this.config, ...newConfig };
    await this.saveConfig();
    this.emit('config_updated', this.config);
  }

  // Getters
  getNotifications(): NotificationData[] {
    return [...this.notifications];
  }

  getUnreadCount(): number {
    return this.notifications.filter(n => !n.read).length;
  }

  getConfig(): NotificationConfig {
    return { ...this.config };
  }

  getFCMToken(): string | null {
    return this.fcmToken;
  }

  isEnabled(): boolean {
    return this.config.enabled;
  }
}
