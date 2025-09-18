import 'dart:convert';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:flutter/foundation.dart';

class RawJsonLogger {
  static const String _fileName = 'last_chat_raw.json';
  
  static Future<void> logChatResponse({
    required String url,
    required Map<String, dynamic> requestBody,
    required int statusCode,
    required Map<String, dynamic> responseBody,
    required int latencyMs,
  }) async {
    try {
      final logData = {
        'timestamp': DateTime.now().toIso8601String(),
        'url': url,
        'request': {
          'body': requestBody,
          'headers': {'Content-Type': 'application/json'},
        },
        'response': {
          'status_code': statusCode,
          'body': responseBody,
          'latency_ms': latencyMs,
        },
        'analysis': {
          'is_placeholder': _isPlaceholderResponse(responseBody),
          'model': responseBody['model'] ?? 'unknown',
          'has_text': _hasTextResponse(responseBody),
        }
      };
      
      // Log to console
      debugPrint('[RawJsonLogger] ===== CHAT RESPONSE =====');
      debugPrint('[RawJsonLogger] URL: $url');
      debugPrint('[RawJsonLogger] Status: $statusCode');
      debugPrint('[RawJsonLogger] Latency: ${latencyMs}ms');
      debugPrint('[RawJsonLogger] Model: ${responseBody['model'] ?? 'unknown'}');
      debugPrint('[RawJsonLogger] Is Placeholder: ${_isPlaceholderResponse(responseBody)}');
      debugPrint('[RawJsonLogger] Raw Response: ${jsonEncode(responseBody)}');
      debugPrint('[RawJsonLogger] =========================');
      
      // Save to file
      if (kDebugMode) {
        final directory = await getApplicationDocumentsDirectory();
        final file = File('${directory.path}/$_fileName');
        await file.writeAsString(jsonEncode(logData));
        debugPrint('[RawJsonLogger] Saved to: ${file.path}');
      }
    } catch (e) {
      debugPrint('[RawJsonLogger] Error logging: $e');
    }
  }
  
  static bool _isPlaceholderResponse(Map<String, dynamic> response) {
    final model = response['model']?.toString().toLowerCase() ?? '';
    final text = response['response']?.toString().toLowerCase() ?? 
                 response['text']?.toString().toLowerCase() ?? '';
    
    return model.contains('placeholder') || 
           text.contains('đang trong quá trình triển khai') ||
           text.contains('hiện tại mình đang') ||
           text.contains('rất vui được làm quen');
  }
  
  static bool _hasTextResponse(Map<String, dynamic> response) {
    return response['response'] != null ||
           response['text'] != null ||
           response['message'] != null ||
           (response['choices'] != null && response['choices'].isNotEmpty);
  }
  
  static Future<String?> getLastRawJson() async {
    try {
      final directory = await getApplicationDocumentsDirectory();
      final file = File('${directory.path}/$_fileName');
      if (await file.exists()) {
        return await file.readAsString();
      }
    } catch (e) {
      debugPrint('[RawJsonLogger] Error reading file: $e');
    }
    return null;
  }
}
