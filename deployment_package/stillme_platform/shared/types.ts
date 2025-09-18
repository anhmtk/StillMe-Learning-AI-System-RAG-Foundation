// StillMe Platform - Shared Types
/**
 * Shared type definitions for StillMe multi-platform system
 */

// Base message types
export interface BaseMessage {
  id: string;
  type: MessageType;
  timestamp: number;
  source: string;
  target?: string;
  metadata?: Record<string, any>;
}

export enum MessageType {
  COMMAND = 'command',
  RESPONSE = 'response',
  STATUS = 'status',
  NOTIFICATION = 'notification',
  SYNC = 'sync',
  HEARTBEAT = 'heartbeat',
  ERROR = 'error',
}

export enum MessagePriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  URGENT = 'urgent',
}

export enum MessageStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

// Command message
export interface CommandMessage extends BaseMessage {
  type: MessageType.COMMAND;
  command: string;
  parameters: Record<string, any>;
  context: Record<string, any>;
  async_execution: boolean;
  timeout: number;
  result_location?: string;
  result_type?: string;
}

// Response message
export interface ResponseMessage extends BaseMessage {
  type: MessageType.RESPONSE;
  response_to: string;
  success: boolean;
  result?: Record<string, any>;
  error?: string;
  execution_time?: number;
  memory_usage?: number;
  files?: Record<string, string>;
}

// Status message
export interface StatusMessage extends BaseMessage {
  type: MessageType.STATUS;
  component: string;
  status: string;
  progress?: number;
  message?: string;
  metrics?: Record<string, any>;
}

// Notification message
export interface NotificationMessage extends BaseMessage {
  type: MessageType.NOTIFICATION;
  title: string;
  body: string;
  category: string;
  actions?: Record<string, string>;
  action_url?: string;
  icon?: string;
  sound?: string;
  badge?: number;
}

// Heartbeat message
export interface HeartbeatMessage extends BaseMessage {
  type: MessageType.HEARTBEAT;
  client_info: Record<string, any>;
  system_info: Record<string, any>;
  health_status: string;
  last_activity?: number;
}

// Union type for all messages
export type Message = 
  | CommandMessage 
  | ResponseMessage 
  | StatusMessage 
  | NotificationMessage 
  | HeartbeatMessage;

// Device types
export interface Device {
  id: string;
  name: string;
  type: DeviceType;
  platform: Platform;
  version: string;
  capabilities: DeviceCapability[];
  last_seen: number;
  status: DeviceStatus;
  metadata: Record<string, any>;
}

export enum DeviceType {
  DESKTOP = 'desktop',
  MOBILE = 'mobile',
  WEB = 'web',
  SERVER = 'server',
}

export enum Platform {
  WINDOWS = 'windows',
  MACOS = 'macos',
  LINUX = 'linux',
  ANDROID = 'android',
  IOS = 'ios',
  WEB = 'web',
}

export enum DeviceCapability {
  CHAT = 'chat',
  FILE_UPLOAD = 'file_upload',
  NOTIFICATIONS = 'notifications',
  BIOMETRIC = 'biometric',
  CAMERA = 'camera',
  MICROPHONE = 'microphone',
  LOCATION = 'location',
  STORAGE = 'storage',
}

export enum DeviceStatus {
  ONLINE = 'online',
  OFFLINE = 'offline',
  AWAY = 'away',
  BUSY = 'busy',
}

// User types
export interface User {
  id: string;
  username: string;
  email: string;
  display_name: string;
  avatar?: string;
  preferences: UserPreferences;
  devices: Device[];
  created_at: number;
  last_active: number;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  notifications: NotificationPreferences;
  privacy: PrivacyPreferences;
  accessibility: AccessibilityPreferences;
}

export interface NotificationPreferences {
  enabled: boolean;
  sound: boolean;
  vibration: boolean;
  categories: Record<string, boolean>;
}

export interface PrivacyPreferences {
  data_collection: boolean;
  analytics: boolean;
  crash_reporting: boolean;
  personalized_ads: boolean;
}

export interface AccessibilityPreferences {
  high_contrast: boolean;
  large_text: boolean;
  screen_reader: boolean;
  reduced_motion: boolean;
}

// File types
export interface FileInfo {
  id: string;
  name: string;
  size: number;
  type: string;
  mime_type: string;
  path: string;
  url?: string;
  thumbnail?: string;
  metadata: Record<string, any>;
  created_at: number;
  modified_at: number;
}

// Connection types
export interface ConnectionInfo {
  id: string;
  type: ConnectionType;
  status: ConnectionStatus;
  url: string;
  last_connected: number;
  metadata: Record<string, any>;
}

export enum ConnectionType {
  WEBSOCKET = 'websocket',
  HTTP = 'http',
  GRPC = 'grpc',
}

export enum ConnectionStatus {
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  ERROR = 'error',
}

// Error types
export interface AppError {
  code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: number;
  stack?: string;
}

// Configuration types
export interface AppConfig {
  gateway_url: string;
  stillme_core_url: string;
  api_key?: string;
  debug: boolean;
  auto_update: boolean;
  analytics: boolean;
  crash_reporting: boolean;
}

// Event types
export interface AppEvent {
  type: string;
  data: Record<string, any>;
  timestamp: number;
  source: string;
}

// API Response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: AppError;
  metadata?: Record<string, any>;
}

// WebSocket event types
export interface WebSocketEvent {
  type: string;
  data: any;
  timestamp: number;
}

// Storage types
export interface StorageItem {
  key: string;
  value: any;
  timestamp: number;
  ttl?: number;
}

// Cache types
export interface CacheItem<T = any> {
  key: string;
  value: T;
  timestamp: number;
  ttl: number;
  hits: number;
}

// Queue types
export interface QueueItem {
  id: string;
  type: string;
  data: any;
  priority: MessagePriority;
  attempts: number;
  max_attempts: number;
  created_at: number;
  scheduled_at?: number;
}

// Metrics types
export interface Metrics {
  timestamp: number;
  component: string;
  metrics: Record<string, number>;
  tags: Record<string, string>;
}

// Health check types
export interface HealthCheck {
  component: string;
  status: 'healthy' | 'unhealthy' | 'degraded';
  message?: string;
  metrics?: Record<string, any>;
  timestamp: number;
}

// Log types
export interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: number;
  component: string;
  metadata?: Record<string, any>;
}

export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error',
  FATAL = 'fatal',
}

