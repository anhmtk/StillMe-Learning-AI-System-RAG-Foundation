// StillMe Mobile - Settings Screen
import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, Alert } from 'react-native';
import { 
  Text, 
  List, 
  Switch, 
  Button, 
  Card, 
  Divider,
  IconButton,
  Menu,
  Portal
} from 'react-native-paper';
import { useDispatch, useSelector } from 'react-redux';
import { RootState, AppDispatch } from '../store/store';
import { setTheme, setLanguage, setBiometricEnabled, setNotificationPreferences, setPrivacyPreferences } from '../store/slices/settingsSlice';
import { logout } from '../store/slices/authSlice';
import { BiometricService } from '../services/biometric';
import { StorageService } from '../services/storage';
import { theme } from '../theme/theme';

const SettingsScreen: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { preferences, biometricEnabled } = useSelector((state: RootState) => state.settings);
  const { user } = useSelector((state: RootState) => state.auth);
  
  const [biometricService] = useState(new BiometricService());
  const [themeMenuVisible, setThemeMenuVisible] = useState(false);
  const [languageMenuVisible, setLanguageMenuVisible] = useState(false);

  useEffect(() => {
    initializeBiometric();
  }, []);

  const initializeBiometric = async () => {
    try {
      await biometricService.initialize();
      const isEnabled = biometricService.isEnabled();
      dispatch(setBiometricEnabled(isEnabled));
    } catch (error) {
      console.error('Failed to initialize biometric:', error);
    }
  };

  const handleThemeChange = async (newTheme: 'light' | 'dark' | 'auto') => {
    dispatch(setTheme(newTheme));
    setThemeMenuVisible(false);
  };

  const handleLanguageChange = async (newLanguage: string) => {
    dispatch(setLanguage(newLanguage));
    setLanguageMenuVisible(false);
  };

  const handleBiometricToggle = async (enabled: boolean) => {
    try {
      if (enabled) {
        await biometricService.enable();
      } else {
        await biometricService.disable();
      }
      dispatch(setBiometricEnabled(enabled));
    } catch (error) {
      Alert.alert('Error', 'Failed to update biometric settings');
    }
  };

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            try {
              await StorageService.getInstance().clearAuthToken();
              await StorageService.getInstance().saveAuthStatus(false);
              dispatch(logout());
            } catch (error) {
              console.error('Logout error:', error);
            }
          },
        },
      ]
    );
  };

  const handleClearCache = () => {
    Alert.alert(
      'Clear Cache',
      'This will clear all cached data. Continue?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            try {
              await StorageService.getInstance().clearCache();
              Alert.alert('Success', 'Cache cleared successfully');
            } catch (error) {
              Alert.alert('Error', 'Failed to clear cache');
            }
          },
        },
      ]
    );
  };

  const getThemeDisplayName = (theme: string) => {
    switch (theme) {
      case 'light': return 'Light';
      case 'dark': return 'Dark';
      case 'auto': return 'Auto';
      default: return 'Auto';
    }
  };

  const getLanguageDisplayName = (lang: string) => {
    switch (lang) {
      case 'en': return 'English';
      case 'vi': return 'Tiếng Việt';
      default: return 'English';
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Text style={styles.sectionTitle}>Account</Text>
          
          <List.Item
            title="Username"
            description={user?.username || 'Not logged in'}
            left={(props) => <List.Icon {...props} icon="account" />}
          />
          
          <List.Item
            title="Email"
            description={user?.email || 'Not available'}
            left={(props) => <List.Icon {...props} icon="email" />}
          />
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Text style={styles.sectionTitle}>Appearance</Text>
          
          <List.Item
            title="Theme"
            description={getThemeDisplayName(preferences.theme)}
            left={(props) => <List.Icon {...props} icon="theme-light-dark" />}
            right={(props) => (
              <Menu
                visible={themeMenuVisible}
                onDismiss={() => setThemeMenuVisible(false)}
                anchor={
                  <IconButton
                    {...props}
                    icon="chevron-down"
                    onPress={() => setThemeMenuVisible(true)}
                  />
                }
              >
                <Menu.Item onPress={() => handleThemeChange('light')} title="Light" />
                <Menu.Item onPress={() => handleThemeChange('dark')} title="Dark" />
                <Menu.Item onPress={() => handleThemeChange('auto')} title="Auto" />
              </Menu>
            )}
          />
          
          <List.Item
            title="Language"
            description={getLanguageDisplayName(preferences.language)}
            left={(props) => <List.Icon {...props} icon="translate" />}
            right={(props) => (
              <Menu
                visible={languageMenuVisible}
                onDismiss={() => setLanguageMenuVisible(false)}
                anchor={
                  <IconButton
                    {...props}
                    icon="chevron-down"
                    onPress={() => setLanguageMenuVisible(true)}
                  />
                }
              >
                <Menu.Item onPress={() => handleLanguageChange('en')} title="English" />
                <Menu.Item onPress={() => handleLanguageChange('vi')} title="Tiếng Việt" />
              </Menu>
            )}
          />
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Text style={styles.sectionTitle}>Security</Text>
          
          <List.Item
            title="Biometric Authentication"
            description={biometricService.isBiometricAvailable() ? 
              `${biometricService.getBiometricTypeDisplayName()} authentication` : 
              'Not available on this device'
            }
            left={(props) => <List.Icon {...props} icon="fingerprint" />}
            right={() => (
              <Switch
                value={biometricEnabled}
                onValueChange={handleBiometricToggle}
                disabled={!biometricService.isBiometricAvailable()}
              />
            )}
          />
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Text style={styles.sectionTitle}>Notifications</Text>
          
          <List.Item
            title="Enable Notifications"
            description="Receive push notifications"
            left={(props) => <List.Icon {...props} icon="bell" />}
            right={() => (
              <Switch
                value={preferences.notifications.enabled}
                onValueChange={(value) => 
                  dispatch(setNotificationPreferences({ enabled: value }))
                }
              />
            )}
          />
          
          <List.Item
            title="Sound"
            description="Play notification sounds"
            left={(props) => <List.Icon {...props} icon="volume-high" />}
            right={() => (
              <Switch
                value={preferences.notifications.sound}
                onValueChange={(value) => 
                  dispatch(setNotificationPreferences({ sound: value }))
                }
                disabled={!preferences.notifications.enabled}
              />
            )}
          />
          
          <List.Item
            title="Vibration"
            description="Vibrate for notifications"
            left={(props) => <List.Icon {...props} icon="vibrate" />}
            right={() => (
              <Switch
                value={preferences.notifications.vibration}
                onValueChange={(value) => 
                  dispatch(setNotificationPreferences({ vibration: value }))
                }
                disabled={!preferences.notifications.enabled}
              />
            )}
          />
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Text style={styles.sectionTitle}>Privacy</Text>
          
          <List.Item
            title="Data Collection"
            description="Allow data collection for analytics"
            left={(props) => <List.Icon {...props} icon="chart-line" />}
            right={() => (
              <Switch
                value={preferences.privacy.data_collection}
                onValueChange={(value) => 
                  dispatch(setPrivacyPreferences({ data_collection: value }))
                }
              />
            )}
          />
          
          <List.Item
            title="Analytics"
            description="Share usage analytics"
            left={(props) => <List.Icon {...props} icon="analytics" />}
            right={() => (
              <Switch
                value={preferences.privacy.analytics}
                onValueChange={(value) => 
                  dispatch(setPrivacyPreferences({ analytics: value }))
                }
              />
            )}
          />
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Text style={styles.sectionTitle}>Storage</Text>
          
          <List.Item
            title="Clear Cache"
            description="Clear all cached data"
            left={(props) => <List.Icon {...props} icon="delete" />}
            onPress={handleClearCache}
          />
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Button
            mode="outlined"
            onPress={handleLogout}
            style={styles.logoutButton}
            textColor={theme.colors.error}
          >
            Logout
          </Button>
        </Card.Content>
      </Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  card: {
    margin: 16,
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: theme.colors.primary,
    marginBottom: 16,
  },
  logoutButton: {
    borderColor: theme.colors.error,
  },
});

export default SettingsScreen;
