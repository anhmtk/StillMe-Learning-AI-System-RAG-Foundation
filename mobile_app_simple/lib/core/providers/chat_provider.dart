import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/chat_models.dart';

class ChatNotifier extends StateNotifier<List<ChatMessage>> {
  ChatNotifier() : super([]);

  void addMessage(ChatMessage message) {
    state = [...state, message];
  }

  void addUserMessage(String content) {
    final message = ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      content: content,
      role: MessageRole.user,
      timestamp: DateTime.now(),
    );
    addMessage(message);
  }

  void addAIMessage(String content, {String? model, int? latencyMs}) {
    final message = ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      content: content,
      role: MessageRole.assistant,
      timestamp: DateTime.now(),
      model: model,
      latencyMs: latencyMs,
    );
    addMessage(message);
  }

  void clearChat() {
    state = [];
  }
}

final chatProvider = StateNotifierProvider<ChatNotifier, List<ChatMessage>>((ref) {
  return ChatNotifier();
});
