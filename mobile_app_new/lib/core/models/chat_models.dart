import 'package:freezed_annotation/freezed_annotation.dart';

part 'chat_models.freezed.dart';
part 'chat_models.g.dart';

@freezed
class ChatMessage with _$ChatMessage {
  const factory ChatMessage({
    required String id,
    required String content,
    required MessageRole role,
    required DateTime timestamp,
    String? model,
    ChatUsage? usage,
    int? latencyMs,
    double? costEstimateUsd,
    ChatRouting? routing,
    ChatSafety? safety,
    @Default(false) bool isTyping,
  }) = _ChatMessage;

  factory ChatMessage.fromJson(Map<String, dynamic> json) =>
      _$ChatMessageFromJson(json);
}

@freezed
class ChatUsage with _$ChatUsage {
  const factory ChatUsage({
    @Default(0) int promptTokens,
    @Default(0) int completionTokens,
    @Default(0) int totalTokens,
  }) = _ChatUsage;

  factory ChatUsage.fromJson(Map<String, dynamic> json) =>
      _$ChatUsageFromJson(json);
}

@freezed
class ChatRouting with _$ChatRouting {
  const factory ChatRouting({
    required String selected,
    @Default([]) List<String> candidates,
  }) = _ChatRouting;

  factory ChatRouting.fromJson(Map<String, dynamic> json) =>
      _$ChatRoutingFromJson(json);
}

@freezed
class ChatSafety with _$ChatSafety {
  const factory ChatSafety({
    @Default(false) bool filtered,
    @Default([]) List<String> flags,
  }) = _ChatSafety;

  factory ChatSafety.fromJson(Map<String, dynamic> json) =>
      _$ChatSafetyFromJson(json);
}

@freezed
class ChatRequest with _$ChatRequest {
  const factory ChatRequest({
    required String message,
    required String sessionId,
    ChatMetadata? metadata,
  }) = _ChatRequest;

  factory ChatRequest.fromJson(Map<String, dynamic> json) =>
      _$ChatRequestFromJson(json);
}

@freezed
class ChatMetadata with _$ChatMetadata {
  const factory ChatMetadata({
    String? persona,
    @Default('vi') String language,
    String? founderCommand,
    @Default(false) bool debug,
  }) = _ChatMetadata;

  factory ChatMetadata.fromJson(Map<String, dynamic> json) =>
      _$ChatMetadataFromJson(json);
}

@freezed
class ChatResponse with _$ChatResponse {
  const factory ChatResponse({
    required String text,
    String? model,
    ChatUsage? usage,
    int? latencyMs,
    double? costEstimateUsd,
    ChatRouting? routing,
    ChatSafety? safety,
  }) = _ChatResponse;

  factory ChatResponse.fromJson(Map<String, dynamic> json) =>
      _$ChatResponseFromJson(json);
}

@freezed
class HealthResponse with _$HealthResponse {
  const factory HealthResponse({
    required String status,
    String? timestamp,
    String? service,
  }) = _HealthResponse;

  factory HealthResponse.fromJson(Map<String, dynamic> json) =>
      _$HealthResponseFromJson(json);
}

enum MessageRole {
  @JsonValue('user')
  user,
  @JsonValue('assistant')
  assistant,
  @JsonValue('system')
  system,
}

@freezed
class TelemetryData with _$TelemetryData {
  const factory TelemetryData({
    required String model,
    required ChatUsage usage,
    required int latencyMs,
    required double costEstimateUsd,
    required DateTime timestamp,
    String? error,
  }) = _TelemetryData;

  factory TelemetryData.fromJson(Map<String, dynamic> json) =>
      _$TelemetryDataFromJson(json);
}

@freezed
class SessionMetrics with _$SessionMetrics {
  const factory SessionMetrics({
    @Default(0) int totalMessages,
    @Default(0) int totalTokens,
    @Default(0) double totalCost,
    @Default(0) int averageLatency,
    @Default([]) List<String> modelsUsed,
    @Default(0) int errorCount,
    required DateTime sessionStart,
  }) = _SessionMetrics;

  factory SessionMetrics.fromJson(Map<String, dynamic> json) =>
      _$SessionMetricsFromJson(json);
}

@freezed
class QuickAction with _$QuickAction {
  const factory QuickAction({
    required String id,
    required String title,
    required String description,
    required String command,
    required QuickActionType type,
    String? icon,
  }) = _QuickAction;

  factory QuickAction.fromJson(Map<String, dynamic> json) =>
      _$QuickActionFromJson(json);
}

enum QuickActionType {
  persona,
  translate,
  devRoute,
  clear,
  export,
  founder,
  nicheRadar,
  webSearch,
}

@freezed
class AppConfig with _$AppConfig {
  const factory AppConfig({
    required AppInfo app,
    required ApiConfig api,
    required FeatureConfig features,
    required UiConfig ui,
    required SecurityConfig security,
    required NicheRadarConfig nicheRadar,
  }) = _AppConfig;

  factory AppConfig.fromJson(Map<String, dynamic> json) =>
      _$AppConfigFromJson(json);
}

@freezed
class AppInfo with _$AppInfo {
  const factory AppInfo({
    required String name,
    required String version,
    required String founder,
    required String description,
  }) = _AppInfo;

  factory AppInfo.fromJson(Map<String, dynamic> json) =>
      _$AppInfoFromJson(json);
}

@freezed
class ApiConfig with _$ApiConfig {
  const factory ApiConfig({
    required String baseUrl,
    @Default(30000) int timeout,
    @Default(3) int retryAttempts,
    required ApiEndpoints endpoints,
  }) = _ApiConfig;

  factory ApiConfig.fromJson(Map<String, dynamic> json) =>
      _$ApiConfigFromJson(json);
}

@freezed
class ApiEndpoints with _$ApiEndpoints {
  const factory ApiEndpoints({
    required String health,
    required String chat,
    required String nicheRadar,
    required String webSearch,
  }) = _ApiEndpoints;

  factory ApiEndpoints.fromJson(Map<String, dynamic> json) =>
      _$ApiEndpointsFromJson(json);
}

@freezed
class FeatureConfig with _$FeatureConfig {
  const factory FeatureConfig({
    @Default(false) bool founderMode,
    @Default(true) bool telemetry,
    @Default(false) bool autoTranslate,
    @Default('normal') String safetyLevel,
    @Default(4000) int tokenCap,
    @Default(10000) int maxLatency,
    @Default(true) bool nicheRadar,
    @Default(true) bool webSearch,
    @Default(true) bool languageDetection,
    @Default(true) bool performanceMetrics,
  }) = _FeatureConfig;

  factory FeatureConfig.fromJson(Map<String, dynamic> json) =>
      _$FeatureConfigFromJson(json);
}

@freezed
class UiConfig with _$UiConfig {
  const factory UiConfig({
    @Default('dark') String theme,
    @Default('#0F172A') String primaryColor,
    @Default('#1E293B') String secondaryColor,
    @Default('#3B82F6') String accentColor,
    @Default('Inter') String fontFamily,
    @Default(['#8B5CF6', '#06B6D4']) List<String> gradientColors,
    @Default(300) int animationDuration,
  }) = _UiConfig;

  factory UiConfig.fromJson(Map<String, dynamic> json) =>
      _$UiConfigFromJson(json);
}

@freezed
class SecurityConfig with _$SecurityConfig {
  const factory SecurityConfig({
    @Default('0000') String founderPasscode,
    @Default(false) bool enableBiometrics,
    @Default(3600) int sessionTimeout,
  }) = _SecurityConfig;

  factory SecurityConfig.fromJson(Map<String, dynamic> json) =>
      _$SecurityConfigFromJson(json);
}

// NicheRadar Models
@freezed
class NicheRadarConfig with _$NicheRadarConfig {
  const factory NicheRadarConfig({
    @Default(true) bool enabled,
    @Default(false) bool autoRefresh,
    @Default(300000) int refreshInterval,
    @Default(10) int maxResults,
    @Default(0.7) double confidenceThreshold,
  }) = _NicheRadarConfig;

  factory NicheRadarConfig.fromJson(Map<String, dynamic> json) =>
      _$NicheRadarConfigFromJson(json);
}

@freezed
class NicheOpportunity with _$NicheOpportunity {
  const factory NicheOpportunity({
    required String topic,
    required double score,
    required double confidence,
    required List<String> keySignals,
    required List<NicheSource> sources,
    required String category,
    required DateTime timestamp,
    String? description,
    List<String>? recommendations,
  }) = _NicheOpportunity;

  factory NicheOpportunity.fromJson(Map<String, dynamic> json) =>
      _$NicheOpportunityFromJson(json);
}

@freezed
class NicheSource with _$NicheSource {
  const factory NicheSource({
    required String name,
    required String url,
    required String domain,
    required DateTime timestamp,
    String? snippet,
  }) = _NicheSource;

  factory NicheSource.fromJson(Map<String, dynamic> json) =>
      _$NicheSourceFromJson(json);
}

@freezed
class NicheRadarResponse with _$NicheRadarResponse {
  const factory NicheRadarResponse({
    required List<NicheOpportunity> opportunities,
    required DateTime generatedAt,
    required int totalSources,
    String? error,
  }) = _NicheRadarResponse;

  factory NicheRadarResponse.fromJson(Map<String, dynamic> json) =>
      _$NicheRadarResponseFromJson(json);
}

@freezed
class PlaybookRequest with _$PlaybookRequest {
  const factory PlaybookRequest({
    required String topic,
    required double score,
    required double confidence,
  }) = _PlaybookRequest;

  factory PlaybookRequest.fromJson(Map<String, dynamic> json) =>
      _$PlaybookRequestFromJson(json);
}

@freezed
class PlaybookResponse with _$PlaybookResponse {
  const factory PlaybookResponse({
    required String topic,
    required ProductBrief productBrief,
    required MVPSpec mvpSpec,
    required PricingSuggestion pricingSuggestion,
    required List<String> assets,
    required DateTime generatedAt,
    String? error,
  }) = _PlaybookResponse;

  factory PlaybookResponse.fromJson(Map<String, dynamic> json) =>
      _$PlaybookResponseFromJson(json);
}

@freezed
class ProductBrief with _$ProductBrief {
  const factory ProductBrief({
    required String title,
    required String description,
    required String persona,
    required List<String> painPoints,
    required List<String> jobToBeDone,
    required String uniqueSellingProposition,
  }) = _ProductBrief;

  factory ProductBrief.fromJson(Map<String, dynamic> json) =>
      _$ProductBriefFromJson(json);
}

@freezed
class MVPSpec with _$MVPSpec {
  const factory MVPSpec({
    required List<Feature> features,
    required int estimatedDevelopmentDays,
    required String architecture,
    required List<String> dependencies,
  }) = _MVPSpec;

  factory MVPSpec.fromJson(Map<String, dynamic> json) =>
      _$MVPSpecFromJson(json);
}

@freezed
class Feature with _$Feature {
  const factory Feature({
    required String name,
    required String description,
    required int estimatedHours,
    required String priority,
  }) = _Feature;

  factory Feature.fromJson(Map<String, dynamic> json) =>
      _$FeatureFromJson(json);
}

@freezed
class PricingSuggestion with _$PricingSuggestion {
  const factory PricingSuggestion({
    required List<PricingTier> tiers,
    required String rationale,
  }) = _PricingSuggestion;

  factory PricingSuggestion.fromJson(Map<String, dynamic> json) =>
      _$PricingSuggestionFromJson(json);
}

@freezed
class PricingTier with _$PricingTier {
  const factory PricingTier({
    required String name,
    required double price,
    required String rationale,
    required List<String> features,
  }) = _PricingTier;

  factory PricingTier.fromJson(Map<String, dynamic> json) =>
      _$PricingTierFromJson(json);
}