import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../core/theme/app_theme.dart';

class ChatInputBar extends StatefulWidget {
  final TextEditingController controller;
  final Function(String) onSendMessage;
  final VoidCallback onShowQuickActions;

  const ChatInputBar({
    super.key,
    required this.controller,
    required this.onSendMessage,
    required this.onShowQuickActions,
  });

  @override
  State<ChatInputBar> createState() => _ChatInputBarState();
}

class _ChatInputBarState extends State<ChatInputBar> {
  bool _isComposing = false;
  final FocusNode _focusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_onTextChanged);
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onTextChanged);
    _focusNode.dispose();
    super.dispose();
  }

  void _onTextChanged() {
    final isComposing = widget.controller.text.trim().isNotEmpty;
    if (isComposing != _isComposing) {
      setState(() {
        _isComposing = isComposing;
      });
    }
  }

  void _handleSendMessage() {
    final text = widget.controller.text.trim();
    if (text.isNotEmpty) {
      widget.onSendMessage(text);
      widget.controller.clear();
      _focusNode.unfocus();
    }
  }

  void _handleQuickActions() {
    widget.onShowQuickActions();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppTheme.spacingL),
      decoration: BoxDecoration(
        color: AppTheme.cardColor,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 8,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        child: Row(
          children: [
            // Quick Actions Button
            Container(
              decoration: BoxDecoration(
                color: AppTheme.surfaceColor,
                borderRadius: BorderRadius.circular(AppTheme.radiusM),
              ),
              child: IconButton(
                onPressed: _handleQuickActions,
                icon: const Icon(Icons.add),
                tooltip: 'Quick Actions',
                color: AppTheme.accentColor,
              ),
            ),
            
            const SizedBox(width: AppTheme.spacingM),
            
            // Text Input
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  color: AppTheme.surfaceColor,
                  borderRadius: BorderRadius.circular(AppTheme.radiusM),
                  border: Border.all(
                    color: _focusNode.hasFocus 
                        ? AppTheme.accentColor 
                        : Colors.transparent,
                    width: 2,
                  ),
                ),
                child: TextField(
                  controller: widget.controller,
                  focusNode: _focusNode,
                  maxLines: null,
                  textCapitalization: TextCapitalization.sentences,
                  decoration: InputDecoration(
                    hintText: 'Nhập tin nhắn...',
                    border: InputBorder.none,
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: AppTheme.spacingL,
                      vertical: AppTheme.spacingM,
                    ),
                    hintStyle: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: AppTheme.textSecondary,
                    ),
                  ),
                  style: Theme.of(context).textTheme.bodyMedium,
                  onSubmitted: (_) => _handleSendMessage(),
                ),
              ),
            ),
            
            const SizedBox(width: AppTheme.spacingM),
            
            // Send Button
            AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              decoration: BoxDecoration(
                color: _isComposing ? AppTheme.accentColor : AppTheme.surfaceColor,
                borderRadius: BorderRadius.circular(AppTheme.radiusM),
              ),
              child: IconButton(
                onPressed: _isComposing ? _handleSendMessage : null,
                icon: Icon(
                  Icons.send,
                  color: _isComposing ? Colors.white : AppTheme.textSecondary,
                ),
                tooltip: 'Gửi tin nhắn',
              ),
            ),
          ],
        ),
      ),
    );
  }
}
