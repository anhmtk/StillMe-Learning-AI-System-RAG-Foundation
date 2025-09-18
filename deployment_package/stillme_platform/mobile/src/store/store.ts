// StillMe Mobile - Redux Store Configuration
import { configureStore, combineReducers } from '@reduxjs/toolkit';
import { persistStore, persistReducer } from 'redux-persist';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Reducers
import appReducer from './slices/appSlice';
import authReducer from './slices/authSlice';
import chatReducer from './slices/chatSlice';
import notificationReducer from './slices/notificationSlice';
import settingsReducer from './slices/settingsSlice';

// Persist config
const persistConfig = {
  key: 'root',
  storage: AsyncStorage,
  whitelist: ['auth', 'settings', 'app'], // Only persist these reducers
};

const rootReducer = combineReducers({
  app: appReducer,
  auth: authReducer,
  chat: chatReducer,
  notifications: notificationReducer,
  settings: settingsReducer,
});

const persistedReducer = persistReducer(persistConfig, rootReducer);

// Store configuration
export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
  devTools: __DEV__,
});

export const persistor = persistStore(store);

// Types
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
