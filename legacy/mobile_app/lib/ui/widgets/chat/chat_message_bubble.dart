import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_markdown/flutter_markdown.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/models/chat_models.dart';

class ChatMessageBubble extends StatelessWidget {
  final ChatMessage message;
  final VoidCallback? onCopy;
  final VoidCallback? onRetry;

  const ChatMessageBubble({
    super.key,
    required this.message,
    this.onCopy,
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == MessageRole.user;
    final isAssistant = message.role == MessageRole.assistant;
    
    return Row(
      mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (!isUser) ...[
          _buildAvatar(),
          const SizedBox(width: AppTheme.spacingM),
        ],
        
        Flexible(
          child: Column(
            crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
            children: [
              _buildMessageBubble(context, isUser),
              if (isAssistant) ...[
                const SizedBox(height: AppTheme.spacingS),
                _buildMessageMetadata(context),
              ],
            ],
          ),
        ),
        
        if (isUser) ...[
          const SizedBox(width: AppTheme.spacingM),
          _buildAvatar(),
        ],
      ],
    );
  }

  Widget _buildAvatar() {
    final isUser = message.role == MessageRole.user;
    
    return Container(
      width: 32,
      height: 32,
      decoration: BoxDecoration(
        color: isUser ? AppTheme.accentColor : AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(16),
        boxShadow: AppTheme.cardShadow,
      ),
      child: Icon(
        isUser ? Icons.person : Icons.psychology,
        size: 18,
        color: Colors.white,
      ),
    );
  }

  Widget _buildMessageBubble(BuildContext context, bool isUser) {
    return Container(
      constraints: BoxConstraints(
        maxWidth: MediaQuery.of(context).size.width * 0.75,
      ),
      padding: const EdgeInsets.all(AppTheme.spacingL),
      decoration: BoxDecoration(
        color: isUser ? AppTheme.chatBubbleUser : AppTheme.chatBubbleAssistant,
        borderRadius: BorderRadius.only(
          topLeft: const Radius.circular(AppTheme.radiusL),
          topRight: const Radius.circular(AppTheme.radiusL),
          bottomLeft: Radius.circular(isUser ? AppTheme.radiusL : AppTheme.radiusS),
          bottomRight: Radius.circular(isUser ? AppTheme.radiusS : AppTheme.radiusL),
        ),
        boxShadow: AppTheme.cardShadow,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (message.isTyping)
            _buildTypingIndicator()
          else
            _buildMessageContent(context),
          
          if (isUser) ...[
            const SizedBox(height: AppTheme.spacingS),
            _buildTimestamp(),
          ],
        ],
      ),
    );
  }

  Widget _buildMessageContent(BuildContext context) {
    return MarkdownBody(
      data: message.content,
      selectable: true,
      styleSheet: MarkdownStyleSheet(
        p: Theme.of(context).textTheme.bodyMedium?.copyWith(
          color: Colors.white,
          height: 1.4,
        ),
        code: Theme.of(context).textTheme.bodyMedium?.copyWith(
          fontFamily: 'monospace',
          backgroundColor: Colors.black.withOpacity(0.2),
          color: Colors.white,
        ),
        codeblockDecoration: BoxDecoration(
          color: Colors.black.withOpacity(0.2),
          borderRadius: BorderRadius.circular(AppTheme.radiusS),
        ),
        blockquoteDecoration: BoxDecoration(
          color: Colors.white.withOpacity(0.1),
          borderRadius: BorderRadius.circular(AppTheme.radiusS),
        ),
        listBullet: Theme.of(context).textTheme.bodyMedium?.copyWith(
          color: Colors.white,
        ),
      ),
      onTapLink: (text, href, title) {
        // TODO: Handle link taps
      },
    );
  }

  Widget _buildTypingIndicator() {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        _buildTypingDot(0),
        const SizedBox(width: 4),
        _buildTypingDot(1),
        const SizedBox(width: 4),
        _buildTypingDot(2),
      ],
    );
  }

  Widget _buildTypingDot(int index) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0.0, end: 1.0),
      duration: const Duration(milliseconds: 600),
      builder: (context, value, child) {
        final delay = index * 0.2;
        final animationValue = (value - delay).clamp(0.0, 1.0);
        final opacity = (animationValue * 2 - 1).abs();
        
        return Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(opacity),
            shape: BoxShape.circle,
          ),
        );
      },
    );
  }

  Widget _buildTimestamp() {
    final time = message.timestamp;
    final timeString = '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';
    
    return Text(
      timeString,
      style: Theme.of(context).textTheme.bodySmall?.copyWith(
        color: Colors.white.withOpacity(0.7),
        fontSize: 11,
      ),
    );
  }

  Widget _buildMessageMetadata(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Model indicator
        if (message.model != null) ...[
          Container(
            padding: const EdgeInsets.symmetric(
              horizontal: AppTheme.spacingS,
              vertical: AppTheme.spacingXS,
            ),
            decoration: BoxDecoration(
              color: AppTheme.surfaceColor,
              borderRadius: BorderRadius.circular(AppTheme.radiusS),
            ),
            child: Text(
              message.model!,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppTheme.textSecondary,
                fontSize: 10,
              ),
            ),
          ),
          const SizedBox(width: AppTheme.spacingS),
        ],
        
        // Latency indicator
        if (message.latencyMs != null) ...[
          Container(
            padding: const EdgeInsets.symmetric(
              horizontal: AppTheme.spacingS,
              vertical: AppTheme.spacingXS,
            ),
            decoration: BoxDecoration(
              color: _getLatencyColor(message.latencyMs!).withOpacity(0.2),
              borderRadius: BorderRadius.circular(AppTheme.radiusS),
            ),
            child: Text(
              '${message.latencyMs}ms',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: _getLatencyColor(message.latencyMs!),
                fontSize: 10,
              ),
            ),
          ),
          const SizedBox(width: AppTheme.spacingS),
        ],
        
        // Action buttons
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (onCopy != null)
              _buildActionButton(
                context,
                icon: Icons.copy,
                onTap: () {
                  Clipboard.setData(ClipboardData(text: message.content));
                  onCopy?.call();
                },
              ),
            
            if (onRetry != null)
              _buildActionButton(
                context,
                icon: Icons.refresh,
                onTap: onRetry!,
              ),
          ],
        ),
      ],
    );
  }

  Widget _buildActionButton(
    BuildContext context, {
    required IconData icon,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppTheme.radiusS),
      child: Container(
        padding: const EdgeInsets.all(AppTheme.spacingXS),
        child: Icon(
          icon,
          size: 14,
          color: AppTheme.textSecondary,
        ),
      ),
    );
  }

  Color _getLatencyColor(int latencyMs) {
    if (latencyMs < 500) return AppTheme.successColor;
    if (latencyMs < 1000) return AppTheme.warningColor;
    return AppTheme.errorColor;
  }
}
