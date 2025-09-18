import 'dart:convert';
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../core/models/chat_models.dart';
import '../core/utils/raw_json_logger.dart';
import '../core/utils/secure_logger.dart';
import '../core/services/session_manager.dart';

class ChatRepository {
  late final Dio _dio;
  final String baseUrl;
  final int timeoutMs;
  final SessionManager _sessionManager = SessionManager();

  ChatRepository({
    required this.baseUrl,
    this.timeoutMs = 25000,
  }) {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 20),
      receiveTimeout: const Duration(seconds: 20),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        // API keys handled server-side for security
        'X-Client-Version': '1.0.0',
        'X-Platform': 'mobile',
      },
    ));

    // Add secure logging interceptor (only in debug mode)
    if (kDebugMode) {
      _dio.interceptors.add(InterceptorsWrapper(
        onRequest: (options, handler) {
          SecureLogger.logRequest(options);
          handler.next(options);
        },
        onResponse: (response, handler) {
          SecureLogger.logResponse(response);
          handler.next(response);
        },
        onError: (error, handler) {
          SecureLogger.logError(error);
          handler.next(error);
        },
      ));
    }
  }

  Future<ChatMessage> sendMessage(String message) async {
    final startTime = DateTime.now();
    
    try {
      // Standardized request body
      final body = {
        "message": message,
        "session_id": "mobile_${DateTime.now().millisecondsSinceEpoch}",
        "metadata": {
          "persona": "assistant",
          "language": "vi",
          "founder_command": false,
          "debug": true
        }
      };
      
      debugPrint('[ChatRepository] Sending request to: $baseUrl/chat');
      debugPrint('[ChatRepository] Request body: ${jsonEncode(body)}');
      
      final response = await _dio.post('/chat', data: body);

      final endTime = DateTime.now();
      final latencyMs = endTime.difference(startTime).inMilliseconds;

      if (response.statusCode == 200) {
        final data = response.data;
        
        debugPrint('[ChatRepository] Response status: ${response.statusCode}');
        debugPrint('[ChatRepository] Response body: ${jsonEncode(data)}');
        
        // Log raw JSON for analysis
        await RawJsonLogger.logChatResponse(
          url: '$baseUrl/chat',
          requestBody: body,
          statusCode: response.statusCode!,
          responseBody: data,
          latencyMs: latencyMs,
        );
        
        // Extract message text with comprehensive fallback priority
        String? extractText(dynamic d) {
          if (d == null) return null;
          if (d is Map<String, dynamic>) {
            return d['response'] ??  // StillMe VPS uses 'response'
                   d['text'] ??
                   d['reply'] ??
                   d['message'] ??
                   (d['choices'] is List && d['choices'].isNotEmpty ? d['choices'][0]['text'] : null) ??
                   (d['choices']?[0]?['message']?['content']);
          }
          return null;
        }
        
        final text = extractText(data);
        final model = data['model'] ?? data['routing']?['selected'] ?? 'unknown';
        final usage = _extractUsage(data['usage']);
        final latency = data['latency_ms'] ?? latencyMs;
        
        // Check if this is a placeholder response
        final isPlaceholder = _isPlaceholderResponse(data, text);
        
        // If status 200 but no text found, show schema mismatch warning
        if (text == null || text.isEmpty) {
          debugPrint('[ChatRepository] WARNING: Schema mismatch - no text field found in response');
          return ChatMessage(
            id: DateTime.now().millisecondsSinceEpoch.toString(),
            content: '⚠️ Schema mismatch: Server response không có trường text. Raw: ${jsonEncode(data)}',
            role: MessageRole.assistant,
            timestamp: DateTime.now(),
            model: model,
            usage: usage,
            latencyMs: latency,
            costEstimateUsd: data['cost_estimate_usd']?.toDouble(),
            safety: const ChatSafety(
              filtered: false,
              flags: ['schema_mismatch'],
            ),
          );
        }
        
        // If placeholder response, show warning
        if (isPlaceholder) {
          debugPrint('[ChatRepository] WARNING: Placeholder response detected');
          return ChatMessage(
            id: DateTime.now().millisecondsSinceEpoch.toString(),
            content: '🚨 Gateway in placeholder mode – not a real LLM response\n\n$text',
            role: MessageRole.assistant,
            timestamp: DateTime.now(),
            model: 'placeholder',
            usage: usage,
            latencyMs: latency,
            costEstimateUsd: data['cost_estimate_usd']?.toDouble(),
            safety: const ChatSafety(
              filtered: false,
              flags: ['placeholder_mode'],
            ),
          );
        }

        return ChatMessage(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          content: text,
          role: MessageRole.assistant,
          timestamp: DateTime.now(),
          model: model,
          usage: usage,
          latencyMs: latency,
          costEstimateUsd: data['cost_estimate_usd']?.toDouble(),
        );
      } else {
        throw Exception('Server returned ${response.statusCode}');
      }
    } catch (e) {
      final endTime = DateTime.now();
      final latencyMs = endTime.difference(startTime).inMilliseconds;
      
      debugPrint('[ChatRepository] Error: $e');
      
      // Return fallback message only on real failure
      return ChatMessage(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        content: 'Xin lỗi, tôi không thể kết nối đến server. Vui lòng kiểm tra kết nối mạng.',
        role: MessageRole.assistant,
        timestamp: DateTime.now(),
        model: 'offline',
        latencyMs: latencyMs,
        safety: const ChatSafety(
          filtered: false,
          flags: ['network_error'],
        ),
      );
    }
  }

  // Helper method to extract usage data safely
  ChatUsage? _extractUsage(dynamic usageData) {
    if (usageData == null) return null;
    if (usageData is Map<String, dynamic>) {
      return ChatUsage(
        promptTokens: usageData['prompt_tokens'] ?? 0,
        completionTokens: usageData['completion_tokens'] ?? 0,
        totalTokens: usageData['total_tokens'] ?? 0,
      );
    }
    return null;
  }
  
  // Helper method to detect placeholder responses
  bool _isPlaceholderResponse(Map<String, dynamic> data, String? text) {
    final model = data['model']?.toString().toLowerCase() ?? '';
    final textLower = text?.toLowerCase() ?? '';
    
    return model.contains('placeholder') || 
           textLower.contains('đang trong quá trình triển khai') ||
           textLower.contains('hiện tại mình đang') ||
           textLower.contains('rất vui được làm quen') ||
           textLower.contains('mình đã nhận được tin nhắn của bạn');
  }

  Future<Map<String, dynamic>> testConnection() async {
    try {
      final response = await _dio.get('/health');
      return {
        'success': response.statusCode == 200,
        'status': response.statusCode == 200 ? 'Connected' : 'Error',
        'message': response.statusCode == 200 ? 'Server is running' : 'Server error',
        'responseTime': response.headers['x-response-time']?.first ?? 'N/A',
      };
    } catch (e) {
      return {
        'success': false,
        'status': 'Failed',
        'message': 'Connection failed: ${e.toString()}',
      };
    }
  }
}
