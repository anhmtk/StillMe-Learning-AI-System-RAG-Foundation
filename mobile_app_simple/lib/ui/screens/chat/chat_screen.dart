import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/models/chat_models.dart';
import '../../../core/providers/chat_provider.dart';
import '../../../data/chat_repository.dart';
import '../../widgets/chat/chat_message_list.dart';
import '../../widgets/chat/chat_input_bar.dart';
import '../../widgets/chat/telemetry_strip.dart';
import '../../widgets/chat/quick_actions_sheet.dart';
import '../settings/settings_screen.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final ScrollController _scrollController = ScrollController();
  final TextEditingController _messageController = TextEditingController();
  late final ChatRepository _chatRepository;
  
  @override
  void initState() {
    super.initState();
    _chatRepository = ChatRepository(
      baseUrl: 'http://160.191.89.99:21568',
      timeoutMs: 25000,
    );
  }
  
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

  void _sendMessage(String message) async {
    // Add user message to chat
    ref.read(chatProvider.notifier).addUserMessage(message);
    
    try {
      // Send to real AI server
      final aiResponse = await _chatRepository.sendMessage(message);
      
      // Add AI response to chat
      ref.read(chatProvider.notifier).addMessage(aiResponse);
    } catch (e) {
      // Show error message
      ref.read(chatProvider.notifier).addAIMessage(
        'Xin lỗi, có lỗi xảy ra: ${e.toString()}',
        model: 'error',
        latencyMs: 0,
      );
    }
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
                  'StillMe',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  'Personal AI',
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
          
          // Metrics Button
          IconButton(
            onPressed: _showMetrics,
            icon: const Icon(Icons.analytics_outlined),
            tooltip: 'View Metrics',
          ),
          
          // Settings Button
          IconButton(
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => const SettingsScreen(),
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
              _sendMessage(message);
              _scrollToBottom();
            },
            onShowQuickActions: _showQuickActions,
          ),
        ],
      ),
    );
  }
}
