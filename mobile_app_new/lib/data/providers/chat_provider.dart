import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../../core/models/chat_models.dart';
import '../repositories/chat_repository.dart';

// Chat state provider
final chatProvider = StateNotifierProvider<ChatNotifier, ChatState>((ref) {
  final repository = ref.watch(chatRepositoryProvider);
  return ChatNotifier(repository);
});

// Session metrics provider
final sessionMetricsProvider = StateNotifierProvider<SessionMetricsNotifier, SessionMetrics>((ref) {
  return SessionMetricsNotifier();
});

// Telemetry provider
final telemetryProvider = StateNotifierProvider<TelemetryNotifier, List<TelemetryData>>((ref) {
  return TelemetryNotifier();
});

class ChatState {
  final List<ChatMessage> messages;
  final bool isLoading;
  final String? error;
  final String sessionId;

  const ChatState({
    this.messages = const [],
    this.isLoading = false,
    this.error,
    required this.sessionId,
  });

  ChatState copyWith({
    List<ChatMessage>? messages,
    bool? isLoading,
    String? error,
    String? sessionId,
  }) {
    return ChatState(
      messages: messages ?? this.messages,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      sessionId: sessionId ?? this.sessionId,
    );
  }
}

class ChatNotifier extends StateNotifier<ChatState> {
  final ChatRepository _repository;
  final String _sessionId = const Uuid().v4();

  ChatNotifier(this._repository) : super(ChatState(sessionId: const Uuid().v4()));

  Future<void> sendMessage(String content, {ChatMetadata? metadata}) async {
    // Add user message
    final userMessage = ChatMessage(
      id: const Uuid().v4(),
      content: content,
      role: MessageRole.user,
      timestamp: DateTime.now(),
    );

    state = state.copyWith(
      messages: [...state.messages, userMessage],
      isLoading: true,
      error: null,
    );

    try {
      // Send to server
      final response = await _repository.sendMessage(
        message: content,
        metadata: metadata,
      );

      // Add assistant response
      final assistantMessage = ChatMessage(
        id: const Uuid().v4(),
        content: response.text,
        role: MessageRole.assistant,
        timestamp: DateTime.now(),
        model: response.model,
        usage: response.usage,
        latencyMs: response.latencyMs,
        costEstimateUsd: response.costEstimateUsd,
        routing: response.routing,
        safety: response.safety,
      );

      state = state.copyWith(
        messages: [...state.messages, assistantMessage],
        isLoading: false,
      );

      // Update telemetry
      _updateTelemetry(response);
      _updateSessionMetrics(response);

    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  void _updateTelemetry(ChatResponse response) {
    // This would update the telemetry provider
    // Implementation depends on how you want to handle telemetry data
  }

  void _updateSessionMetrics(ChatResponse response) {
    // This would update the session metrics provider
    // Implementation depends on how you want to handle session data
  }

  void clearMessages() {
    state = state.copyWith(
      messages: [],
      error: null,
    );
  }

  void retryLastMessage() {
    if (state.messages.isNotEmpty) {
      final lastUserMessage = state.messages
          .where((m) => m.role == MessageRole.user)
          .lastOrNull;
      
      if (lastUserMessage != null) {
        sendMessage(lastUserMessage.content);
      }
    }
  }

  void setTyping(bool isTyping) {
    if (state.messages.isNotEmpty) {
      final lastMessage = state.messages.last;
      if (lastMessage.role == MessageRole.assistant) {
        final updatedMessage = lastMessage.copyWith(isTyping: isTyping);
        final updatedMessages = [...state.messages];
        updatedMessages[updatedMessages.length - 1] = updatedMessage;
        
        state = state.copyWith(messages: updatedMessages);
      }
    }
  }
}

class SessionMetricsNotifier extends StateNotifier<SessionMetrics> {
  SessionMetricsNotifier() : super(SessionMetrics(sessionStart: DateTime.now()));

  void updateMetrics(ChatResponse response) {
    final usage = response.usage;
    final latency = response.latencyMs ?? 0;
    final cost = response.costEstimateUsd ?? 0.0;
    final model = response.model ?? 'unknown';

    state = state.copyWith(
      totalMessages: state.totalMessages + 1,
      totalTokens: state.totalTokens + (usage?.totalTokens ?? 0),
      totalCost: state.totalCost + cost,
      averageLatency: _calculateAverageLatency(latency),
      modelsUsed: _updateModelsUsed(model),
    );
  }

  int _calculateAverageLatency(int newLatency) {
    if (state.totalMessages == 0) return newLatency;
    
    final totalLatency = state.averageLatency * state.totalMessages + newLatency;
    return totalLatency ~/ (state.totalMessages + 1);
  }

  List<String> _updateModelsUsed(String model) {
    final models = List<String>.from(state.modelsUsed);
    if (!models.contains(model)) {
      models.add(model);
    }
    return models;
  }

  void reset() {
    state = SessionMetrics(sessionStart: DateTime.now());
  }
}

class TelemetryNotifier extends StateNotifier<List<TelemetryData>> {
  TelemetryNotifier() : super([]);

  void addTelemetry(TelemetryData data) {
    state = [...state, data];
    
    // Keep only last 100 telemetry entries
    if (state.length > 100) {
      state = state.skip(state.length - 100).toList();
    }
  }

  void clearTelemetry() {
    state = [];
  }

  List<TelemetryData> getRecentTelemetry({int count = 10}) {
    return state.length > count 
        ? state.skip(state.length - count).toList()
        : state;
  }

  double getAverageLatency() {
    if (state.isEmpty) return 0.0;
    
    final totalLatency = state.fold(0, (sum, data) => sum + data.latencyMs);
    return totalLatency / state.length;
  }

  double getTotalCost() {
    return state.fold(0.0, (sum, data) => sum + data.costEstimateUsd);
  }

  int getTotalTokens() {
    return state.fold(0, (sum, data) => sum + data.usage.totalTokens);
  }

  Map<String, int> getModelUsage() {
    final usage = <String, int>{};
    for (final data in state) {
      usage[data.model] = (usage[data.model] ?? 0) + 1;
    }
    return usage;
  }
}
