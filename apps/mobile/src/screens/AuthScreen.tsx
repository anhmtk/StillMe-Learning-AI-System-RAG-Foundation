// StillMe Mobile - Authentication Screen
import React, { useState, useEffect } from 'react';
import { View, StyleSheet, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { Text, TextInput, Button, Card, Switch } from 'react-native-paper';
import { useDispatch, useSelector } from 'react-redux';
import { RootState, AppDispatch } from '../store/store';
import { loginSuccess, setLoading, setError } from '../store/slices/authSlice';
import { BiometricService } from '../services/biometric';
import { StorageService } from '../services/storage';
import { theme } from '../theme/theme';

const AuthScreen: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { isLoading, error, biometricEnabled } = useSelector((state: RootState) => state.auth);
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [biometricService] = useState(new BiometricService());

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

  const handleLogin = async () => {
    if (!username.trim() || !password.trim()) {
      dispatch(setError('Please enter both username and password'));
      return;
    }

    dispatch(setLoading(true));
    dispatch(setError(null));

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Mock user data
      const user = {
        id: '1',
        username: username.trim(),
        email: `${username.trim()}@stillme.ai`,
        display_name: username.trim(),
        preferences: {
          theme: 'auto' as const,
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
        devices: [],
        created_at: Date.now(),
        last_active: Date.now(),
      };

      const token = `token_${Date.now()}`;

      // Save to storage
      await StorageService.getInstance().saveUserData(user);
      await StorageService.getInstance().saveAuthToken(token);
      await StorageService.getInstance().saveAuthStatus(true);

      dispatch(loginSuccess({ user, token }));
    } catch (error) {
      dispatch(setError('Login failed. Please try again.'));
    } finally {
      dispatch(setLoading(false));
    }
  };

  const handleBiometricLogin = async () => {
    try {
      const result = await biometricService.authenticate('Login to StillMe');
      if (result.success) {
        // Load saved credentials and login
        const savedUser = await StorageService.getInstance().getUserData();
        const savedToken = await StorageService.getInstance().getAuthToken();
        
        if (savedUser && savedToken) {
          dispatch(loginSuccess({ user: savedUser, token: savedToken }));
        } else {
          dispatch(setError('No saved credentials found'));
        }
      } else {
        dispatch(setError(result.error || 'Biometric authentication failed'));
      }
    } catch (error) {
      dispatch(setError('Biometric authentication error'));
    }
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container} 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.content}>
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.title}>Welcome to StillMe</Text>
            <Text style={styles.subtitle}>Sign in to continue</Text>

            <TextInput
              label="Username"
              value={username}
              onChangeText={setUsername}
              mode="outlined"
              style={styles.input}
              autoCapitalize="none"
              autoCorrect={false}
            />

            <TextInput
              label="Password"
              value={password}
              onChangeText={setPassword}
              mode="outlined"
              secureTextEntry
              style={styles.input}
            />

            <View style={styles.rememberMe}>
              <Text>Remember me</Text>
              <Switch
                value={rememberMe}
                onValueChange={setRememberMe}
              />
            </View>

            {error && (
              <Text style={styles.errorText}>{error}</Text>
            )}

            <Button
              mode="contained"
              onPress={handleLogin}
              loading={isLoading}
              disabled={isLoading}
              style={styles.loginButton}
            >
              Sign In
            </Button>

            {biometricEnabled && (
              <Button
                mode="outlined"
                onPress={handleBiometricLogin}
                style={styles.biometricButton}
                icon="fingerprint"
              >
                Use Biometric
              </Button>
            )}
          </Card.Content>
        </Card>
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    padding: 16,
  },
  card: {
    elevation: 4,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 8,
    color: theme.colors.primary,
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 24,
    color: theme.colors.onSurfaceVariant,
  },
  input: {
    marginBottom: 16,
  },
  rememberMe: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  errorText: {
    color: theme.colors.error,
    textAlign: 'center',
    marginBottom: 16,
  },
  loginButton: {
    marginBottom: 16,
  },
  biometricButton: {
    marginBottom: 8,
  },
});

export default AuthScreen;
