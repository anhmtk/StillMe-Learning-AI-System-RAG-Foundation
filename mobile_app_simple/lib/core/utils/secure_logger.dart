import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';

class SecureLogger {
  static const List<String> _sensitiveKeys = [
    'password', 'passcode', 'token', 'key', 'secret', 'auth',
    'api_key', 'apikey', 'authorization', 'bearer', 'session',
    'cookie', 'credential', 'private', 'sensitive'
  ];
  
  static const List<String> _sensitiveHeaders = [
    'authorization', 'x-api-key', 'x-auth-token', 'x-session',
    'cookie', 'set-cookie', 'x-csrf-token'
  ];
  
  static bool get _shouldLog => kDebugMode;
  
  static void logRequest(RequestOptions options) {
    if (!_shouldLog) return;
    
    debugPrint('[SecureLogger] ===== REQUEST =====');
    debugPrint('[SecureLogger] ${options.method} ${options.uri}');
    debugPrint('[SecureLogger] Headers: ${_redactHeaders(options.headers)}');
    
    if (options.data != null) {
      debugPrint('[SecureLogger] Body: ${_redactSensitiveData(options.data)}');
    }
    debugPrint('[SecureLogger] ===================');
  }
  
  static void logResponse(Response response) {
    if (!_shouldLog) return;
    
    debugPrint('[SecureLogger] ===== RESPONSE =====');
    debugPrint('[SecureLogger] Status: ${response.statusCode}');
    debugPrint('[SecureLogger] Headers: ${_redactHeaders(response.headers.map)}');
    debugPrint('[SecureLogger] Data: ${_redactSensitiveData(response.data)}');
    debugPrint('[SecureLogger] ====================');
  }
  
  static void logError(DioException error) {
    if (!_shouldLog) return;
    
    debugPrint('[SecureLogger] ===== ERROR =====');
    debugPrint('[SecureLogger] Type: ${error.type}');
    debugPrint('[SecureLogger] Message: ${error.message}');
    debugPrint('[SecureLogger] Response: ${_redactSensitiveData(error.response?.data)}');
    debugPrint('[SecureLogger] =================');
  }
  
  static Map<String, dynamic> _redactHeaders(Map<String, dynamic> headers) {
    final redacted = Map<String, dynamic>.from(headers);
    
    for (final key in redacted.keys) {
      final lowerKey = key.toLowerCase();
      if (_sensitiveHeaders.any((sensitive) => lowerKey.contains(sensitive))) {
        redacted[key] = '[REDACTED]';
      }
    }
    
    return redacted;
  }
  
  static dynamic _redactSensitiveData(dynamic data) {
    if (data == null) return data;
    
    if (data is String) {
      try {
        final jsonData = json.decode(data);
        return _redactJson(jsonData);
      } catch (e) {
        return data;
      }
    }
    
    if (data is Map<String, dynamic>) {
      return _redactJson(data);
    }
    
    if (data is List) {
      return data.map((item) => _redactSensitiveData(item)).toList();
    }
    
    return data;
  }
  
  static Map<String, dynamic> _redactJson(Map<String, dynamic> json) {
    final redacted = Map<String, dynamic>.from(json);
    
    for (final key in redacted.keys) {
      final lowerKey = key.toLowerCase();
      
      if (_sensitiveKeys.any((sensitive) => lowerKey.contains(sensitive))) {
        redacted[key] = '[REDACTED]';
      } else if (redacted[key] is Map<String, dynamic>) {
        redacted[key] = _redactJson(redacted[key] as Map<String, dynamic>);
      } else if (redacted[key] is List) {
        redacted[key] = (redacted[key] as List).map((item) {
          if (item is Map<String, dynamic>) {
            return _redactJson(item);
          }
          return item;
        }).toList();
      }
    }
    
    return redacted;
  }
  
  static void logTelemetry(String event, Map<String, dynamic> data) {
    if (!_shouldLog) return;
    
    debugPrint('[SecureLogger] ===== TELEMETRY =====');
    debugPrint('[SecureLogger] Event: $event');
    debugPrint('[SecureLogger] Data: ${_redactSensitiveData(data)}');
    debugPrint('[SecureLogger] =====================');
  }
}
