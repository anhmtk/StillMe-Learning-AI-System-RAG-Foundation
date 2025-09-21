import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/chat_repository.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        title: const Text('Settings'),
        backgroundColor: AppTheme.primaryColor,
        foregroundColor: Colors.white,
      ),
      body: ListView(
        padding: const EdgeInsets.all(AppTheme.spacingL),
        children: [
          // Profile Section
          _buildSection(
            title: 'Profile',
            children: [
              _buildSettingTile(
                icon: Icons.person,
                title: 'Founder: Anh Nguyen',
                subtitle: 'StillMe AI Creator',
                onTap: () {},
              ),
            ],
          ),
          
          const SizedBox(height: AppTheme.spacingXL),
          
          // App Settings
          _buildSection(
            title: 'App Settings',
            children: [
              _buildSettingTile(
                icon: Icons.palette,
                title: 'Theme',
                subtitle: 'Dark Mode',
                onTap: () {},
              ),
              _buildSettingTile(
                icon: Icons.language,
                title: 'Language',
                subtitle: 'Vietnamese',
                onTap: () {},
              ),
            ],
          ),
          
          const SizedBox(height: AppTheme.spacingXL),
          
          // Server Settings
          _buildSection(
            title: 'Server Settings',
            children: [
              _buildSettingTile(
                icon: Icons.cloud,
                title: 'Base URL',
                subtitle: 'http://192.168.1.12:1216',
                onTap: () => _editBaseUrl(context),
              ),
              _buildSettingTile(
                icon: Icons.health_and_safety,
                title: 'Test Connection',
                subtitle: 'Check server status',
                onTap: () => _testConnection(context),
              ),
            ],
          ),
          
          const SizedBox(height: AppTheme.spacingXL),
          
          // About
          _buildSection(
            title: 'About',
            children: [
              _buildSettingTile(
                icon: Icons.info,
                title: 'Version',
                subtitle: '1.0.0',
                onTap: () {},
              ),
              _buildSettingTile(
                icon: Icons.code,
                title: 'StillMe AI',
                subtitle: 'Personal AI Assistant',
                onTap: () {},
              ),
              FutureBuilder<PackageInfo>(
                future: PackageInfo.fromPlatform(),
                builder: (context, snapshot) {
                  if (snapshot.hasData) {
                    final packageInfo = snapshot.data!;
                    return _buildSettingTile(
                      icon: Icons.android,
                      title: 'Package ID',
                      subtitle: '${packageInfo.packageName}\nBuild: ${packageInfo.buildNumber}',
                      onTap: () {},
                    );
                  }
                  return _buildSettingTile(
                    icon: Icons.android,
                    title: 'Package ID',
                    subtitle: 'Loading...',
                    onTap: () {},
                  );
                },
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSection({
    required String title,
    required List<Widget> children,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: AppTheme.textPrimary,
          ),
        ),
        const SizedBox(height: AppTheme.spacingM),
        ...children,
      ],
    );
  }

  Widget _buildSettingTile({
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return Card(
      color: AppTheme.cardColor,
      child: ListTile(
        leading: Icon(icon, color: AppTheme.primaryColor),
        title: Text(
          title,
          style: const TextStyle(color: AppTheme.textPrimary),
        ),
        subtitle: Text(
          subtitle,
          style: const TextStyle(color: AppTheme.textSecondary),
        ),
        trailing: const Icon(
          Icons.chevron_right,
          color: AppTheme.textSecondary,
        ),
        onTap: onTap,
      ),
    );
  }

  void _editBaseUrl(BuildContext context) {
    final TextEditingController controller = TextEditingController();
    controller.text = 'http://192.168.1.12:1216';
    
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Edit Base URL'),
          content: TextField(
            controller: controller,
            decoration: const InputDecoration(
              hintText: 'Enter base URL',
              border: OutlineInputBorder(),
            ),
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
                  SnackBar(
                    content: Text('Base URL updated: ${controller.text}'),
                    backgroundColor: Colors.green,
                  ),
                );
              },
              child: const Text('Save'),
            ),
          ],
        );
      },
    );
  }

  void _testConnection(BuildContext context) async {
    // Show loading
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Testing connection...'),
        duration: Duration(seconds: 1),
      ),
    );

    try {
      final chatRepository = ChatRepository(
        baseUrl: 'http://192.168.1.12:1216',
        timeoutMs: 25000,
      );
      
      // Test health endpoint
      final healthResult = await chatRepository.testConnection();
      
      if (healthResult['success']) {
        // Test chat endpoint
        try {
          final chatResult = await chatRepository.sendMessage('ping from mobile test');
          
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('✅ Health: ${healthResult['message']}\n💬 Chat: ${chatResult.content.length > 50 ? chatResult.content.substring(0, 50) + '...' : chatResult.content}'),
              backgroundColor: Colors.green,
              duration: const Duration(seconds: 5),
            ),
          );
        } catch (chatError) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('✅ Health: ${healthResult['message']}\n❌ Chat: $chatError'),
              backgroundColor: Colors.orange,
              duration: const Duration(seconds: 5),
            ),
          );
        }
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('❌ ${healthResult['message']}'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('❌ Error: ${e.toString()}'),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 3),
        ),
      );
    }
  }
}