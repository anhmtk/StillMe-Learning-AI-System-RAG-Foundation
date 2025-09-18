import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/models/chat_models.dart';

class TelemetryStrip extends ConsumerStatefulWidget {
  const TelemetryStrip({super.key});

  @override
  ConsumerState<TelemetryStrip> createState() => _TelemetryStripState();
}

class _TelemetryStripState extends ConsumerState<TelemetryStrip>
    with TickerProviderStateMixin {
  bool _isExpanded = false;
  late AnimationController _animationController;
  late Animation<double> _expandAnimation;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _expandAnimation = CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    );
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  void _toggleExpanded() {
    setState(() {
      _isExpanded = !_isExpanded;
    });
    
    if (_isExpanded) {
      _animationController.forward();
    } else {
      _animationController.reverse();
    }
  }

  @override
  Widget build(BuildContext context) {
    // TODO: Replace with actual telemetry data from provider
    final telemetry = TelemetryData(
      model: 'gemma2:2b',
      usage: const ChatUsage(
        promptTokens: 20,
        completionTokens: 35,
        totalTokens: 55,
      ),
      latencyMs: 840,
      costEstimateUsd: 0.0008,
      timestamp: DateTime.now(),
    );

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: AppTheme.spacingL),
      decoration: BoxDecoration(
        color: AppTheme.telemetryBackground,
        borderRadius: BorderRadius.circular(AppTheme.radiusM),
        border: Border.all(
          color: AppTheme.surfaceColor,
          width: 1,
        ),
      ),
      child: Column(
        children: [
          // Collapsed View
          InkWell(
            onTap: _toggleExpanded,
            borderRadius: BorderRadius.circular(AppTheme.radiusM),
            child: Container(
              padding: const EdgeInsets.symmetric(
                horizontal: AppTheme.spacingM,
                vertical: AppTheme.spacingS,
              ),
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    // Model Indicator
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: AppTheme.spacingS,
                        vertical: AppTheme.spacingXS,
                      ),
                      decoration: BoxDecoration(
                        color: AppTheme.accentColor.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(AppTheme.radiusS),
                      ),
                      child: Text(
                        telemetry.model,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: AppTheme.accentColor,
                          fontWeight: FontWeight.w600,
                          fontSize: 11,
                        ),
                      ),
                    ),
                    
                    const SizedBox(width: AppTheme.spacingS),
                    
                    // Latency
                    _buildMetricChip(
                      context,
                      icon: Icons.speed,
                      value: '${telemetry.latencyMs}ms',
                      color: _getLatencyColor(telemetry.latencyMs),
                    ),
                    
                    const SizedBox(width: AppTheme.spacingS),
                    
                    // Tokens
                    _buildMetricChip(
                      context,
                      icon: Icons.token,
                      value: '${telemetry.usage.totalTokens}',
                      color: AppTheme.successColor,
                    ),
                    
                    const SizedBox(width: AppTheme.spacingS),
                    
                    // Cost
                    _buildMetricChip(
                      context,
                      icon: Icons.attach_money,
                      value: '\$${telemetry.costEstimateUsd.toStringAsFixed(4)}',
                      color: AppTheme.warningColor,
                    ),
                    
                    const SizedBox(width: AppTheme.spacingM),
                    
                    // Expand/Collapse Icon
                    AnimatedRotation(
                      turns: _isExpanded ? 0.5 : 0,
                      duration: const Duration(milliseconds: 300),
                      child: Icon(
                        Icons.keyboard_arrow_down,
                        size: 20,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          
          // Expanded View
          SizeTransition(
            sizeFactor: _expandAnimation,
            child: Container(
              padding: const EdgeInsets.fromLTRB(
                AppTheme.spacingM,
                0,
                AppTheme.spacingM,
                AppTheme.spacingM,
              ),
              child: Column(
                children: [
                  const Divider(color: AppTheme.surfaceColor),
                  const SizedBox(height: AppTheme.spacingM),
                  
                  // Detailed Metrics
                  Row(
                    children: [
                      Expanded(
                        child: _buildDetailedMetric(
                          context,
                          label: 'Prompt Tokens',
                          value: '${telemetry.usage.promptTokens}',
                          icon: Icons.input,
                        ),
                      ),
                      Expanded(
                        child: _buildDetailedMetric(
                          context,
                          label: 'Completion Tokens',
                          value: '${telemetry.usage.completionTokens}',
                          icon: Icons.output,
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: AppTheme.spacingM),
                  
                  Row(
                    children: [
                      Expanded(
                        child: _buildDetailedMetric(
                          context,
                          label: 'Total Tokens',
                          value: '${telemetry.usage.totalTokens}',
                          icon: Icons.token,
                        ),
                      ),
                      Expanded(
                        child: _buildDetailedMetric(
                          context,
                          label: 'Cost Estimate',
                          value: '\$${telemetry.costEstimateUsd.toStringAsFixed(4)}',
                          icon: Icons.attach_money,
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: AppTheme.spacingM),
                  
                  // Session Summary (if available)
                  Container(
                    padding: const EdgeInsets.all(AppTheme.spacingM),
                    decoration: BoxDecoration(
                      color: AppTheme.surfaceColor.withOpacity(0.3),
                      borderRadius: BorderRadius.circular(AppTheme.radiusS),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          Icons.analytics,
                          size: 16,
                          color: AppTheme.accentColor,
                        ),
                        const SizedBox(width: AppTheme.spacingS),
                        Text(
                          'Session: 1 messages • 55 tokens • \$0.0008',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: AppTheme.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricChip(
    BuildContext context, {
    required IconData icon,
    required String value,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppTheme.spacingS,
        vertical: AppTheme.spacingXS,
      ),
      decoration: BoxDecoration(
        color: color.withOpacity(0.2),
        borderRadius: BorderRadius.circular(AppTheme.radiusS),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            size: 12,
            color: color,
          ),
          const SizedBox(width: AppTheme.spacingXS),
          Text(
            value,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: color,
              fontWeight: FontWeight.w600,
              fontSize: 10,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailedMetric(
    BuildContext context, {
    required String label,
    required String value,
    required IconData icon,
  }) {
    return Container(
      padding: const EdgeInsets.all(AppTheme.spacingM),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor.withOpacity(0.3),
        borderRadius: BorderRadius.circular(AppTheme.radiusS),
      ),
      child: Column(
        children: [
          Icon(
            icon,
            size: 20,
            color: AppTheme.accentColor,
          ),
          const SizedBox(height: AppTheme.spacingS),
          Text(
            value,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: AppTheme.spacingXS),
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

  Color _getLatencyColor(int latencyMs) {
    if (latencyMs < 500) return AppTheme.successColor;
    if (latencyMs < 1000) return AppTheme.warningColor;
    return AppTheme.errorColor;
  }
}
