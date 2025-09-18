import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/models/chat_models.dart';
import '../../../core/providers/chat_provider.dart';
import 'chat_message_bubble.dart';

class ChatMessageList extends ConsumerStatefulWidget {
  final ScrollController scrollController;
  final VoidCallback onScrollToBottom;

  const ChatMessageList({
    super.key,
    required this.scrollController,
    required this.onScrollToBottom,
  });

  @override
  ConsumerState<ChatMessageList> createState() => _ChatMessageListState();
}

class _ChatMessageListState extends ConsumerState<ChatMessageList> {
  @override
  Widget build(BuildContext context) {
    final messages = ref.watch(chatProvider);
    
    // Add welcome message if no messages
    if (messages.isEmpty) {
      final welcomeMessage = ChatMessage(
        id: 'welcome',
        content: 'Xin chào! Tôi là StillMe AI, trợ lý cá nhân của bạn. Tôi có thể giúp gì cho bạn hôm nay?',
        role: MessageRole.assistant,
        timestamp: DateTime.now().subtract(const Duration(minutes: 5)),
        model: 'gemma2:2b',
        usage: const ChatUsage(
          promptTokens: 20,
          completionTokens: 35,
          totalTokens: 55,
        ),
        latencyMs: 840,
        costEstimateUsd: 0.0008,
        routing: const ChatRouting(
          selected: 'gemma2:2b',
          candidates: ['gemma2:2b', 'deepseek-coder-6.7b'],
        ),
        safety: const ChatSafety(
          filtered: false,
          flags: [],
        ),
      );
      
      return ListView.builder(
        controller: widget.scrollController,
        padding: const EdgeInsets.all(AppTheme.spacingL),
        itemCount: 1,
        itemBuilder: (context, index) {
          return Padding(
            padding: const EdgeInsets.only(bottom: AppTheme.spacingL),
            child: ChatMessageBubble(
              message: welcomeMessage,
              onCopy: () => _copyMessage(welcomeMessage.content),
              onRetry: () => _retryMessage(welcomeMessage),
            ),
          );
        },
      );
    }

    return ListView.builder(
      controller: widget.scrollController,
      padding: const EdgeInsets.all(AppTheme.spacingL),
      itemCount: messages.length,
      itemBuilder: (context, index) {
        final message = messages[index];
        final isLastMessage = index == messages.length - 1;
        
        return Padding(
          padding: EdgeInsets.only(
            bottom: isLastMessage ? AppTheme.spacingL : AppTheme.spacingM,
          ),
          child: ChatMessageBubble(
            message: message,
            onCopy: () => _copyMessage(message.content),
            onRetry: message.role == MessageRole.assistant ? () => _retryMessage(message) : null,
          ),
        );
      },
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              color: AppTheme.accentColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Icon(
              Icons.chat_bubble_outline,
              size: 40,
              color: AppTheme.accentColor.withOpacity(0.6),
            ),
          ),
          const SizedBox(height: AppTheme.spacingXL),
          Text(
            'Chào mừng đến với StillMe!',
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: AppTheme.spacingM),
          Text(
            'Tôi là trợ lý AI cá nhân của bạn.\nHãy bắt đầu cuộc trò chuyện!',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: AppTheme.textSecondary,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: AppTheme.spacingXXL),
          Container(
            padding: const EdgeInsets.all(AppTheme.spacingL),
            decoration: BoxDecoration(
              color: AppTheme.cardColor,
              borderRadius: BorderRadius.circular(AppTheme.radiusL),
              boxShadow: AppTheme.cardShadow,
            ),
            child: Column(
              children: [
                Text(
                  '💡 Gợi ý',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: AppTheme.spacingM),
                _buildSuggestionChip('Hỏi về lập trình'),
                const SizedBox(height: AppTheme.spacingS),
                _buildSuggestionChip('Dịch văn bản'),
                const SizedBox(height: AppTheme.spacingS),
                _buildSuggestionChip('Tóm tắt nội dung'),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSuggestionChip(String text) {
    return InkWell(
      onTap: () {
        // TODO: Send suggestion message
      },
      borderRadius: BorderRadius.circular(AppTheme.radiusM),
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppTheme.spacingL,
          vertical: AppTheme.spacingM,
        ),
        decoration: BoxDecoration(
          color: AppTheme.surfaceColor,
          borderRadius: BorderRadius.circular(AppTheme.radiusM),
          border: Border.all(
            color: AppTheme.accentColor.withOpacity(0.3),
            width: 1,
          ),
        ),
        child: Text(
          text,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: AppTheme.accentColor,
          ),
        ),
      ),
    );
  }

  void _copyMessage(String content) {
    // TODO: Implement copy to clipboard
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Đã sao chép tin nhắn'),
        duration: Duration(seconds: 2),
      ),
    );
  }

  void _retryMessage(ChatMessage message) {
    // TODO: Implement retry message
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Đang thử lại...'),
        duration: Duration(seconds: 2),
      ),
    );
  }
}
