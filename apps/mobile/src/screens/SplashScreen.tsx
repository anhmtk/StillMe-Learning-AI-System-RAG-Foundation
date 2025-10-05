// StillMe Mobile - Splash Screen
import React from 'react';
import { View, StyleSheet, ActivityIndicator } from 'react-native';
import { Text } from 'react-native-paper';
import { theme } from '../theme/theme';

const SplashScreen: React.FC = () => {
  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>StillMe</Text>
        <Text style={styles.subtitle}>AI Assistant</Text>
        <ActivityIndicator 
          size="large" 
          color={theme.colors.primary} 
          style={styles.loader}
        />
        <Text style={styles.loadingText}>Initializing...</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    alignItems: 'center',
  },
  title: {
    fontSize: 48,
    fontWeight: 'bold',
    color: theme.colors.primary,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 18,
    color: theme.colors.onSurfaceVariant,
    marginBottom: 48,
  },
  loader: {
    marginBottom: 16,
  },
  loadingText: {
    fontSize: 16,
    color: theme.colors.onSurfaceVariant,
  },
});

export default SplashScreen;
