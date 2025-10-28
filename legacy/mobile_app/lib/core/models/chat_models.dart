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
}

@freezed
class AppConfig with _$AppConfig {
  const factory AppConfig({
    required AppInfo app,
    required ApiConfig api,
    required FeatureConfig features,
    required UiConfig ui,
    required SecurityConfig security,
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
