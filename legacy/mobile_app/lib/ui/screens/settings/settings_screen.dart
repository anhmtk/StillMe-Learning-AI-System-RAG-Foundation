import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_theme.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        title: const Text('Settings'),
        leading: IconButton(
          onPressed: () => Navigator.of(context).pop(),
          icon: const Icon(Icons.arrow_back),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(AppTheme.spacingL),
        children: [
          // Profile Section
          _buildSection(
            context,
            title: 'Profile',
            icon: Icons.person,
            children: [
              _buildProfileCard(context),
            ],
          ),
          
          const SizedBox(height: AppTheme.spacingXL),
          
          // Server Settings
          _buildSection(
            context,
            title: 'Server Settings',
            icon: Icons.dns,
            children: [
              _buildServerCard(context),
            ],
          ),
          
          const SizedBox(height: AppTheme.spacingXL),
          
          // Features
          _buildSection(
            context,
            title: 'Features',
            icon: Icons.tune,
            children: [
              _buildFeatureSwitch(
                context,
                title: 'Telemetry',
                subtitle: 'Hiển thị metrics và thống kê',
                value: true,
                onChanged: (value) {
                  // TODO: Update telemetry setting
                },
              ),
              _buildFeatureSwitch(
                context,
                title: 'Auto Translate',
                subtitle: 'Dịch tự động đầu vào/ra',
                value: false,
                onChanged: (value) {
                  // TODO: Update auto translate setting
                },
              ),
              _buildFeatureSwitch(
                context,
                title: 'Founder Mode',
                subtitle: 'Kích hoạt chế độ founder',
                value: false,
                onChanged: (value) {
                  // TODO: Update founder mode setting
                },
              ),
            ],
          ),
          
          const SizedBox(height: AppTheme.spacingXL),
          
          // Privacy
          _buildSection(
            context,
            title: 'Privacy',
            icon: Icons.privacy_tip,
            children: [
              _buildFeatureSwitch(
                context,
                title: 'Local Logging Only',
                subtitle: 'Chỉ lưu log trên thiết bị',
                value: true,
                onChanged: (value) {
                  // TODO: Update privacy setting
                },
              ),
            ],
          ),
          
          const SizedBox(height: AppTheme.spacingXL),
          
          // About
          _buildSection(
            context,
            title: 'About',
            icon: Icons.info,
            children: [
              _buildAboutCard(context),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSection(
    BuildContext context, {
    required String title,
    required IconData icon,
    required List<Widget> children,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(
              icon,
              color: AppTheme.accentColor,
              size: 24,
            ),
            const SizedBox(width: AppTheme.spacingM),
            Text(
              title,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        const SizedBox(height: AppTheme.spacingL),
        ...children,
      ],
    );
  }

  Widget _buildProfileCard(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppTheme.spacingL),
        child: Column(
          children: [
            CircleAvatar(
              radius: 40,
              backgroundColor: AppTheme.accentColor,
              child: const Icon(
                Icons.person,
                size: 40,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: AppTheme.spacingL),
            Text(
              'Founder: Anh Nguyen',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: AppTheme.spacingS),
            Text(
              'StillMe Personal AI',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: AppTheme.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildServerCard(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppTheme.spacingL),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.link, color: AppTheme.accentColor),
                const SizedBox(width: AppTheme.spacingM),
                Text(
                  'Base URL',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const Spacer(),
                TextButton(
                  onPressed: () => _showServerSettings(context),
                  child: const Text('Edit'),
                ),
              ],
            ),
            const SizedBox(height: AppTheme.spacingM),
            Container(
              padding: const EdgeInsets.all(AppTheme.spacingM),
              decoration: BoxDecoration(
                color: AppTheme.surfaceColor,
                borderRadius: BorderRadius.circular(AppTheme.radiusS),
              ),
              child: Row(
                children: [
                  const Icon(Icons.dns, size: 16, color: AppTheme.textSecondary),
                  const SizedBox(width: AppTheme.spacingS),
                  Expanded(
                    child: Text(
                      'http://160.191.89.99:21568',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ),
                  IconButton(
                    onPressed: () => _testConnection(context),
                    icon: const Icon(Icons.wifi_protected_setup, size: 20),
                    tooltip: 'Test Connection',
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFeatureSwitch(
    BuildContext context, {
    required String title,
    required String subtitle,
    required bool value,
    required ValueChanged<bool> onChanged,
  }) {
    return Card(
      child: SwitchListTile(
        title: Text(
          title,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
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
      ),
    );
  }

  Widget _buildAboutCard(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppTheme.spacingL),
        child: Column(
          children: [
            _buildAboutItem(
              context,
              'Version',
              '1.0.0',
              Icons.info_outline,
            ),
            const Divider(),
            _buildAboutItem(
              context,
              'Build',
              '2025.01.16',
              Icons.build,
            ),
            const Divider(),
            _buildAboutItem(
              context,
              'Flutter',
              '3.10.0',
              Icons.phone_android,
            ),
            const Divider(),
            _buildAboutItem(
              context,
              'License',
              'MIT',
              Icons.copyright,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAboutItem(
    BuildContext context,
    String label,
    String value,
    IconData icon,
  ) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppTheme.spacingS),
      child: Row(
        children: [
          Icon(icon, size: 20, color: AppTheme.textSecondary),
          const SizedBox(width: AppTheme.spacingM),
          Text(
            label,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const Spacer(),
          Text(
            value,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  void _showServerSettings(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Server Settings'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              decoration: const InputDecoration(
                labelText: 'Base URL',
                hintText: 'http://160.191.89.99:21568',
              ),
              controller: TextEditingController(
                text: 'http://160.191.89.99:21568',
              ),
            ),
            const SizedBox(height: AppTheme.spacingM),
            TextField(
              decoration: const InputDecoration(
                labelText: 'Timeout (ms)',
                hintText: '30000',
              ),
              controller: TextEditingController(text: '30000'),
              keyboardType: TextInputType.number,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Server settings updated')),
              );
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }

  void _testConnection(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Row(
          children: [
            SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            SizedBox(width: AppTheme.spacingM),
            Text('Testing connection...'),
          ],
        ),
        duration: Duration(seconds: 2),
      ),
    );
    
    // TODO: Implement actual connection test
    Future.delayed(const Duration(seconds: 2), () {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Row(
              children: [
                Icon(Icons.check_circle, color: AppTheme.successColor),
                SizedBox(width: AppTheme.spacingM),
                Text('Connection successful!'),
              ],
            ),
            backgroundColor: AppTheme.successColor,
          ),
        );
      }
    });
  }
}
