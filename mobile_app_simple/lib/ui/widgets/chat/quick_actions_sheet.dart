import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/models/chat_models.dart';

class QuickActionsSheet extends StatelessWidget {
  const QuickActionsSheet({super.key});

  @override
  Widget build(BuildContext context) {
    final quickActions = [
      QuickAction(
        id: 'persona',
        title: 'Đổi Persona',
        description: 'Thay đổi phong cách trò chuyện',
        command: '/persona',
        type: QuickActionType.persona,
        icon: '🎭',
      ),
      QuickAction(
        id: 'translate',
        title: 'Dịch Tự Động',
        description: 'Bật/tắt dịch tự động',
        command: '/translate',
        type: QuickActionType.translate,
        icon: '🌐',
      ),
      QuickAction(
        id: 'dev_route',
        title: 'Dev Route',
        description: 'Hiển thị routing model',
        command: '/dev route',
        type: QuickActionType.devRoute,
        icon: '🔧',
      ),
      QuickAction(
        id: 'clear',
        title: 'Xóa Session',
        description: 'Xóa toàn bộ cuộc trò chuyện',
        command: '/clear',
        type: QuickActionType.clear,
        icon: '🗑️',
      ),
      QuickAction(
        id: 'export',
        title: 'Xuất Hội Thoại',
        description: 'Xuất ra JSON/Markdown',
        command: '/export',
        type: QuickActionType.export,
        icon: '📤',
      ),
      QuickAction(
        id: 'founder',
        title: 'Founder Console',
        description: 'Mở console dành cho founder',
        command: ':founder',
        type: QuickActionType.founder,
        icon: '👑',
      ),
    ];

    return Container(
      decoration: const BoxDecoration(
        color: AppTheme.cardColor,
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(AppTheme.radiusXL),
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Handle
          Container(
            margin: const EdgeInsets.only(top: AppTheme.spacingM),
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: AppTheme.textSecondary,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          
          // Header
          Padding(
            padding: const EdgeInsets.all(AppTheme.spacingL),
            child: Row(
              children: [
                Icon(
                  Icons.flash_on,
                  color: AppTheme.accentColor,
                  size: 24,
                ),
                const SizedBox(width: AppTheme.spacingM),
                Text(
                  'Quick Actions',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                IconButton(
                  onPressed: () => Navigator.of(context).pop(),
                  icon: const Icon(Icons.close),
                  color: AppTheme.textSecondary,
                ),
              ],
            ),
          ),
          
          // Actions Grid
          Padding(
            padding: const EdgeInsets.fromLTRB(
              AppTheme.spacingL,
              0,
              AppTheme.spacingL,
              AppTheme.spacingL,
            ),
            child: GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                crossAxisSpacing: AppTheme.spacingM,
                mainAxisSpacing: AppTheme.spacingM,
                childAspectRatio: 1.2,
              ),
              itemCount: quickActions.length,
              itemBuilder: (context, index) {
                final action = quickActions[index];
                return _buildActionCard(context, action);
              },
            ),
          ),
          
          // Bottom padding for safe area
          SizedBox(height: MediaQuery.of(context).padding.bottom),
        ],
      ),
    );
  }

  Widget _buildActionCard(BuildContext context, QuickAction action) {
    return InkWell(
      onTap: () => _handleAction(context, action),
      borderRadius: BorderRadius.circular(AppTheme.radiusL),
      child: Container(
        padding: const EdgeInsets.all(AppTheme.spacingL),
        decoration: BoxDecoration(
          color: AppTheme.surfaceColor,
          borderRadius: BorderRadius.circular(AppTheme.radiusL),
          border: Border.all(
            color: AppTheme.accentColor.withOpacity(0.2),
            width: 1,
          ),
          boxShadow: AppTheme.cardShadow,
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Icon
            Text(
              action.icon ?? '❓',
              style: const TextStyle(fontSize: 32),
            ),
            
            const SizedBox(height: AppTheme.spacingM),
            
            // Title
            Text(
              action.title,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
              textAlign: TextAlign.center,
            ),
            
            const SizedBox(height: AppTheme.spacingS),
            
            // Description
            Text(
              action.description,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppTheme.textSecondary,
              ),
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }

  void _handleAction(BuildContext context, QuickAction action) {
    Navigator.of(context).pop();
    
    switch (action.type) {
      case QuickActionType.persona:
        _showPersonaDialog(context);
        break;
      case QuickActionType.translate:
        _toggleTranslate(context);
        break;
      case QuickActionType.devRoute:
        _showDevRoute(context);
        break;
      case QuickActionType.clear:
        _showClearDialog(context);
        break;
      case QuickActionType.export:
        _showExportDialog(context);
        break;
      case QuickActionType.founder:
        _openFounderConsole(context);
        break;
    }
  }

  void _showPersonaDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Chọn Persona'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildPersonaOption(context, 'Assistant', 'Trợ lý thông thường'),
            _buildPersonaOption(context, 'Developer', 'Chuyên gia lập trình'),
            _buildPersonaOption(context, 'Teacher', 'Giáo viên kiên nhẫn'),
            _buildPersonaOption(context, 'Friend', 'Bạn bè thân thiết'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Hủy'),
          ),
        ],
      ),
    );
  }

  Widget _buildPersonaOption(BuildContext context, String name, String description) {
    return ListTile(
      title: Text(name),
      subtitle: Text(description),
      onTap: () {
        Navigator.of(context).pop();
        // TODO: Apply persona
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Đã chọn persona: $name')),
        );
      },
    );
  }

  void _toggleTranslate(BuildContext context) {
    // TODO: Toggle auto translate
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Đã bật/tắt dịch tự động')),
    );
  }

  void _showDevRoute(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Dev Route Info'),
        content: const Text(
          'Model hiện tại: gemma2:2b\n'
          'Candidates: gemma2:2b, deepseek-coder-6.7b\n'
          'Routing: Local-first với fallback',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Đóng'),
          ),
        ],
      ),
    );
  }

  void _showClearDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Xóa Session'),
        content: const Text('Bạn có chắc muốn xóa toàn bộ cuộc trò chuyện?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Hủy'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              // TODO: Clear session
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Đã xóa session')),
              );
            },
            child: const Text('Xóa', style: TextStyle(color: AppTheme.errorColor)),
          ),
        ],
      ),
    );
  }

  void _showExportDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Xuất Hội Thoại'),
        content: const Text('Chọn định dạng xuất:'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Hủy'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              // TODO: Export as JSON
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Đã xuất JSON')),
              );
            },
            child: const Text('JSON'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              // TODO: Export as Markdown
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Đã xuất Markdown')),
              );
            },
            child: const Text('Markdown'),
          ),
        ],
      ),
    );
  }

  void _openFounderConsole(BuildContext context) {
    // TODO: Navigate to founder console
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Mở Founder Console...')),
    );
  }
}
