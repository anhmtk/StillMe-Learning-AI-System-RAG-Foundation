import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../core/config/app_config_service.dart';

// Founder mode provider
final founderModeProvider = StateNotifierProvider<FounderModeNotifier, FounderModeState>((ref) {
  final config = ref.watch(appConfigProvider).value;
  return FounderModeNotifier(config);
});

// Founder passcode provider
final founderPasscodeProvider = StateNotifierProvider<FounderPasscodeNotifier, String>((ref) {
  final config = ref.watch(appConfigProvider).value;
  return FounderPasscodeNotifier(config?.security.founderPasscode ?? '0000');
});

class FounderModeState {
  final bool isEnabled;
  final bool isAuthenticated;
  final String? error;
  final DateTime? lastAccess;

  const FounderModeState({
    this.isEnabled = false,
    this.isAuthenticated = false,
    this.error,
    this.lastAccess,
  });

  FounderModeState copyWith({
    bool? isEnabled,
    bool? isAuthenticated,
    String? error,
    DateTime? lastAccess,
  }) {
    return FounderModeState(
      isEnabled: isEnabled ?? this.isEnabled,
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      error: error,
      lastAccess: lastAccess ?? this.lastAccess,
    );
  }
}

class FounderModeNotifier extends StateNotifier<FounderModeState> {
  final AppConfig? _config;
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();

  FounderModeNotifier(this._config) : super(const FounderModeState()) {
    _loadFounderMode();
  }

  Future<void> _loadFounderMode() async {
    try {
      final isEnabled = await _secureStorage.read(key: 'founder_mode_enabled') == 'true';
      final lastAccess = await _secureStorage.read(key: 'founder_mode_last_access');
      
      state = state.copyWith(
        isEnabled: isEnabled,
        lastAccess: lastAccess != null ? DateTime.parse(lastAccess) : null,
      );
    } catch (e) {
      state = state.copyWith(error: 'Failed to load founder mode: $e');
    }
  }

  Future<bool> authenticate(String passcode) async {
    try {
      final correctPasscode = _config?.security.founderPasscode ?? '0000';
      
      if (passcode == correctPasscode) {
        await _secureStorage.write(key: 'founder_mode_enabled', value: 'true');
        await _secureStorage.write(
          key: 'founder_mode_last_access', 
          value: DateTime.now().toIso8601String(),
        );
        
        state = state.copyWith(
          isAuthenticated: true,
          isEnabled: true,
          lastAccess: DateTime.now(),
          error: null,
        );
        
        return true;
      } else {
        state = state.copyWith(
          isAuthenticated: false,
          error: 'Invalid passcode',
        );
        return false;
      }
    } catch (e) {
      state = state.copyWith(
        isAuthenticated: false,
        error: 'Authentication failed: $e',
      );
      return false;
    }
  }

  Future<void> enableFounderMode() async {
    try {
      await _secureStorage.write(key: 'founder_mode_enabled', value: 'true');
      await _secureStorage.write(
        key: 'founder_mode_last_access', 
        value: DateTime.now().toIso8601String(),
      );
      
      state = state.copyWith(
        isEnabled: true,
        lastAccess: DateTime.now(),
        error: null,
      );
    } catch (e) {
      state = state.copyWith(error: 'Failed to enable founder mode: $e');
    }
  }

  Future<void> disableFounderMode() async {
    try {
      await _secureStorage.delete(key: 'founder_mode_enabled');
      await _secureStorage.delete(key: 'founder_mode_last_access');
      
      state = state.copyWith(
        isEnabled: false,
        isAuthenticated: false,
        lastAccess: null,
        error: null,
      );
    } catch (e) {
      state = state.copyWith(error: 'Failed to disable founder mode: $e');
    }
  }

  Future<void> logout() async {
    state = state.copyWith(
      isAuthenticated: false,
      error: null,
    );
  }

  bool isSessionValid() {
    if (!state.isEnabled || state.lastAccess == null) return false;
    
    final sessionTimeout = _config?.security.sessionTimeout ?? 3600;
    final now = DateTime.now();
    final timeDiff = now.difference(state.lastAccess!).inSeconds;
    
    return timeDiff < sessionTimeout;
  }

  Future<void> refreshSession() async {
    if (state.isEnabled) {
      await _secureStorage.write(
        key: 'founder_mode_last_access', 
        value: DateTime.now().toIso8601String(),
      );
      
      state = state.copyWith(lastAccess: DateTime.now());
    }
  }
}

class FounderPasscodeNotifier extends StateNotifier<String> {
  final String _defaultPasscode;

  FounderPasscodeNotifier(this._defaultPasscode) : super(_defaultPasscode);

  void updatePasscode(String newPasscode) {
    if (newPasscode.isNotEmpty && newPasscode.length >= 4) {
      state = newPasscode;
    }
  }

  void resetToDefault() {
    state = _defaultPasscode;
  }

  bool validatePasscode(String passcode) {
    return passcode == state;
  }
}
