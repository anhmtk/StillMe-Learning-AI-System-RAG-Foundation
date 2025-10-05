// StillMe Mobile - Theme Configuration
import { MD3LightTheme, MD3DarkTheme } from 'react-native-paper';

export const lightTheme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary: '#6750A4',
    secondary: '#625B71',
    tertiary: '#7D5260',
    surface: '#FFFBFE',
    surfaceVariant: '#E7E0EC',
    background: '#FFFBFE',
    error: '#BA1A1A',
    onPrimary: '#FFFFFF',
    onSecondary: '#FFFFFF',
    onTertiary: '#FFFFFF',
    onSurface: '#1C1B1F',
    onSurfaceVariant: '#49454F',
    onBackground: '#1C1B1F',
    onError: '#FFFFFF',
    outline: '#79747E',
    outlineVariant: '#CAC4D0',
    shadow: '#000000',
    scrim: '#000000',
    inverseSurface: '#313033',
    inverseOnSurface: '#F4EFF4',
    inversePrimary: '#D0BCFF',
    elevation: {
      level0: 'transparent',
      level1: '#F7F2FA',
      level2: '#F1ECF4',
      level3: '#EBE6ED',
      level4: '#E9E4EB',
      level5: '#E6E1E8',
    },
  },
};

export const darkTheme = {
  ...MD3DarkTheme,
  colors: {
    ...MD3DarkTheme.colors,
    primary: '#D0BCFF',
    secondary: '#CCC2DC',
    tertiary: '#EFB8C8',
    surface: '#141218',
    surfaceVariant: '#49454F',
    background: '#141218',
    error: '#F2B8B5',
    onPrimary: '#381E72',
    onSecondary: '#332D41',
    onTertiary: '#492532',
    onSurface: '#E6E0E9',
    onSurfaceVariant: '#CAC4D0',
    onBackground: '#E6E0E9',
    onError: '#601410',
    outline: '#938F99',
    outlineVariant: '#49454F',
    shadow: '#000000',
    scrim: '#000000',
    inverseSurface: '#E6E0E9',
    inverseOnSurface: '#313033',
    inversePrimary: '#6750A4',
    elevation: {
      level0: 'transparent',
      level1: '#1C1B1F',
      level2: '#211F26',
      level3: '#27242B',
      level4: '#2A2730',
      level5: '#2E2A35',
    },
  },
};

// Default theme (will be set based on user preference)
export const theme = lightTheme;
