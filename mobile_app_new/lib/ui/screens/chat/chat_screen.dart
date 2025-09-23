import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/models/chat_models.dart';
import '../../../core/navigation/app_router.dart';
import '../../widgets/chat/chat_message_list.dart';
import '../../widgets/chat/chat_input_bar.dart';
import '../../widgets/chat/telemetry_strip.dart';
import '../../widgets/chat/quick_actions_sheet.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final ScrollController _scrollController = ScrollController();
  final TextEditingController _messageController = TextEditingController();
  
  @override
  void dispose() {
    _scrollController.dispose();
    _messageController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _showQuickActions() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => const QuickActionsSheet(),
    );
  }

  void _showMetrics() {
    // TODO: Implement metrics bottom sheet
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Metrics feature coming soon!'),
        duration: Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: AppTheme.accentColor,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(
                Icons.psychology,
                color: Colors.white,
                size: 20,
              ),
            ),
            const SizedBox(width: AppTheme.spacingM),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'StillMe – IPC',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  'Intelligent Personal Companion',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppTheme.textSecondary,
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          // Founder Mode Indicator
          Consumer(
            builder: (context, ref, child) {
              // TODO: Check founder mode from config
              final isFounderMode = false; // ref.watch(founderModeProvider);
              
              if (isFounderMode) {
                return Container(
                  margin: const EdgeInsets.only(right: AppTheme.spacingS),
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppTheme.spacingM,
                    vertical: AppTheme.spacingS,
                  ),
                  decoration: BoxDecoration(
                    color: AppTheme.founderModeAccent.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: AppTheme.founderModeAccent,
                      width: 1,
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.admin_panel_settings,
                        size: 16,
                        color: AppTheme.founderModeAccent,
                      ),
                      const SizedBox(width: AppTheme.spacingXS),
                      Text(
                        'Founder',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: AppTheme.founderModeAccent,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                );
              }
              
              return const SizedBox.shrink();
            },
          ),
          
          // NicheRadar Button
          IconButton(
            onPressed: () {
              context.pushToNicheRadar();
            },
            icon: const Icon(Icons.radar),
            tooltip: 'Niche Radar',
          ),
          
          // Metrics Button
          IconButton(
            onPressed: _showMetrics,
            icon: const Icon(Icons.analytics_outlined),
            tooltip: 'View Metrics',
          ),
          
          // Settings Button
          IconButton(
            onPressed: () {
              // TODO: Navigate to settings
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Settings coming soon!'),
                  duration: Duration(seconds: 2),
                ),
              );
            },
            icon: const Icon(Icons.settings_outlined),
            tooltip: 'Settings',
          ),
        ],
      ),
      body: Column(
        children: [
          // Telemetry Strip
          const TelemetryStrip(),
          
          // Chat Messages
          Expanded(
            child: ChatMessageList(
              scrollController: _scrollController,
              onScrollToBottom: _scrollToBottom,
            ),
          ),
          
          // Chat Input
          ChatInputBar(
            controller: _messageController,
            onSendMessage: (message) {
              // TODO: Send message
              _scrollToBottom();
            },
            onShowQuickActions: _showQuickActions,
          ),
        ],
      ),
    );
  }
}
