import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../../core/models/chat_models.dart';
import '../../core/config/app_config_service.dart';
import '../services/api_service.dart';

final chatRepositoryProvider = Provider<ChatRepository>((ref) {
  final apiService = ref.watch(apiServiceProvider);
  final config = ref.watch(appConfigProvider).value;
  return ChatRepository(apiService, config);
});

class ChatRepository {
  final ApiService _apiService;
  final AppConfig? _config;
  final String _sessionId = const Uuid().v4();

  ChatRepository(this._apiService, this._config);

  Future<ChatResponse> sendMessage({
    required String message,
    ChatMetadata? metadata,
  }) async {
    try {
      final request = ChatRequest(
        message: message,
        sessionId: _sessionId,
        metadata: metadata ?? const ChatMetadata(),
      );

      final response = await _apiService.post(
        '/chat',
        data: request.toJson(),
      );

      // Handle different response formats from the server
      return _adaptResponse(response.data);
    } catch (e) {
      throw ChatException('Failed to send message: $e');
    }
  }

  Future<HealthResponse> checkHealth() async {
    try {
      final response = await _apiService.get('/health');
      return HealthResponse.fromJson(response.data);
    } catch (e) {
      throw ChatException('Failed to check health: $e');
    }
  }

  ChatResponse _adaptResponse(Map<String, dynamic> data) {
    // Adapter to handle different server response formats
    // This ensures compatibility with the current VPS server format
    
    String text = '';
    String? model;
    ChatUsage? usage;
    int? latencyMs;
    double? costEstimateUsd;
    ChatRouting? routing;
    ChatSafety? safety;

    // Handle current VPS server format
    if (data.containsKey('response')) {
      text = data['response'] ?? '';
    } else if (data.containsKey('text')) {
      text = data['text'] ?? '';
    } else if (data.containsKey('message')) {
      text = data['message'] ?? '';
    }

    // Extract model information
    if (data.containsKey('model')) {
      model = data['model'];
    }

    // Extract usage information
    if (data.containsKey('usage')) {
      final usageData = data['usage'];
      if (usageData is Map<String, dynamic>) {
        usage = ChatUsage.fromJson(usageData);
      }
    }

    // Extract latency
    if (data.containsKey('latency_ms')) {
      latencyMs = data['latency_ms'];
    } else if (data.containsKey('latencyMs')) {
      latencyMs = data['latencyMs'];
    }

    // Extract cost estimate
    if (data.containsKey('cost_estimate_usd')) {
      costEstimateUsd = data['cost_estimate_usd']?.toDouble();
    } else if (data.containsKey('costEstimateUsd')) {
      costEstimateUsd = data['costEstimateUsd']?.toDouble();
    }

    // Extract routing information
    if (data.containsKey('routing')) {
      final routingData = data['routing'];
      if (routingData is Map<String, dynamic>) {
        routing = ChatRouting.fromJson(routingData);
      }
    }

    // Extract safety information
    if (data.containsKey('safety')) {
      final safetyData = data['safety'];
      if (safetyData is Map<String, dynamic>) {
        safety = ChatSafety.fromJson(safetyData);
      }
    }

    // If no usage data, create default based on text length
    usage ??= ChatUsage(
      promptTokens: _estimateTokens(text),
      completionTokens: _estimateTokens(text),
      totalTokens: _estimateTokens(text) * 2,
    );

    // If no latency, use default
    latencyMs ??= 500;

    // If no cost estimate, calculate based on tokens
    costEstimateUsd ??= _estimateCost(usage!.totalTokens);

    // If no routing, use default
    routing ??= const ChatRouting(
      selected: 'gemma2:2b',
      candidates: ['gemma2:2b', 'deepseek-coder-6.7b'],
    );

    // If no safety, use default
    safety ??= const ChatSafety(
      filtered: false,
      flags: [],
    );

    return ChatResponse(
      text: text,
      model: model,
      usage: usage,
      latencyMs: latencyMs,
      costEstimateUsd: costEstimateUsd,
      routing: routing,
      safety: safety,
    );
  }

  int _estimateTokens(String text) {
    // Simple token estimation: ~4 characters per token
    return (text.length / 4).ceil();
  }

  double _estimateCost(int tokens) {
    // Rough cost estimation: $0.0001 per 1K tokens
    return (tokens / 1000) * 0.0001;
  }
}

class ChatException implements Exception {
  final String message;
  ChatException(this.message);

  @override
  String toString() => 'ChatException: $message';
}
