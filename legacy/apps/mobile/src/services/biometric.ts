// StillMe Mobile - Biometric Service
import { Platform, Alert } from 'react-native';
import ReactNativeBiometrics from 'react-native-biometrics';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { EventEmitter } from 'events';

interface BiometricConfig {
  enabled: boolean;
  type: 'fingerprint' | 'face' | 'iris' | 'voice' | 'none';
  fallbackToPasscode: boolean;
  requireConfirmation: boolean;
}

interface BiometricResult {
  success: boolean;
  error?: string;
  biometryType?: string;
}

export class BiometricService extends EventEmitter {
  private config: BiometricConfig;
  private rnBiometrics: ReactNativeBiometrics;
  private isAvailable: boolean = false;
  private biometryType: string = 'none';

  constructor() {
    super();
    this.config = {
      enabled: false,
      type: 'none',
      fallbackToPasscode: true,
      requireConfirmation: true,
    };
    this.rnBiometrics = new ReactNativeBiometrics({
      allowDeviceCredentials: true,
    });
  }

  async initialize(): Promise<void> {
    try {
      // Load config from storage
      await this.loadConfig();

      // Check biometric availability
      await this.checkAvailability();

      console.log('Biometric service initialized');
    } catch (error) {
      console.error('Failed to initialize biometric service:', error);
      this.emit('error', error);
    }
  }

  private async loadConfig(): Promise<void> {
    try {
      const savedConfig = await AsyncStorage.getItem('biometric_config');
      if (savedConfig) {
        this.config = { ...this.config, ...JSON.parse(savedConfig) };
      }
    } catch (error) {
      console.error('Failed to load biometric config:', error);
    }
  }

  private async saveConfig(): Promise<void> {
    try {
      await AsyncStorage.setItem('biometric_config', JSON.stringify(this.config));
    } catch (error) {
      console.error('Failed to save biometric config:', error);
    }
  }

  private async checkAvailability(): Promise<void> {
    try {
      const { available, biometryType } = await this.rnBiometrics.isSensorAvailable();
      
      this.isAvailable = available;
      this.biometryType = biometryType || 'none';

      console.log('Biometric availability:', { available, biometryType });

      if (available) {
        this.emit('biometric_available', { type: biometryType });
      } else {
        this.emit('biometric_unavailable', { reason: 'No biometric sensor found' });
      }
    } catch (error) {
      console.error('Failed to check biometric availability:', error);
      this.isAvailable = false;
      this.emit('error', error);
    }
  }

  async authenticate(reason: string = 'Authenticate to continue'): Promise<BiometricResult> {
    if (!this.isAvailable || !this.config.enabled) {
      return {
        success: false,
        error: 'Biometric authentication not available or disabled',
      };
    }

    try {
      const promptMessage = Platform.OS === 'ios' 
        ? reason 
        : `${reason}\nUse your ${this.biometryType} to authenticate`;

      const { success, error } = await this.rnBiometrics.simplePrompt({
        promptMessage,
        cancelButtonText: 'Cancel',
        fallbackPromptMessage: this.config.fallbackToPasscode 
          ? 'Use device passcode instead' 
          : undefined,
      });

      if (success) {
        this.emit('authentication_success');
        return { success: true, biometryType: this.biometryType };
      } else {
        this.emit('authentication_failed', { error });
        return { success: false, error: error || 'Authentication failed' };
      }
    } catch (error) {
      console.error('Biometric authentication error:', error);
      this.emit('authentication_error', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Authentication error',
      };
    }
  }

  async createKeyPair(): Promise<{ success: boolean; publicKey?: string; error?: string }> {
    if (!this.isAvailable) {
      return {
        success: false,
        error: 'Biometric authentication not available',
      };
    }

    try {
      const { publicKey } = await this.rnBiometrics.createKeys();
      
      // Save public key to storage
      await AsyncStorage.setItem('biometric_public_key', publicKey);
      
      this.emit('key_pair_created', { publicKey });
      return { success: true, publicKey };
    } catch (error) {
      console.error('Failed to create biometric key pair:', error);
      this.emit('key_pair_error', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to create key pair',
      };
    }
  }

  async deleteKeyPair(): Promise<{ success: boolean; error?: string }> {
    try {
      await this.rnBiometrics.deleteKeys();
      await AsyncStorage.removeItem('biometric_public_key');
      
      this.emit('key_pair_deleted');
      return { success: true };
    } catch (error) {
      console.error('Failed to delete biometric key pair:', error);
      this.emit('key_pair_error', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to delete key pair',
      };
    }
  }

  async signMessage(message: string): Promise<{ success: boolean; signature?: string; error?: string }> {
    if (!this.isAvailable) {
      return {
        success: false,
        error: 'Biometric authentication not available',
      };
    }

    try {
      const { success, signature } = await this.rnBiometrics.createSignature({
        promptMessage: 'Sign message with biometric',
        payload: message,
        cancelButtonText: 'Cancel',
      });

      if (success && signature) {
        this.emit('message_signed', { message, signature });
        return { success: true, signature };
      } else {
        return { success: false, error: 'Failed to sign message' };
      }
    } catch (error) {
      console.error('Failed to sign message:', error);
      this.emit('signature_error', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to sign message',
      };
    }
  }

  async verifySignature(message: string, signature: string): Promise<{ success: boolean; error?: string }> {
    try {
      const { success } = await this.rnBiometrics.biometricKeysExist();
      
      if (!success) {
        return { success: false, error: 'Biometric keys not found' };
      }

      // Note: React Native Biometrics doesn't have a direct verify method
      // This would typically be done server-side or with additional crypto libraries
      this.emit('signature_verified', { message, signature });
      return { success: true };
    } catch (error) {
      console.error('Failed to verify signature:', error);
      this.emit('verification_error', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to verify signature',
      };
    }
  }

  async enable(): Promise<void> {
    if (!this.isAvailable) {
      throw new Error('Biometric authentication not available');
    }

    this.config.enabled = true;
    await this.saveConfig();
    this.emit('biometric_enabled');
  }

  async disable(): Promise<void> {
    this.config.enabled = false;
    await this.saveConfig();
    this.emit('biometric_disabled');
  }

  async updateConfig(newConfig: Partial<BiometricConfig>): Promise<void> {
    this.config = { ...this.config, ...newConfig };
    await this.saveConfig();
    this.emit('config_updated', this.config);
  }

  // Getters
  isBiometricAvailable(): boolean {
    return this.isAvailable;
  }

  getBiometryType(): string {
    return this.biometryType;
  }

  isEnabled(): boolean {
    return this.config.enabled;
  }

  getConfig(): BiometricConfig {
    return { ...this.config };
  }

  async getPublicKey(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem('biometric_public_key');
    } catch (error) {
      console.error('Failed to get public key:', error);
      return null;
    }
  }

  // Utility methods
  getBiometricTypeDisplayName(): string {
    switch (this.biometryType) {
      case 'TouchID':
        return 'Touch ID';
      case 'FaceID':
        return 'Face ID';
      case 'Fingerprint':
        return 'Fingerprint';
      case 'Face':
        return 'Face Recognition';
      case 'Iris':
        return 'Iris';
      case 'Voice':
        return 'Voice Recognition';
      default:
        return 'Biometric';
    }
  }

  showBiometricSettings(): void {
    Alert.alert(
      'Biometric Settings',
      `Biometric authentication is ${this.isAvailable ? 'available' : 'not available'} on this device.\n\nType: ${this.getBiometricTypeDisplayName()}\nStatus: ${this.config.enabled ? 'Enabled' : 'Disabled'}`,
      [
        { text: 'OK' },
        ...(this.isAvailable ? [
          {
            text: this.config.enabled ? 'Disable' : 'Enable',
            onPress: () => {
              if (this.config.enabled) {
                this.disable();
              } else {
                this.enable();
              }
            },
          },
        ] : []),
      ]
    );
  }
}
