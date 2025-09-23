import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/chat_models.dart';

final appConfigProvider = FutureProvider<AppConfig>((ref) async {
  final service = AppConfigService();
  return await service.loadConfig();
});

final appConfigNotifierProvider = StateNotifierProvider<AppConfigNotifier, AppConfig?>((ref) {
  return AppConfigNotifier();
});

class AppConfigService {
  static const String _configAssetPath = 'assets/config/app_config.json';
  static const String _configKey = 'app_config_override';
  
  Future<AppConfig> loadConfig() async {
    try {
      // Load base config from assets
      final String configString = await rootBundle.loadString(_configAssetPath);
      final Map<String, dynamic> configJson = json.decode(configString);
      
      // Apply any overrides from SharedPreferences
      final prefs = await SharedPreferences.getInstance();
      final String? overrideString = prefs.getString(_configKey);
      
      if (overrideString != null) {
        final Map<String, dynamic> overrideJson = json.decode(overrideString);
        configJson.addAll(overrideJson);
      }
      
      // Apply environment variable overrides
      _applyEnvironmentOverrides(configJson);
      
      return AppConfig.fromJson(configJson);
    } catch (e) {
      // Return default config if loading fails
      return _getDefaultConfig();
    }
  }
  
  Future<void> saveConfigOverride(Map<String, dynamic> override) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_configKey, json.encode(override));
  }
  
  Future<void> clearConfigOverride() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_configKey);
  }
  
  void _applyEnvironmentOverrides(Map<String, dynamic> config) {
    // Apply BASE_URL override if provided via --dart-define
    const String? baseUrl = String.fromEnvironment('BASE_URL');
    if (baseUrl != null && baseUrl.isNotEmpty) {
      config['api'] ??= {};
      config['api']['baseUrl'] = baseUrl;
    }
    
    // Apply FOUNDER_MODE override
    const String? founderMode = String.fromEnvironment('FOUNDER_MODE');
    if (founderMode != null) {
      config['features'] ??= {};
      config['features']['founderMode'] = founderMode.toLowerCase() == 'true';
    }
    
    // Apply FOUNDER_PASSCODE override
    const String? founderPasscode = String.fromEnvironment('FOUNDER_PASSCODE');
    if (founderPasscode != null && founderPasscode.isNotEmpty) {
      config['security'] ??= {};
      config['security']['founderPasscode'] = founderPasscode;
    }
  }
  
  AppConfig _getDefaultConfig() {
    return const AppConfig(
      app: AppInfo(
        name: 'StillMe',
        version: '1.0.0',
        founder: 'Anh Nguyen',
        description: 'Personal AI Assistant',
      ),
      api: ApiConfig(
        baseUrl: 'http://160.191.89.99:21568',
        timeout: 30000,
        retryAttempts: 3,
        endpoints: ApiEndpoints(
          health: '/health',
          chat: '/chat',
          nicheRadar: '/niche-radar',
          webSearch: '/web-search',
        ),
      ),
      features: FeatureConfig(
        founderMode: false,
        telemetry: true,
        autoTranslate: false,
        safetyLevel: 'normal',
        tokenCap: 4000,
        maxLatency: 10000,
        nicheRadar: true,
        webSearch: true,
        languageDetection: true,
        performanceMetrics: true,
      ),
      ui: UiConfig(
        theme: 'dark',
        primaryColor: '#0F172A',
        secondaryColor: '#1E293B',
        accentColor: '#3B82F6',
        fontFamily: 'Inter',
        gradientColors: ['#8B5CF6', '#06B6D4'],
        animationDuration: 300,
      ),
      security: SecurityConfig(
        founderPasscode: '0000',
        enableBiometrics: false,
        sessionTimeout: 3600,
      ),
      nicheRadar: NicheRadarConfig(
        enabled: true,
        autoRefresh: false,
        refreshInterval: 300000,
        maxResults: 10,
        confidenceThreshold: 0.7,
      ),
    );
  }
}

class AppConfigNotifier extends StateNotifier<AppConfig?> {
  AppConfigNotifier() : super(null);
  
  final AppConfigService _service = AppConfigService();
  
  Future<void> loadConfig() async {
    try {
      final config = await _service.loadConfig();
      state = config;
    } catch (e) {
      // Handle error
      state = _service._getDefaultConfig();
    }
  }
  
  Future<void> updateApiConfig({
    String? baseUrl,
    int? timeout,
    int? retryAttempts,
  }) async {
    if (state == null) return;
    
    final currentConfig = state!;
    final newApiConfig = currentConfig.api.copyWith(
      baseUrl: baseUrl ?? currentConfig.api.baseUrl,
      timeout: timeout ?? currentConfig.api.timeout,
      retryAttempts: retryAttempts ?? currentConfig.api.retryAttempts,
    );
    
    final newConfig = currentConfig.copyWith(api: newApiConfig);
    state = newConfig;
    
    // Save override
    await _service.saveConfigOverride({
      'api': {
        'baseUrl': newApiConfig.baseUrl,
        'timeout': newApiConfig.timeout,
        'retryAttempts': newApiConfig.retryAttempts,
      }
    });
  }
  
  Future<void> updateFeatureConfig({
    bool? founderMode,
    bool? telemetry,
    bool? autoTranslate,
    String? safetyLevel,
    int? tokenCap,
    int? maxLatency,
  }) async {
    if (state == null) return;
    
    final currentConfig = state!;
    final newFeatureConfig = currentConfig.features.copyWith(
      founderMode: founderMode ?? currentConfig.features.founderMode,
      telemetry: telemetry ?? currentConfig.features.telemetry,
      autoTranslate: autoTranslate ?? currentConfig.features.autoTranslate,
      safetyLevel: safetyLevel ?? currentConfig.features.safetyLevel,
      tokenCap: tokenCap ?? currentConfig.features.tokenCap,
      maxLatency: maxLatency ?? currentConfig.features.maxLatency,
    );
    
    final newConfig = currentConfig.copyWith(features: newFeatureConfig);
    state = newConfig;
    
    // Save override
    await _service.saveConfigOverride({
      'features': {
        'founderMode': newFeatureConfig.founderMode,
        'telemetry': newFeatureConfig.telemetry,
        'autoTranslate': newFeatureConfig.autoTranslate,
        'safetyLevel': newFeatureConfig.safetyLevel,
        'tokenCap': newFeatureConfig.tokenCap,
        'maxLatency': newFeatureConfig.maxLatency,
      }
    });
  }
  
  Future<void> updateSecurityConfig({
    String? founderPasscode,
    bool? enableBiometrics,
    int? sessionTimeout,
  }) async {
    if (state == null) return;
    
    final currentConfig = state!;
    final newSecurityConfig = currentConfig.security.copyWith(
      founderPasscode: founderPasscode ?? currentConfig.security.founderPasscode,
      enableBiometrics: enableBiometrics ?? currentConfig.security.enableBiometrics,
      sessionTimeout: sessionTimeout ?? currentConfig.security.sessionTimeout,
    );
    
    final newConfig = currentConfig.copyWith(security: newSecurityConfig);
    state = newConfig;
    
    // Save override
    await _service.saveConfigOverride({
      'security': {
        'founderPasscode': newSecurityConfig.founderPasscode,
        'enableBiometrics': newSecurityConfig.enableBiometrics,
        'sessionTimeout': newSecurityConfig.sessionTimeout,
      }
    });
  }
  
  Future<void> resetToDefault() async {
    await _service.clearConfigOverride();
    await loadConfig();
  }
}
