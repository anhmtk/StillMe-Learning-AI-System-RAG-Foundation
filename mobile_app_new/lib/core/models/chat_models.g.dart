// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'chat_models.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$ChatMessageImpl _$$ChatMessageImplFromJson(Map<String, dynamic> json) =>
    _$ChatMessageImpl(
      id: json['id'] as String,
      content: json['content'] as String,
      role: $enumDecode(_$MessageRoleEnumMap, json['role']),
      timestamp: DateTime.parse(json['timestamp'] as String),
      model: json['model'] as String?,
      usage: json['usage'] == null
          ? null
          : ChatUsage.fromJson(json['usage'] as Map<String, dynamic>),
      latencyMs: (json['latencyMs'] as num?)?.toInt(),
      costEstimateUsd: (json['costEstimateUsd'] as num?)?.toDouble(),
      routing: json['routing'] == null
          ? null
          : ChatRouting.fromJson(json['routing'] as Map<String, dynamic>),
      safety: json['safety'] == null
          ? null
          : ChatSafety.fromJson(json['safety'] as Map<String, dynamic>),
      isTyping: json['isTyping'] as bool? ?? false,
    );

Map<String, dynamic> _$$ChatMessageImplToJson(_$ChatMessageImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'content': instance.content,
      'role': _$MessageRoleEnumMap[instance.role]!,
      'timestamp': instance.timestamp.toIso8601String(),
      'model': instance.model,
      'usage': instance.usage,
      'latencyMs': instance.latencyMs,
      'costEstimateUsd': instance.costEstimateUsd,
      'routing': instance.routing,
      'safety': instance.safety,
      'isTyping': instance.isTyping,
    };

const _$MessageRoleEnumMap = {
  MessageRole.user: 'user',
  MessageRole.assistant: 'assistant',
  MessageRole.system: 'system',
};

_$ChatUsageImpl _$$ChatUsageImplFromJson(Map<String, dynamic> json) =>
    _$ChatUsageImpl(
      promptTokens: (json['promptTokens'] as num?)?.toInt() ?? 0,
      completionTokens: (json['completionTokens'] as num?)?.toInt() ?? 0,
      totalTokens: (json['totalTokens'] as num?)?.toInt() ?? 0,
    );

Map<String, dynamic> _$$ChatUsageImplToJson(_$ChatUsageImpl instance) =>
    <String, dynamic>{
      'promptTokens': instance.promptTokens,
      'completionTokens': instance.completionTokens,
      'totalTokens': instance.totalTokens,
    };

_$ChatRoutingImpl _$$ChatRoutingImplFromJson(Map<String, dynamic> json) =>
    _$ChatRoutingImpl(
      selected: json['selected'] as String,
      candidates: (json['candidates'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
    );

Map<String, dynamic> _$$ChatRoutingImplToJson(_$ChatRoutingImpl instance) =>
    <String, dynamic>{
      'selected': instance.selected,
      'candidates': instance.candidates,
    };

_$ChatSafetyImpl _$$ChatSafetyImplFromJson(Map<String, dynamic> json) =>
    _$ChatSafetyImpl(
      filtered: json['filtered'] as bool? ?? false,
      flags:
          (json['flags'] as List<dynamic>?)?.map((e) => e as String).toList() ??
              const [],
    );

Map<String, dynamic> _$$ChatSafetyImplToJson(_$ChatSafetyImpl instance) =>
    <String, dynamic>{
      'filtered': instance.filtered,
      'flags': instance.flags,
    };

_$ChatRequestImpl _$$ChatRequestImplFromJson(Map<String, dynamic> json) =>
    _$ChatRequestImpl(
      message: json['message'] as String,
      sessionId: json['sessionId'] as String,
      metadata: json['metadata'] == null
          ? null
          : ChatMetadata.fromJson(json['metadata'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$ChatRequestImplToJson(_$ChatRequestImpl instance) =>
    <String, dynamic>{
      'message': instance.message,
      'sessionId': instance.sessionId,
      'metadata': instance.metadata,
    };

_$ChatMetadataImpl _$$ChatMetadataImplFromJson(Map<String, dynamic> json) =>
    _$ChatMetadataImpl(
      persona: json['persona'] as String?,
      language: json['language'] as String? ?? 'vi',
      founderCommand: json['founderCommand'] as String?,
      debug: json['debug'] as bool? ?? false,
    );

Map<String, dynamic> _$$ChatMetadataImplToJson(_$ChatMetadataImpl instance) =>
    <String, dynamic>{
      'persona': instance.persona,
      'language': instance.language,
      'founderCommand': instance.founderCommand,
      'debug': instance.debug,
    };

_$ChatResponseImpl _$$ChatResponseImplFromJson(Map<String, dynamic> json) =>
    _$ChatResponseImpl(
      text: json['text'] as String,
      model: json['model'] as String?,
      usage: json['usage'] == null
          ? null
          : ChatUsage.fromJson(json['usage'] as Map<String, dynamic>),
      latencyMs: (json['latencyMs'] as num?)?.toInt(),
      costEstimateUsd: (json['costEstimateUsd'] as num?)?.toDouble(),
      routing: json['routing'] == null
          ? null
          : ChatRouting.fromJson(json['routing'] as Map<String, dynamic>),
      safety: json['safety'] == null
          ? null
          : ChatSafety.fromJson(json['safety'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$ChatResponseImplToJson(_$ChatResponseImpl instance) =>
    <String, dynamic>{
      'text': instance.text,
      'model': instance.model,
      'usage': instance.usage,
      'latencyMs': instance.latencyMs,
      'costEstimateUsd': instance.costEstimateUsd,
      'routing': instance.routing,
      'safety': instance.safety,
    };

_$HealthResponseImpl _$$HealthResponseImplFromJson(Map<String, dynamic> json) =>
    _$HealthResponseImpl(
      status: json['status'] as String,
      timestamp: json['timestamp'] as String?,
      service: json['service'] as String?,
    );

Map<String, dynamic> _$$HealthResponseImplToJson(
        _$HealthResponseImpl instance) =>
    <String, dynamic>{
      'status': instance.status,
      'timestamp': instance.timestamp,
      'service': instance.service,
    };

_$TelemetryDataImpl _$$TelemetryDataImplFromJson(Map<String, dynamic> json) =>
    _$TelemetryDataImpl(
      model: json['model'] as String,
      usage: ChatUsage.fromJson(json['usage'] as Map<String, dynamic>),
      latencyMs: (json['latencyMs'] as num).toInt(),
      costEstimateUsd: (json['costEstimateUsd'] as num).toDouble(),
      timestamp: DateTime.parse(json['timestamp'] as String),
      error: json['error'] as String?,
    );

Map<String, dynamic> _$$TelemetryDataImplToJson(_$TelemetryDataImpl instance) =>
    <String, dynamic>{
      'model': instance.model,
      'usage': instance.usage,
      'latencyMs': instance.latencyMs,
      'costEstimateUsd': instance.costEstimateUsd,
      'timestamp': instance.timestamp.toIso8601String(),
      'error': instance.error,
    };

_$SessionMetricsImpl _$$SessionMetricsImplFromJson(Map<String, dynamic> json) =>
    _$SessionMetricsImpl(
      totalMessages: (json['totalMessages'] as num?)?.toInt() ?? 0,
      totalTokens: (json['totalTokens'] as num?)?.toInt() ?? 0,
      totalCost: (json['totalCost'] as num?)?.toDouble() ?? 0,
      averageLatency: (json['averageLatency'] as num?)?.toInt() ?? 0,
      modelsUsed: (json['modelsUsed'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      errorCount: (json['errorCount'] as num?)?.toInt() ?? 0,
      sessionStart: DateTime.parse(json['sessionStart'] as String),
    );

Map<String, dynamic> _$$SessionMetricsImplToJson(
        _$SessionMetricsImpl instance) =>
    <String, dynamic>{
      'totalMessages': instance.totalMessages,
      'totalTokens': instance.totalTokens,
      'totalCost': instance.totalCost,
      'averageLatency': instance.averageLatency,
      'modelsUsed': instance.modelsUsed,
      'errorCount': instance.errorCount,
      'sessionStart': instance.sessionStart.toIso8601String(),
    };

_$QuickActionImpl _$$QuickActionImplFromJson(Map<String, dynamic> json) =>
    _$QuickActionImpl(
      id: json['id'] as String,
      title: json['title'] as String,
      description: json['description'] as String,
      command: json['command'] as String,
      type: $enumDecode(_$QuickActionTypeEnumMap, json['type']),
      icon: json['icon'] as String?,
    );

Map<String, dynamic> _$$QuickActionImplToJson(_$QuickActionImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'title': instance.title,
      'description': instance.description,
      'command': instance.command,
      'type': _$QuickActionTypeEnumMap[instance.type]!,
      'icon': instance.icon,
    };

const _$QuickActionTypeEnumMap = {
  QuickActionType.persona: 'persona',
  QuickActionType.translate: 'translate',
  QuickActionType.devRoute: 'devRoute',
  QuickActionType.clear: 'clear',
  QuickActionType.export: 'export',
  QuickActionType.founder: 'founder',
  QuickActionType.nicheRadar: 'nicheRadar',
  QuickActionType.webSearch: 'webSearch',
};

_$AppConfigImpl _$$AppConfigImplFromJson(Map<String, dynamic> json) =>
    _$AppConfigImpl(
      app: AppInfo.fromJson(json['app'] as Map<String, dynamic>),
      api: ApiConfig.fromJson(json['api'] as Map<String, dynamic>),
      features:
          FeatureConfig.fromJson(json['features'] as Map<String, dynamic>),
      ui: UiConfig.fromJson(json['ui'] as Map<String, dynamic>),
      security:
          SecurityConfig.fromJson(json['security'] as Map<String, dynamic>),
      nicheRadar:
          NicheRadarConfig.fromJson(json['nicheRadar'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$AppConfigImplToJson(_$AppConfigImpl instance) =>
    <String, dynamic>{
      'app': instance.app,
      'api': instance.api,
      'features': instance.features,
      'ui': instance.ui,
      'security': instance.security,
      'nicheRadar': instance.nicheRadar,
    };

_$AppInfoImpl _$$AppInfoImplFromJson(Map<String, dynamic> json) =>
    _$AppInfoImpl(
      name: json['name'] as String,
      version: json['version'] as String,
      founder: json['founder'] as String,
      description: json['description'] as String,
    );

Map<String, dynamic> _$$AppInfoImplToJson(_$AppInfoImpl instance) =>
    <String, dynamic>{
      'name': instance.name,
      'version': instance.version,
      'founder': instance.founder,
      'description': instance.description,
    };

_$ApiConfigImpl _$$ApiConfigImplFromJson(Map<String, dynamic> json) =>
    _$ApiConfigImpl(
      baseUrl: json['baseUrl'] as String,
      timeout: (json['timeout'] as num?)?.toInt() ?? 30000,
      retryAttempts: (json['retryAttempts'] as num?)?.toInt() ?? 3,
      endpoints:
          ApiEndpoints.fromJson(json['endpoints'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$ApiConfigImplToJson(_$ApiConfigImpl instance) =>
    <String, dynamic>{
      'baseUrl': instance.baseUrl,
      'timeout': instance.timeout,
      'retryAttempts': instance.retryAttempts,
      'endpoints': instance.endpoints,
    };

_$ApiEndpointsImpl _$$ApiEndpointsImplFromJson(Map<String, dynamic> json) =>
    _$ApiEndpointsImpl(
      health: json['health'] as String,
      chat: json['chat'] as String,
      nicheRadar: json['nicheRadar'] as String,
      webSearch: json['webSearch'] as String,
    );

Map<String, dynamic> _$$ApiEndpointsImplToJson(_$ApiEndpointsImpl instance) =>
    <String, dynamic>{
      'health': instance.health,
      'chat': instance.chat,
      'nicheRadar': instance.nicheRadar,
      'webSearch': instance.webSearch,
    };

_$FeatureConfigImpl _$$FeatureConfigImplFromJson(Map<String, dynamic> json) =>
    _$FeatureConfigImpl(
      founderMode: json['founderMode'] as bool? ?? false,
      telemetry: json['telemetry'] as bool? ?? true,
      autoTranslate: json['autoTranslate'] as bool? ?? false,
      safetyLevel: json['safetyLevel'] as String? ?? 'normal',
      tokenCap: (json['tokenCap'] as num?)?.toInt() ?? 4000,
      maxLatency: (json['maxLatency'] as num?)?.toInt() ?? 10000,
      nicheRadar: json['nicheRadar'] as bool? ?? true,
      webSearch: json['webSearch'] as bool? ?? true,
      languageDetection: json['languageDetection'] as bool? ?? true,
      performanceMetrics: json['performanceMetrics'] as bool? ?? true,
    );

Map<String, dynamic> _$$FeatureConfigImplToJson(_$FeatureConfigImpl instance) =>
    <String, dynamic>{
      'founderMode': instance.founderMode,
      'telemetry': instance.telemetry,
      'autoTranslate': instance.autoTranslate,
      'safetyLevel': instance.safetyLevel,
      'tokenCap': instance.tokenCap,
      'maxLatency': instance.maxLatency,
      'nicheRadar': instance.nicheRadar,
      'webSearch': instance.webSearch,
      'languageDetection': instance.languageDetection,
      'performanceMetrics': instance.performanceMetrics,
    };

_$UiConfigImpl _$$UiConfigImplFromJson(Map<String, dynamic> json) =>
    _$UiConfigImpl(
      theme: json['theme'] as String? ?? 'dark',
      primaryColor: json['primaryColor'] as String? ?? '#0F172A',
      secondaryColor: json['secondaryColor'] as String? ?? '#1E293B',
      accentColor: json['accentColor'] as String? ?? '#3B82F6',
      fontFamily: json['fontFamily'] as String? ?? 'Inter',
      gradientColors: (json['gradientColors'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const ['#8B5CF6', '#06B6D4'],
      animationDuration: (json['animationDuration'] as num?)?.toInt() ?? 300,
    );

Map<String, dynamic> _$$UiConfigImplToJson(_$UiConfigImpl instance) =>
    <String, dynamic>{
      'theme': instance.theme,
      'primaryColor': instance.primaryColor,
      'secondaryColor': instance.secondaryColor,
      'accentColor': instance.accentColor,
      'fontFamily': instance.fontFamily,
      'gradientColors': instance.gradientColors,
      'animationDuration': instance.animationDuration,
    };

_$SecurityConfigImpl _$$SecurityConfigImplFromJson(Map<String, dynamic> json) =>
    _$SecurityConfigImpl(
      founderPasscode: json['founderPasscode'] as String? ?? '0000',
      enableBiometrics: json['enableBiometrics'] as bool? ?? false,
      sessionTimeout: (json['sessionTimeout'] as num?)?.toInt() ?? 3600,
    );

Map<String, dynamic> _$$SecurityConfigImplToJson(
        _$SecurityConfigImpl instance) =>
    <String, dynamic>{
      'founderPasscode': instance.founderPasscode,
      'enableBiometrics': instance.enableBiometrics,
      'sessionTimeout': instance.sessionTimeout,
    };

_$NicheRadarConfigImpl _$$NicheRadarConfigImplFromJson(
        Map<String, dynamic> json) =>
    _$NicheRadarConfigImpl(
      enabled: json['enabled'] as bool? ?? true,
      autoRefresh: json['autoRefresh'] as bool? ?? false,
      refreshInterval: (json['refreshInterval'] as num?)?.toInt() ?? 300000,
      maxResults: (json['maxResults'] as num?)?.toInt() ?? 10,
      confidenceThreshold:
          (json['confidenceThreshold'] as num?)?.toDouble() ?? 0.7,
    );

Map<String, dynamic> _$$NicheRadarConfigImplToJson(
        _$NicheRadarConfigImpl instance) =>
    <String, dynamic>{
      'enabled': instance.enabled,
      'autoRefresh': instance.autoRefresh,
      'refreshInterval': instance.refreshInterval,
      'maxResults': instance.maxResults,
      'confidenceThreshold': instance.confidenceThreshold,
    };

_$NicheOpportunityImpl _$$NicheOpportunityImplFromJson(
        Map<String, dynamic> json) =>
    _$NicheOpportunityImpl(
      topic: json['topic'] as String,
      score: (json['score'] as num).toDouble(),
      confidence: (json['confidence'] as num).toDouble(),
      keySignals: (json['keySignals'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      sources: (json['sources'] as List<dynamic>)
          .map((e) => NicheSource.fromJson(e as Map<String, dynamic>))
          .toList(),
      category: json['category'] as String,
      timestamp: DateTime.parse(json['timestamp'] as String),
      description: json['description'] as String?,
      recommendations: (json['recommendations'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList(),
    );

Map<String, dynamic> _$$NicheOpportunityImplToJson(
        _$NicheOpportunityImpl instance) =>
    <String, dynamic>{
      'topic': instance.topic,
      'score': instance.score,
      'confidence': instance.confidence,
      'keySignals': instance.keySignals,
      'sources': instance.sources,
      'category': instance.category,
      'timestamp': instance.timestamp.toIso8601String(),
      'description': instance.description,
      'recommendations': instance.recommendations,
    };

_$NicheSourceImpl _$$NicheSourceImplFromJson(Map<String, dynamic> json) =>
    _$NicheSourceImpl(
      name: json['name'] as String,
      url: json['url'] as String,
      domain: json['domain'] as String,
      timestamp: DateTime.parse(json['timestamp'] as String),
      snippet: json['snippet'] as String?,
    );

Map<String, dynamic> _$$NicheSourceImplToJson(_$NicheSourceImpl instance) =>
    <String, dynamic>{
      'name': instance.name,
      'url': instance.url,
      'domain': instance.domain,
      'timestamp': instance.timestamp.toIso8601String(),
      'snippet': instance.snippet,
    };

_$NicheRadarResponseImpl _$$NicheRadarResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$NicheRadarResponseImpl(
      opportunities: (json['opportunities'] as List<dynamic>)
          .map((e) => NicheOpportunity.fromJson(e as Map<String, dynamic>))
          .toList(),
      generatedAt: DateTime.parse(json['generatedAt'] as String),
      totalSources: (json['totalSources'] as num).toInt(),
      error: json['error'] as String?,
    );

Map<String, dynamic> _$$NicheRadarResponseImplToJson(
        _$NicheRadarResponseImpl instance) =>
    <String, dynamic>{
      'opportunities': instance.opportunities,
      'generatedAt': instance.generatedAt.toIso8601String(),
      'totalSources': instance.totalSources,
      'error': instance.error,
    };

_$PlaybookRequestImpl _$$PlaybookRequestImplFromJson(
        Map<String, dynamic> json) =>
    _$PlaybookRequestImpl(
      topic: json['topic'] as String,
      score: (json['score'] as num).toDouble(),
      confidence: (json['confidence'] as num).toDouble(),
    );

Map<String, dynamic> _$$PlaybookRequestImplToJson(
        _$PlaybookRequestImpl instance) =>
    <String, dynamic>{
      'topic': instance.topic,
      'score': instance.score,
      'confidence': instance.confidence,
    };

_$PlaybookResponseImpl _$$PlaybookResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$PlaybookResponseImpl(
      topic: json['topic'] as String,
      productBrief:
          ProductBrief.fromJson(json['productBrief'] as Map<String, dynamic>),
      mvpSpec: MVPSpec.fromJson(json['mvpSpec'] as Map<String, dynamic>),
      pricingSuggestion: PricingSuggestion.fromJson(
          json['pricingSuggestion'] as Map<String, dynamic>),
      assets:
          (json['assets'] as List<dynamic>).map((e) => e as String).toList(),
      generatedAt: DateTime.parse(json['generatedAt'] as String),
      error: json['error'] as String?,
    );

Map<String, dynamic> _$$PlaybookResponseImplToJson(
        _$PlaybookResponseImpl instance) =>
    <String, dynamic>{
      'topic': instance.topic,
      'productBrief': instance.productBrief,
      'mvpSpec': instance.mvpSpec,
      'pricingSuggestion': instance.pricingSuggestion,
      'assets': instance.assets,
      'generatedAt': instance.generatedAt.toIso8601String(),
      'error': instance.error,
    };

_$ProductBriefImpl _$$ProductBriefImplFromJson(Map<String, dynamic> json) =>
    _$ProductBriefImpl(
      title: json['title'] as String,
      description: json['description'] as String,
      persona: json['persona'] as String,
      painPoints: (json['painPoints'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      jobToBeDone: (json['jobToBeDone'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      uniqueSellingProposition: json['uniqueSellingProposition'] as String,
    );

Map<String, dynamic> _$$ProductBriefImplToJson(_$ProductBriefImpl instance) =>
    <String, dynamic>{
      'title': instance.title,
      'description': instance.description,
      'persona': instance.persona,
      'painPoints': instance.painPoints,
      'jobToBeDone': instance.jobToBeDone,
      'uniqueSellingProposition': instance.uniqueSellingProposition,
    };

_$MVPSpecImpl _$$MVPSpecImplFromJson(Map<String, dynamic> json) =>
    _$MVPSpecImpl(
      features: (json['features'] as List<dynamic>)
          .map((e) => Feature.fromJson(e as Map<String, dynamic>))
          .toList(),
      estimatedDevelopmentDays:
          (json['estimatedDevelopmentDays'] as num).toInt(),
      architecture: json['architecture'] as String,
      dependencies: (json['dependencies'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
    );

Map<String, dynamic> _$$MVPSpecImplToJson(_$MVPSpecImpl instance) =>
    <String, dynamic>{
      'features': instance.features,
      'estimatedDevelopmentDays': instance.estimatedDevelopmentDays,
      'architecture': instance.architecture,
      'dependencies': instance.dependencies,
    };

_$FeatureImpl _$$FeatureImplFromJson(Map<String, dynamic> json) =>
    _$FeatureImpl(
      name: json['name'] as String,
      description: json['description'] as String,
      estimatedHours: (json['estimatedHours'] as num).toInt(),
      priority: json['priority'] as String,
    );

Map<String, dynamic> _$$FeatureImplToJson(_$FeatureImpl instance) =>
    <String, dynamic>{
      'name': instance.name,
      'description': instance.description,
      'estimatedHours': instance.estimatedHours,
      'priority': instance.priority,
    };

_$PricingSuggestionImpl _$$PricingSuggestionImplFromJson(
        Map<String, dynamic> json) =>
    _$PricingSuggestionImpl(
      tiers: (json['tiers'] as List<dynamic>)
          .map((e) => PricingTier.fromJson(e as Map<String, dynamic>))
          .toList(),
      rationale: json['rationale'] as String,
    );

Map<String, dynamic> _$$PricingSuggestionImplToJson(
        _$PricingSuggestionImpl instance) =>
    <String, dynamic>{
      'tiers': instance.tiers,
      'rationale': instance.rationale,
    };

_$PricingTierImpl _$$PricingTierImplFromJson(Map<String, dynamic> json) =>
    _$PricingTierImpl(
      name: json['name'] as String,
      price: (json['price'] as num).toDouble(),
      rationale: json['rationale'] as String,
      features:
          (json['features'] as List<dynamic>).map((e) => e as String).toList(),
    );

Map<String, dynamic> _$$PricingTierImplToJson(_$PricingTierImpl instance) =>
    <String, dynamic>{
      'name': instance.name,
      'price': instance.price,
      'rationale': instance.rationale,
      'features': instance.features,
    };
