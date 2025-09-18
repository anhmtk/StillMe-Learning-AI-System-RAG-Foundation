import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_theme.dart';

class FounderConsoleScreen extends ConsumerStatefulWidget {
  const FounderConsoleScreen({super.key});

  @override
  ConsumerState<FounderConsoleScreen> createState() => _FounderConsoleScreenState();
}

class _FounderConsoleScreenState extends ConsumerState<FounderConsoleScreen> {
  final TextEditingController _commandController = TextEditingController();
  final List<String> _commandHistory = [];
  int _historyIndex = -1;

  @override
  void dispose() {
    _commandController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        title: Row(
          children: [
            Icon(
              Icons.admin_panel_settings,
              color: AppTheme.founderModeAccent,
            ),
            const SizedBox(width: AppTheme.spacingM),
            const Text('Founder Console'),
            const Spacer(),
            Container(
              padding: const EdgeInsets.symmetric(
                horizontal: AppTheme.spacingM,
                vertical: AppTheme.spacingS,
              ),
              decoration: BoxDecoration(
                color: AppTheme.founderModeAccent.withOpacity(0.2),
                borderRadius: BorderRadius.circular(AppTheme.radiusS),
                border: Border.all(
                  color: AppTheme.founderModeAccent,
                  width: 1,
                ),
              ),
              child: Text(
                'FOUNDER MODE',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppTheme.founderModeAccent,
                  fontWeight: FontWeight.bold,
                  fontSize: 10,
                ),
              ),
            ),
          ],
        ),
        leading: IconButton(
          onPressed: () => Navigator.of(context).pop(),
          icon: const Icon(Icons.arrow_back),
        ),
      ),
      body: Column(
        children: [
          // AgentDev Commands Section
          Expanded(
            flex: 2,
            child: _buildAgentDevSection(context),
          ),
          
          // Switches Section
          Expanded(
            flex: 2,
            child: _buildSwitchesSection(context),
          ),
          
          // Metrics Section
          Expanded(
            flex: 3,
            child: _buildMetricsSection(context),
          ),
          
          // Command Input
          _buildCommandInput(context),
        ],
      ),
    );
  }

  Widget _buildAgentDevSection(BuildContext context) {
    return Container(
      margin: const EdgeInsets.all(AppTheme.spacingL),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'AgentDev Commands',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: AppTheme.spacingL),
          
          Expanded(
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(AppTheme.spacingL),
                child: Column(
                  children: [
                    _buildCommandButton(
                      context,
                      '/agentdev run <task>',
                      'Execute AgentDev task',
                      Icons.play_arrow,
                      () => _executeCommand('/agentdev run test'),
                    ),
                    const SizedBox(height: AppTheme.spacingM),
                    _buildCommandButton(
                      context,
                      '/agentdev status',
                      'Check AgentDev status',
                      Icons.info,
                      () => _executeCommand('/agentdev status'),
                    ),
                    const SizedBox(height: AppTheme.spacingM),
                    _buildCommandButton(
                      context,
                      '/agentdev model <name>',
                      'Set model routing hint',
                      Icons.model_training,
                      () => _executeCommand('/agentdev model gemma2:2b'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCommandButton(
    BuildContext context,
    String command,
    String description,
    IconData icon,
    VoidCallback onPressed,
  ) {
    return InkWell(
      onTap: onPressed,
      borderRadius: BorderRadius.circular(AppTheme.radiusM),
      child: Container(
        padding: const EdgeInsets.all(AppTheme.spacingM),
        decoration: BoxDecoration(
          color: AppTheme.surfaceColor,
          borderRadius: BorderRadius.circular(AppTheme.radiusM),
          border: Border.all(
            color: AppTheme.accentColor.withOpacity(0.3),
            width: 1,
          ),
        ),
        child: Row(
          children: [
            Icon(icon, color: AppTheme.accentColor),
            const SizedBox(width: AppTheme.spacingM),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    command,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                      fontFamily: 'monospace',
                    ),
                  ),
                  Text(
                    description,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: AppTheme.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
            const Icon(Icons.arrow_forward_ios, size: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildSwitchesSection(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(
        AppTheme.spacingL,
        0,
        AppTheme.spacingL,
        AppTheme.spacingL,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'System Switches',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: AppTheme.spacingL),
          
          Expanded(
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(AppTheme.spacingL),
                child: Column(
                  children: [
                    _buildSwitchTile(
                      context,
                      'Auto-translate',
                      'Gemma/NLLB đầu vào/ra',
                      true,
                      (value) {},
                    ),
                    _buildSwitchTile(
                      context,
                      'Safety Level: Strict',
                      'Bảo mật cao',
                      false,
                      (value) {},
                    ),
                    _buildSwitchTile(
                      context,
                      'Token Cap: 4000',
                      'Giới hạn token mỗi tin nhắn',
                      true,
                      (value) {},
                    ),
                    _buildSwitchTile(
                      context,
                      'Max Latency: 10s',
                      'Cảnh báo nếu vượt ngưỡng',
                      true,
                      (value) {},
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSwitchTile(
    BuildContext context,
    String title,
    String subtitle,
    bool value,
    ValueChanged<bool> onChanged,
  ) {
    return SwitchListTile(
      title: Text(
        title,
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
          fontWeight: FontWeight.w600,
        ),
      ),
      subtitle: Text(
        subtitle,
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
          color: AppTheme.textSecondary,
        ),
      ),
      value: value,
      onChanged: onChanged,
      activeColor: AppTheme.accentColor,
      contentPadding: EdgeInsets.zero,
    );
  }

  Widget _buildMetricsSection(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(
        AppTheme.spacingL,
        0,
        AppTheme.spacingL,
        AppTheme.spacingL,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Live Metrics',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: AppTheme.spacingL),
          
          Expanded(
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(AppTheme.spacingL),
                child: Column(
                  children: [
                    // Model Status
                    _buildMetricCard(
                      context,
                      'Model In-Use',
                      'gemma2:2b',
                      Icons.model_training,
                      AppTheme.accentColor,
                    ),
                    
                    const SizedBox(height: AppTheme.spacingM),
                    
                    // Token Usage
                    Row(
                      children: [
                        Expanded(
                          child: _buildMetricCard(
                            context,
                            'Prompt Tokens',
                            '1,234',
                            Icons.input,
                            AppTheme.successColor,
                          ),
                        ),
                        const SizedBox(width: AppTheme.spacingM),
                        Expanded(
                          child: _buildMetricCard(
                            context,
                            'Completion Tokens',
                            '2,567',
                            Icons.output,
                            AppTheme.warningColor,
                          ),
                        ),
                      ],
                    ),
                    
                    const SizedBox(height: AppTheme.spacingM),
                    
                    // Performance
                    Row(
                      children: [
                        Expanded(
                          child: _buildMetricCard(
                            context,
                            'Avg Latency',
                            '840ms',
                            Icons.speed,
                            AppTheme.successColor,
                          ),
                        ),
                        const SizedBox(width: AppTheme.spacingM),
                        Expanded(
                          child: _buildMetricCard(
                            context,
                            'Error Rate',
                            '0.1%',
                            Icons.error_outline,
                            AppTheme.successColor,
                          ),
                        ),
                      ],
                    ),
                    
                    const SizedBox(height: AppTheme.spacingM),
                    
                    // Cost
                    _buildMetricCard(
                      context,
                      'Session Cost',
                      '\$0.0042',
                      Icons.attach_money,
                      AppTheme.warningColor,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricCard(
    BuildContext context,
    String label,
    String value,
    IconData icon,
    Color color,
  ) {
    return Container(
      padding: const EdgeInsets.all(AppTheme.spacingM),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(AppTheme.radiusM),
        border: Border.all(
          color: color.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: AppTheme.spacingS),
          Text(
            value,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          Text(
            label,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: AppTheme.textSecondary,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildCommandInput(BuildContext context) {
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
            Expanded(
              child: TextField(
                controller: _commandController,
                decoration: InputDecoration(
                  hintText: 'Enter AgentDev command...',
                  prefixIcon: const Icon(Icons.terminal),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(AppTheme.radiusM),
                  ),
                ),
                style: const TextStyle(fontFamily: 'monospace'),
                onSubmitted: _executeCommand,
                onChanged: (value) {
                  // Handle command history navigation
                },
              ),
            ),
            const SizedBox(width: AppTheme.spacingM),
            IconButton(
              onPressed: () => _executeCommand(_commandController.text),
              icon: const Icon(Icons.send),
              style: IconButton.styleFrom(
                backgroundColor: AppTheme.accentColor,
                foregroundColor: Colors.white,
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _executeCommand(String command) {
    if (command.trim().isEmpty) return;
    
    _commandHistory.add(command);
    _historyIndex = _commandHistory.length;
    _commandController.clear();
    
    // TODO: Execute actual command
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Executing: $command'),
        duration: const Duration(seconds: 2),
      ),
    );
  }
}
