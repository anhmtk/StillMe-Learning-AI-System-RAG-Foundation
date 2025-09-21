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
          debugPrint('[Dio] REQUEST: ${options.method} ${options.uri}');
          debugPrint('[Dio] HEADERS: ${options.headers}');
          if (options.data != null) {
            debugPrint('[Dio] BODY: ${jsonEncode(options.data)}');
          }
          handler.next(options);
        },
        onResponse: (response, handler) {
          SecureLogger.logResponse(response);
          debugPrint('[Dio] RESPONSE: ${response.statusCode} ${response.requestOptions.uri}');
          debugPrint('[Dio] RESPONSE BODY: ${jsonEncode(response.data)}');
          handler.next(response);
        },
        onError: (error, handler) {
          SecureLogger.logError(error);
          debugPrint('[Dio] ERROR: ${error.message}');
          if (error.response != null) {
            debugPrint('[Dio] ERROR RESPONSE: ${error.response?.statusCode}');
            debugPrint('[Dio] ERROR BODY: ${jsonEncode(error.response?.data)}');
          }
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
            // Priority order: response -> text -> output -> choices[0].message.content
            return d['response'] ??  // StillMe VPS uses 'response'
                   d['text'] ??      // Standard text field
                   d['output'] ??    // Alternative output field
                   d['reply'] ??     // Reply field
                   d['message'] ??   // Message field
                   (d['choices'] is List && d['choices'].isNotEmpty ? 
                     (d['choices'][0]['message']?['content'] ?? d['choices'][0]['text']) : null);
          }
          return null;
        }
        
        final text = extractText(data);
        final model = data['model'] ?? data['routing']?['selected'] ?? 'unknown';
        final usage = _extractUsage(data['usage']);
        final latency = data['latency_ms'] ?? latencyMs;
        
        // If status 200 but no text found, show schema mismatch warning with available keys
        if (text == null || text.isEmpty) {
          final availableKeys = data is Map<String, dynamic> ? data.keys.toList() : ['unknown'];
          debugPrint('[ChatRepository] WARNING: Schema mismatch - no text field found in response');
          debugPrint('[ChatRepository] Available keys: $availableKeys');
          return ChatMessage(
            id: DateTime.now().millisecondsSinceEpoch.toString(),
            content: '⚠️ Unknown schema: ${availableKeys.join(", ")}',
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
      
      // Only return fallback message for network errors (timeout, 5xx, connection issues)
      final isNetworkError = e is DioException && (
        e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout ||
        e.type == DioExceptionType.sendTimeout ||
        e.type == DioExceptionType.connectionError ||
        (e.response?.statusCode != null && e.response!.statusCode! >= 500)
      );
      
      if (isNetworkError) {
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
      } else {
        // For other errors (4xx, parsing errors, etc.), show the actual error
        return ChatMessage(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          content: 'Lỗi: ${e.toString()}',
          role: MessageRole.assistant,
          timestamp: DateTime.now(),
          model: 'error',
          latencyMs: latencyMs,
          safety: const ChatSafety(
            filtered: false,
            flags: ['client_error'],
          ),
        );
      }
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
