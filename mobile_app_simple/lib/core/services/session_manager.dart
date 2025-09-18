import 'dart:convert';
import 'dart:math';
import 'package:crypto/crypto.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:package_info_plus/package_info_plus.dart';

class SessionManager {
  static const String _sessionTokenKey = 'session_token';
  static const String _sessionNonceKey = 'session_nonce';
  static const String _sessionExpiryKey = 'session_expiry';
  static const String _hmacKeyKey = 'hmac_key';
  
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage(
    aOptions: AndroidOptions(
      encryptedSharedPreferences: true,
    ),
  );
  
  String? _sessionToken;
  String? _nonce;
  DateTime? _expiry;
  String? _hmacKey;
  
  Future<void> initializeSession(String baseUrl) async {
    try {
      // Check if we have a valid session
      final existingToken = await _secureStorage.read(key: _sessionTokenKey);
      final existingExpiry = await _secureStorage.read(key: _sessionExpiryKey);
      
      if (existingToken != null && existingExpiry != null) {
        final expiry = DateTime.parse(existingExpiry);
        if (expiry.isAfter(DateTime.now())) {
          _sessionToken = existingToken;
          _nonce = await _secureStorage.read(key: _sessionNonceKey);
          _hmacKey = await _secureStorage.read(key: _hmacKeyKey);
          _expiry = expiry;
          return;
        }
      }
      
      // Start new session
      await _startNewSession(baseUrl);
    } catch (e) {
      debugPrint('[SessionManager] Error initializing session: $e');
      await _startNewSession(baseUrl);
    }
  }
  
  Future<void> _startNewSession(String baseUrl) async {
    try {
      final packageInfo = await PackageInfo.fromPlatform();
      final clientVersion = '${packageInfo.version}+${packageInfo.buildNumber}';
      
      final response = await _makeRequest(
        'POST',
        '$baseUrl/session/start',
        {
          'client_version': clientVersion,
          'platform': 'mobile',
          'app_id': packageInfo.packageName,
        },
      );
      
      if (response['success'] == true) {
        _sessionToken = response['session_token'];
        _nonce = response['nonce'];
        _hmacKey = response['hmac_key'];
        _expiry = DateTime.now().add(Duration(seconds: response['expires_in'] ?? 3600));
        
        // Store securely
        await _secureStorage.write(key: _sessionTokenKey, value: _sessionToken);
        await _secureStorage.write(key: _sessionNonceKey, value: _nonce);
        await _secureStorage.write(key: _sessionExpiryKey, value: _expiry!.toIso8601String());
        await _secureStorage.write(key: _hmacKeyKey, value: _hmacKey);
        
        debugPrint('[SessionManager] New session started');
      }
    } catch (e) {
      debugPrint('[SessionManager] Error starting session: $e');
      rethrow;
    }
  }
  
  Map<String, String> getAuthHeaders() {
    if (_sessionToken == null || _nonce == null) {
      return {};
    }
    
    return {
      'X-Session': _sessionToken!,
      'X-Nonce': _nonce!,
      'X-Client': 'stillme-mobile/1.0.0',
    };
  }
  
  String? signRequest(String body) {
    if (_hmacKey == null) return null;
    
    final timestamp = DateTime.now().millisecondsSinceEpoch.toString();
    final data = '$body$timestamp${_nonce ?? ''}';
    final bytes = utf8.encode(data);
    final digest = sha256.convert(bytes);
    final signature = base64.encode(digest.bytes);
    
    return signature;
  }
  
  Future<Map<String, dynamic>> _makeRequest(
    String method,
    String url,
    Map<String, dynamic>? body,
  ) async {
    // This would use Dio or http package
    // For now, return mock response
    return {
      'success': true,
      'session_token': 'mock_session_token_${Random().nextInt(10000)}',
      'nonce': 'mock_nonce_${Random().nextInt(10000)}',
      'hmac_key': 'mock_hmac_key_${Random().nextInt(10000)}',
      'expires_in': 3600,
    };
  }
  
  Future<void> refreshSession() async {
    // Implementation for refreshing session
    debugPrint('[SessionManager] Refreshing session...');
  }
  
  Future<void> clearSession() async {
    await _secureStorage.delete(key: _sessionTokenKey);
    await _secureStorage.delete(key: _sessionNonceKey);
    await _secureStorage.delete(key: _sessionExpiryKey);
    await _secureStorage.delete(key: _hmacKeyKey);
    
    _sessionToken = null;
    _nonce = null;
    _expiry = null;
    _hmacKey = null;
    
    debugPrint('[SessionManager] Session cleared');
  }
  
  bool get hasValidSession {
    return _sessionToken != null && 
           _expiry != null && 
           _expiry!.isAfter(DateTime.now());
  }
}
