// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'chat_models.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

ChatMessage _$ChatMessageFromJson(Map<String, dynamic> json) {
  return _ChatMessage.fromJson(json);
}

/// @nodoc
mixin _$ChatMessage {
  String get id => throw _privateConstructorUsedError;
  String get content => throw _privateConstructorUsedError;
  MessageRole get role => throw _privateConstructorUsedError;
  DateTime get timestamp => throw _privateConstructorUsedError;
  String? get model => throw _privateConstructorUsedError;
  ChatUsage? get usage => throw _privateConstructorUsedError;
  int? get latencyMs => throw _privateConstructorUsedError;
  double? get costEstimateUsd => throw _privateConstructorUsedError;
  ChatRouting? get routing => throw _privateConstructorUsedError;
  ChatSafety? get safety => throw _privateConstructorUsedError;
  bool get isTyping => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ChatMessageCopyWith<ChatMessage> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ChatMessageCopyWith<$Res> {
  factory $ChatMessageCopyWith(
          ChatMessage value, $Res Function(ChatMessage) then) =
      _$ChatMessageCopyWithImpl<$Res, ChatMessage>;
  @useResult
  $Res call(
      {String id,
      String content,
      MessageRole role,
      DateTime timestamp,
      String? model,
      ChatUsage? usage,
      int? latencyMs,
      double? costEstimateUsd,
      ChatRouting? routing,
      ChatSafety? safety,
      bool isTyping});

  $ChatUsageCopyWith<$Res>? get usage;
  $ChatRoutingCopyWith<$Res>? get routing;
  $ChatSafetyCopyWith<$Res>? get safety;
}

/// @nodoc
class _$ChatMessageCopyWithImpl<$Res, $Val extends ChatMessage>
    implements $ChatMessageCopyWith<$Res> {
  _$ChatMessageCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? content = null,
    Object? role = null,
    Object? timestamp = null,
    Object? model = freezed,
    Object? usage = freezed,
    Object? latencyMs = freezed,
    Object? costEstimateUsd = freezed,
    Object? routing = freezed,
    Object? safety = freezed,
    Object? isTyping = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      content: null == content
          ? _value.content
          : content // ignore: cast_nullable_to_non_nullable
              as String,
      role: null == role
          ? _value.role
          : role // ignore: cast_nullable_to_non_nullable
              as MessageRole,
      timestamp: null == timestamp
          ? _value.timestamp
          : timestamp // ignore: cast_nullable_to_non_nullable
              as DateTime,
      model: freezed == model
          ? _value.model
          : model // ignore: cast_nullable_to_non_nullable
              as String?,
      usage: freezed == usage
          ? _value.usage
          : usage // ignore: cast_nullable_to_non_nullable
              as ChatUsage?,
      latencyMs: freezed == latencyMs
          ? _value.latencyMs
          : latencyMs // ignore: cast_nullable_to_non_nullable
              as int?,
      costEstimateUsd: freezed == costEstimateUsd
          ? _value.costEstimateUsd
          : costEstimateUsd // ignore: cast_nullable_to_non_nullable
              as double?,
      routing: freezed == routing
          ? _value.routing
          : routing // ignore: cast_nullable_to_non_nullable
              as ChatRouting?,
      safety: freezed == safety
          ? _value.safety
          : safety // ignore: cast_nullable_to_non_nullable
              as ChatSafety?,
      isTyping: null == isTyping
          ? _value.isTyping
          : isTyping // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $ChatUsageCopyWith<$Res>? get usage {
    if (_value.usage == null) {
      return null;
    }

    return $ChatUsageCopyWith<$Res>(_value.usage!, (value) {
      return _then(_value.copyWith(usage: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $ChatRoutingCopyWith<$Res>? get routing {
    if (_value.routing == null) {
      return null;
    }

    return $ChatRoutingCopyWith<$Res>(_value.routing!, (value) {
      return _then(_value.copyWith(routing: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $ChatSafetyCopyWith<$Res>? get safety {
    if (_value.safety == null) {
      return null;
    }

    return $ChatSafetyCopyWith<$Res>(_value.safety!, (value) {
      return _then(_value.copyWith(safety: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$ChatMessageImplCopyWith<$Res>
    implements $ChatMessageCopyWith<$Res> {
  factory _$$ChatMessageImplCopyWith(
          _$ChatMessageImpl value, $Res Function(_$ChatMessageImpl) then) =
      __$$ChatMessageImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String content,
      MessageRole role,
      DateTime timestamp,
      String? model,
      ChatUsage? usage,
      int? latencyMs,
      double? costEstimateUsd,
      ChatRouting? routing,
      ChatSafety? safety,
      bool isTyping});

  @override
  $ChatUsageCopyWith<$Res>? get usage;
  @override
  $ChatRoutingCopyWith<$Res>? get routing;
  @override
  $ChatSafetyCopyWith<$Res>? get safety;
}

/// @nodoc
class __$$ChatMessageImplCopyWithImpl<$Res>
    extends _$ChatMessageCopyWithImpl<$Res, _$ChatMessageImpl>
    implements _$$ChatMessageImplCopyWith<$Res> {
  __$$ChatMessageImplCopyWithImpl(
      _$ChatMessageImpl _value, $Res Function(_$ChatMessageImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? content = null,
    Object? role = null,
    Object? timestamp = null,
    Object? model = freezed,
    Object? usage = freezed,
    Object? latencyMs = freezed,
    Object? costEstimateUsd = freezed,
    Object? routing = freezed,
    Object? safety = freezed,
    Object? isTyping = null,
  }) {
    return _then(_$ChatMessageImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      content: null == content
          ? _value.content
          : content // ignore: cast_nullable_to_non_nullable
              as String,
      role: null == role
          ? _value.role
          : role // ignore: cast_nullable_to_non_nullable
              as MessageRole,
      timestamp: null == timestamp
          ? _value.timestamp
          : timestamp // ignore: cast_nullable_to_non_nullable
              as DateTime,
      model: freezed == model
          ? _value.model
          : model // ignore: cast_nullable_to_non_nullable
              as String?,
      usage: freezed == usage
          ? _value.usage
          : usage // ignore: cast_nullable_to_non_nullable
              as ChatUsage?,
      latencyMs: freezed == latencyMs
          ? _value.latencyMs
          : latencyMs // ignore: cast_nullable_to_non_nullable
              as int?,
      costEstimateUsd: freezed == costEstimateUsd
          ? _value.costEstimateUsd
          : costEstimateUsd // ignore: cast_nullable_to_non_nullable
              as double?,
      routing: freezed == routing
          ? _value.routing
          : routing // ignore: cast_nullable_to_non_nullable
              as ChatRouting?,
      safety: freezed == safety
          ? _value.safety
          : safety // ignore: cast_nullable_to_non_nullable
              as ChatSafety?,
      isTyping: null == isTyping
          ? _value.isTyping
          : isTyping // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ChatMessageImpl implements _ChatMessage {
  const _$ChatMessageImpl(
      {required this.id,
      required this.content,
      required this.role,
      required this.timestamp,
      this.model,
      this.usage,
      this.latencyMs,
      this.costEstimateUsd,
      this.routing,
      this.safety,
      this.isTyping = false});

  factory _$ChatMessageImpl.fromJson(Map<String, dynamic> json) =>
      _$$ChatMessageImplFromJson(json);

  @override
  final String id;
  @override
  final String content;
  @override
  final MessageRole role;
  @override
  final DateTime timestamp;
  @override
  final String? model;
  @override
  final ChatUsage? usage;
  @override
  final int? latencyMs;
  @override
  final double? costEstimateUsd;
  @override
  final ChatRouting? routing;
  @override
  final ChatSafety? safety;
  @override
  @JsonKey()
  final bool isTyping;

  @override
  String toString() {
    return 'ChatMessage(id: $id, content: $content, role: $role, timestamp: $timestamp, model: $model, usage: $usage, latencyMs: $latencyMs, costEstimateUsd: $costEstimateUsd, routing: $routing, safety: $safety, isTyping: $isTyping)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ChatMessageImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.content, content) || other.content == content) &&
            (identical(other.role, role) || other.role == role) &&
            (identical(other.timestamp, timestamp) ||
                other.timestamp == timestamp) &&
            (identical(other.model, model) || other.model == model) &&
            (identical(other.usage, usage) || other.usage == usage) &&
            (identical(other.latencyMs, latencyMs) ||
                other.latencyMs == latencyMs) &&
            (identical(other.costEstimateUsd, costEstimateUsd) ||
                other.costEstimateUsd == costEstimateUsd) &&
            (identical(other.routing, routing) || other.routing == routing) &&
            (identical(other.safety, safety) || other.safety == safety) &&
            (identical(other.isTyping, isTyping) ||
                other.isTyping == isTyping));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, id, content, role, timestamp,
      model, usage, latencyMs, costEstimateUsd, routing, safety, isTyping);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ChatMessageImplCopyWith<_$ChatMessageImpl> get copyWith =>
      __$$ChatMessageImplCopyWithImpl<_$ChatMessageImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ChatMessageImplToJson(
      this,
    );
  }
}

abstract class _ChatMessage implements ChatMessage {
  const factory _ChatMessage(
      {required final String id,
      required final String content,
      required final MessageRole role,
      required final DateTime timestamp,
      final String? model,
      final ChatUsage? usage,
      final int? latencyMs,
      final double? costEstimateUsd,
      final ChatRouting? routing,
      final ChatSafety? safety,
      final bool isTyping}) = _$ChatMessageImpl;

  factory _ChatMessage.fromJson(Map<String, dynamic> json) =
      _$ChatMessageImpl.fromJson;

  @override
  String get id;
  @override
  String get content;
  @override
  MessageRole get role;
  @override
  DateTime get timestamp;
  @override
  String? get model;
  @override
  ChatUsage? get usage;
  @override
  int? get latencyMs;
  @override
  double? get costEstimateUsd;
  @override
  ChatRouting? get routing;
  @override
  ChatSafety? get safety;
  @override
  bool get isTyping;
  @override
  @JsonKey(ignore: true)
  _$$ChatMessageImplCopyWith<_$ChatMessageImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ChatUsage _$ChatUsageFromJson(Map<String, dynamic> json) {
  return _ChatUsage.fromJson(json);
}

/// @nodoc
mixin _$ChatUsage {
  int get promptTokens => throw _privateConstructorUsedError;
  int get completionTokens => throw _privateConstructorUsedError;
  int get totalTokens => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ChatUsageCopyWith<ChatUsage> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ChatUsageCopyWith<$Res> {
  factory $ChatUsageCopyWith(ChatUsage value, $Res Function(ChatUsage) then) =
      _$ChatUsageCopyWithImpl<$Res, ChatUsage>;
  @useResult
  $Res call({int promptTokens, int completionTokens, int totalTokens});
}

/// @nodoc
class _$ChatUsageCopyWithImpl<$Res, $Val extends ChatUsage>
    implements $ChatUsageCopyWith<$Res> {
  _$ChatUsageCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? promptTokens = null,
    Object? completionTokens = null,
    Object? totalTokens = null,
  }) {
    return _then(_value.copyWith(
      promptTokens: null == promptTokens
          ? _value.promptTokens
          : promptTokens // ignore: cast_nullable_to_non_nullable
              as int,
      completionTokens: null == completionTokens
          ? _value.completionTokens
          : completionTokens // ignore: cast_nullable_to_non_nullable
              as int,
      totalTokens: null == totalTokens
          ? _value.totalTokens
          : totalTokens // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ChatUsageImplCopyWith<$Res>
    implements $ChatUsageCopyWith<$Res> {
  factory _$$ChatUsageImplCopyWith(
          _$ChatUsageImpl value, $Res Function(_$ChatUsageImpl) then) =
      __$$ChatUsageImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({int promptTokens, int completionTokens, int totalTokens});
}

/// @nodoc
class __$$ChatUsageImplCopyWithImpl<$Res>
    extends _$ChatUsageCopyWithImpl<$Res, _$ChatUsageImpl>
    implements _$$ChatUsageImplCopyWith<$Res> {
  __$$ChatUsageImplCopyWithImpl(
      _$ChatUsageImpl _value, $Res Function(_$ChatUsageImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? promptTokens = null,
    Object? completionTokens = null,
    Object? totalTokens = null,
  }) {
    return _then(_$ChatUsageImpl(
      promptTokens: null == promptTokens
          ? _value.promptTokens
          : promptTokens // ignore: cast_nullable_to_non_nullable
              as int,
      completionTokens: null == completionTokens
          ? _value.completionTokens
          : completionTokens // ignore: cast_nullable_to_non_nullable
              as int,
      totalTokens: null == totalTokens
          ? _value.totalTokens
          : totalTokens // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ChatUsageImpl implements _ChatUsage {
  const _$ChatUsageImpl(
      {this.promptTokens = 0, this.completionTokens = 0, this.totalTokens = 0});

  factory _$ChatUsageImpl.fromJson(Map<String, dynamic> json) =>
      _$$ChatUsageImplFromJson(json);

  @override
  @JsonKey()
  final int promptTokens;
  @override
  @JsonKey()
  final int completionTokens;
  @override
  @JsonKey()
  final int totalTokens;

  @override
  String toString() {
    return 'ChatUsage(promptTokens: $promptTokens, completionTokens: $completionTokens, totalTokens: $totalTokens)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ChatUsageImpl &&
            (identical(other.promptTokens, promptTokens) ||
                other.promptTokens == promptTokens) &&
            (identical(other.completionTokens, completionTokens) ||
                other.completionTokens == completionTokens) &&
            (identical(other.totalTokens, totalTokens) ||
                other.totalTokens == totalTokens));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode =>
      Object.hash(runtimeType, promptTokens, completionTokens, totalTokens);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ChatUsageImplCopyWith<_$ChatUsageImpl> get copyWith =>
      __$$ChatUsageImplCopyWithImpl<_$ChatUsageImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ChatUsageImplToJson(
      this,
    );
  }
}

abstract class _ChatUsage implements ChatUsage {
  const factory _ChatUsage(
      {final int promptTokens,
      final int completionTokens,
      final int totalTokens}) = _$ChatUsageImpl;

  factory _ChatUsage.fromJson(Map<String, dynamic> json) =
      _$ChatUsageImpl.fromJson;

  @override
  int get promptTokens;
  @override
  int get completionTokens;
  @override
  int get totalTokens;
  @override
  @JsonKey(ignore: true)
  _$$ChatUsageImplCopyWith<_$ChatUsageImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ChatRouting _$ChatRoutingFromJson(Map<String, dynamic> json) {
  return _ChatRouting.fromJson(json);
}

/// @nodoc
mixin _$ChatRouting {
  String get selected => throw _privateConstructorUsedError;
  List<String> get candidates => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ChatRoutingCopyWith<ChatRouting> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ChatRoutingCopyWith<$Res> {
  factory $ChatRoutingCopyWith(
          ChatRouting value, $Res Function(ChatRouting) then) =
      _$ChatRoutingCopyWithImpl<$Res, ChatRouting>;
  @useResult
  $Res call({String selected, List<String> candidates});
}

/// @nodoc
class _$ChatRoutingCopyWithImpl<$Res, $Val extends ChatRouting>
    implements $ChatRoutingCopyWith<$Res> {
  _$ChatRoutingCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? selected = null,
    Object? candidates = null,
  }) {
    return _then(_value.copyWith(
      selected: null == selected
          ? _value.selected
          : selected // ignore: cast_nullable_to_non_nullable
              as String,
      candidates: null == candidates
          ? _value.candidates
          : candidates // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ChatRoutingImplCopyWith<$Res>
    implements $ChatRoutingCopyWith<$Res> {
  factory _$$ChatRoutingImplCopyWith(
          _$ChatRoutingImpl value, $Res Function(_$ChatRoutingImpl) then) =
      __$$ChatRoutingImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({String selected, List<String> candidates});
}

/// @nodoc
class __$$ChatRoutingImplCopyWithImpl<$Res>
    extends _$ChatRoutingCopyWithImpl<$Res, _$ChatRoutingImpl>
    implements _$$ChatRoutingImplCopyWith<$Res> {
  __$$ChatRoutingImplCopyWithImpl(
      _$ChatRoutingImpl _value, $Res Function(_$ChatRoutingImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? selected = null,
    Object? candidates = null,
  }) {
    return _then(_$ChatRoutingImpl(
      selected: null == selected
          ? _value.selected
          : selected // ignore: cast_nullable_to_non_nullable
              as String,
      candidates: null == candidates
          ? _value._candidates
          : candidates // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ChatRoutingImpl implements _ChatRouting {
  const _$ChatRoutingImpl(
      {required this.selected, final List<String> candidates = const []})
      : _candidates = candidates;

  factory _$ChatRoutingImpl.fromJson(Map<String, dynamic> json) =>
      _$$ChatRoutingImplFromJson(json);

  @override
  final String selected;
  final List<String> _candidates;
  @override
  @JsonKey()
  List<String> get candidates {
    if (_candidates is EqualUnmodifiableListView) return _candidates;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_candidates);
  }

  @override
  String toString() {
    return 'ChatRouting(selected: $selected, candidates: $candidates)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ChatRoutingImpl &&
            (identical(other.selected, selected) ||
                other.selected == selected) &&
            const DeepCollectionEquality()
                .equals(other._candidates, _candidates));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType, selected, const DeepCollectionEquality().hash(_candidates));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ChatRoutingImplCopyWith<_$ChatRoutingImpl> get copyWith =>
      __$$ChatRoutingImplCopyWithImpl<_$ChatRoutingImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ChatRoutingImplToJson(
      this,
    );
  }
}

abstract class _ChatRouting implements ChatRouting {
  const factory _ChatRouting(
      {required final String selected,
      final List<String> candidates}) = _$ChatRoutingImpl;

  factory _ChatRouting.fromJson(Map<String, dynamic> json) =
      _$ChatRoutingImpl.fromJson;

  @override
  String get selected;
  @override
  List<String> get candidates;
  @override
  @JsonKey(ignore: true)
  _$$ChatRoutingImplCopyWith<_$ChatRoutingImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ChatSafety _$ChatSafetyFromJson(Map<String, dynamic> json) {
  return _ChatSafety.fromJson(json);
}

/// @nodoc
mixin _$ChatSafety {
  bool get filtered => throw _privateConstructorUsedError;
  List<String> get flags => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ChatSafetyCopyWith<ChatSafety> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ChatSafetyCopyWith<$Res> {
  factory $ChatSafetyCopyWith(
          ChatSafety value, $Res Function(ChatSafety) then) =
      _$ChatSafetyCopyWithImpl<$Res, ChatSafety>;
  @useResult
  $Res call({bool filtered, List<String> flags});
}

/// @nodoc
class _$ChatSafetyCopyWithImpl<$Res, $Val extends ChatSafety>
    implements $ChatSafetyCopyWith<$Res> {
  _$ChatSafetyCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? filtered = null,
    Object? flags = null,
  }) {
    return _then(_value.copyWith(
      filtered: null == filtered
          ? _value.filtered
          : filtered // ignore: cast_nullable_to_non_nullable
              as bool,
      flags: null == flags
          ? _value.flags
          : flags // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ChatSafetyImplCopyWith<$Res>
    implements $ChatSafetyCopyWith<$Res> {
  factory _$$ChatSafetyImplCopyWith(
          _$ChatSafetyImpl value, $Res Function(_$ChatSafetyImpl) then) =
      __$$ChatSafetyImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({bool filtered, List<String> flags});
}

/// @nodoc
class __$$ChatSafetyImplCopyWithImpl<$Res>
    extends _$ChatSafetyCopyWithImpl<$Res, _$ChatSafetyImpl>
    implements _$$ChatSafetyImplCopyWith<$Res> {
  __$$ChatSafetyImplCopyWithImpl(
      _$ChatSafetyImpl _value, $Res Function(_$ChatSafetyImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? filtered = null,
    Object? flags = null,
  }) {
    return _then(_$ChatSafetyImpl(
      filtered: null == filtered
          ? _value.filtered
          : filtered // ignore: cast_nullable_to_non_nullable
              as bool,
      flags: null == flags
          ? _value._flags
          : flags // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ChatSafetyImpl implements _ChatSafety {
  const _$ChatSafetyImpl(
      {this.filtered = false, final List<String> flags = const []})
      : _flags = flags;

  factory _$ChatSafetyImpl.fromJson(Map<String, dynamic> json) =>
      _$$ChatSafetyImplFromJson(json);

  @override
  @JsonKey()
  final bool filtered;
  final List<String> _flags;
  @override
  @JsonKey()
  List<String> get flags {
    if (_flags is EqualUnmodifiableListView) return _flags;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_flags);
  }

  @override
  String toString() {
    return 'ChatSafety(filtered: $filtered, flags: $flags)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ChatSafetyImpl &&
            (identical(other.filtered, filtered) ||
                other.filtered == filtered) &&
            const DeepCollectionEquality().equals(other._flags, _flags));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType, filtered, const DeepCollectionEquality().hash(_flags));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ChatSafetyImplCopyWith<_$ChatSafetyImpl> get copyWith =>
      __$$ChatSafetyImplCopyWithImpl<_$ChatSafetyImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ChatSafetyImplToJson(
      this,
    );
  }
}

abstract class _ChatSafety implements ChatSafety {
  const factory _ChatSafety({final bool filtered, final List<String> flags}) =
      _$ChatSafetyImpl;

  factory _ChatSafety.fromJson(Map<String, dynamic> json) =
      _$ChatSafetyImpl.fromJson;

  @override
  bool get filtered;
  @override
  List<String> get flags;
  @override
  @JsonKey(ignore: true)
  _$$ChatSafetyImplCopyWith<_$ChatSafetyImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ChatRequest _$ChatRequestFromJson(Map<String, dynamic> json) {
  return _ChatRequest.fromJson(json);
}

/// @nodoc
mixin _$ChatRequest {
  String get message => throw _privateConstructorUsedError;
  String get sessionId => throw _privateConstructorUsedError;
  ChatMetadata? get metadata => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ChatRequestCopyWith<ChatRequest> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ChatRequestCopyWith<$Res> {
  factory $ChatRequestCopyWith(
          ChatRequest value, $Res Function(ChatRequest) then) =
      _$ChatRequestCopyWithImpl<$Res, ChatRequest>;
  @useResult
  $Res call({String message, String sessionId, ChatMetadata? metadata});

  $ChatMetadataCopyWith<$Res>? get metadata;
}

/// @nodoc
class _$ChatRequestCopyWithImpl<$Res, $Val extends ChatRequest>
    implements $ChatRequestCopyWith<$Res> {
  _$ChatRequestCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? message = null,
    Object? sessionId = null,
    Object? metadata = freezed,
  }) {
    return _then(_value.copyWith(
      message: null == message
          ? _value.message
          : message // ignore: cast_nullable_to_non_nullable
              as String,
      sessionId: null == sessionId
          ? _value.sessionId
          : sessionId // ignore: cast_nullable_to_non_nullable
              as String,
      metadata: freezed == metadata
          ? _value.metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as ChatMetadata?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $ChatMetadataCopyWith<$Res>? get metadata {
    if (_value.metadata == null) {
      return null;
    }

    return $ChatMetadataCopyWith<$Res>(_value.metadata!, (value) {
      return _then(_value.copyWith(metadata: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$ChatRequestImplCopyWith<$Res>
    implements $ChatRequestCopyWith<$Res> {
  factory _$$ChatRequestImplCopyWith(
          _$ChatRequestImpl value, $Res Function(_$ChatRequestImpl) then) =
      __$$ChatRequestImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({String message, String sessionId, ChatMetadata? metadata});

  @override
  $ChatMetadataCopyWith<$Res>? get metadata;
}

/// @nodoc
class __$$ChatRequestImplCopyWithImpl<$Res>
    extends _$ChatRequestCopyWithImpl<$Res, _$ChatRequestImpl>
    implements _$$ChatRequestImplCopyWith<$Res> {
  __$$ChatRequestImplCopyWithImpl(
      _$ChatRequestImpl _value, $Res Function(_$ChatRequestImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? message = null,
    Object? sessionId = null,
    Object? metadata = freezed,
  }) {
    return _then(_$ChatRequestImpl(
      message: null == message
          ? _value.message
          : message // ignore: cast_nullable_to_non_nullable
              as String,
      sessionId: null == sessionId
          ? _value.sessionId
          : sessionId // ignore: cast_nullable_to_non_nullable
              as String,
      metadata: freezed == metadata
          ? _value.metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as ChatMetadata?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ChatRequestImpl implements _ChatRequest {
  const _$ChatRequestImpl(
      {required this.message, required this.sessionId, this.metadata});

  factory _$ChatRequestImpl.fromJson(Map<String, dynamic> json) =>
      _$$ChatRequestImplFromJson(json);

  @override
  final String message;
  @override
  final String sessionId;
  @override
  final ChatMetadata? metadata;

  @override
  String toString() {
    return 'ChatRequest(message: $message, sessionId: $sessionId, metadata: $metadata)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ChatRequestImpl &&
            (identical(other.message, message) || other.message == message) &&
            (identical(other.sessionId, sessionId) ||
                other.sessionId == sessionId) &&
            (identical(other.metadata, metadata) ||
                other.metadata == metadata));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, message, sessionId, metadata);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ChatRequestImplCopyWith<_$ChatRequestImpl> get copyWith =>
      __$$ChatRequestImplCopyWithImpl<_$ChatRequestImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ChatRequestImplToJson(
      this,
    );
  }
}

abstract class _ChatRequest implements ChatRequest {
  const factory _ChatRequest(
      {required final String message,
      required final String sessionId,
      final ChatMetadata? metadata}) = _$ChatRequestImpl;

  factory _ChatRequest.fromJson(Map<String, dynamic> json) =
      _$ChatRequestImpl.fromJson;

  @override
  String get message;
  @override
  String get sessionId;
  @override
  ChatMetadata? get metadata;
  @override
  @JsonKey(ignore: true)
  _$$ChatRequestImplCopyWith<_$ChatRequestImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ChatMetadata _$ChatMetadataFromJson(Map<String, dynamic> json) {
  return _ChatMetadata.fromJson(json);
}

/// @nodoc
mixin _$ChatMetadata {
  String? get persona => throw _privateConstructorUsedError;
  String get language => throw _privateConstructorUsedError;
  String? get founderCommand => throw _privateConstructorUsedError;
  bool get debug => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ChatMetadataCopyWith<ChatMetadata> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ChatMetadataCopyWith<$Res> {
  factory $ChatMetadataCopyWith(
          ChatMetadata value, $Res Function(ChatMetadata) then) =
      _$ChatMetadataCopyWithImpl<$Res, ChatMetadata>;
  @useResult
  $Res call(
      {String? persona, String language, String? founderCommand, bool debug});
}

/// @nodoc
class _$ChatMetadataCopyWithImpl<$Res, $Val extends ChatMetadata>
    implements $ChatMetadataCopyWith<$Res> {
  _$ChatMetadataCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? persona = freezed,
    Object? language = null,
    Object? founderCommand = freezed,
    Object? debug = null,
  }) {
    return _then(_value.copyWith(
      persona: freezed == persona
          ? _value.persona
          : persona // ignore: cast_nullable_to_non_nullable
              as String?,
      language: null == language
          ? _value.language
          : language // ignore: cast_nullable_to_non_nullable
              as String,
      founderCommand: freezed == founderCommand
          ? _value.founderCommand
          : founderCommand // ignore: cast_nullable_to_non_nullable
              as String?,
      debug: null == debug
          ? _value.debug
          : debug // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ChatMetadataImplCopyWith<$Res>
    implements $ChatMetadataCopyWith<$Res> {
  factory _$$ChatMetadataImplCopyWith(
          _$ChatMetadataImpl value, $Res Function(_$ChatMetadataImpl) then) =
      __$$ChatMetadataImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String? persona, String language, String? founderCommand, bool debug});
}

/// @nodoc
class __$$ChatMetadataImplCopyWithImpl<$Res>
    extends _$ChatMetadataCopyWithImpl<$Res, _$ChatMetadataImpl>
    implements _$$ChatMetadataImplCopyWith<$Res> {
  __$$ChatMetadataImplCopyWithImpl(
      _$ChatMetadataImpl _value, $Res Function(_$ChatMetadataImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? persona = freezed,
    Object? language = null,
    Object? founderCommand = freezed,
    Object? debug = null,
  }) {
    return _then(_$ChatMetadataImpl(
      persona: freezed == persona
          ? _value.persona
          : persona // ignore: cast_nullable_to_non_nullable
              as String?,
      language: null == language
          ? _value.language
          : language // ignore: cast_nullable_to_non_nullable
              as String,
      founderCommand: freezed == founderCommand
          ? _value.founderCommand
          : founderCommand // ignore: cast_nullable_to_non_nullable
              as String?,
      debug: null == debug
          ? _value.debug
          : debug // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ChatMetadataImpl implements _ChatMetadata {
  const _$ChatMetadataImpl(
      {this.persona,
      this.language = 'vi',
      this.founderCommand,
      this.debug = false});

  factory _$ChatMetadataImpl.fromJson(Map<String, dynamic> json) =>
      _$$ChatMetadataImplFromJson(json);

  @override
  final String? persona;
  @override
  @JsonKey()
  final String language;
  @override
  final String? founderCommand;
  @override
  @JsonKey()
  final bool debug;

  @override
  String toString() {
    return 'ChatMetadata(persona: $persona, language: $language, founderCommand: $founderCommand, debug: $debug)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ChatMetadataImpl &&
            (identical(other.persona, persona) || other.persona == persona) &&
            (identical(other.language, language) ||
                other.language == language) &&
            (identical(other.founderCommand, founderCommand) ||
                other.founderCommand == founderCommand) &&
            (identical(other.debug, debug) || other.debug == debug));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode =>
      Object.hash(runtimeType, persona, language, founderCommand, debug);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ChatMetadataImplCopyWith<_$ChatMetadataImpl> get copyWith =>
      __$$ChatMetadataImplCopyWithImpl<_$ChatMetadataImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ChatMetadataImplToJson(
      this,
    );
  }
}

abstract class _ChatMetadata implements ChatMetadata {
  const factory _ChatMetadata(
      {final String? persona,
      final String language,
      final String? founderCommand,
      final bool debug}) = _$ChatMetadataImpl;

  factory _ChatMetadata.fromJson(Map<String, dynamic> json) =
      _$ChatMetadataImpl.fromJson;

  @override
  String? get persona;
  @override
  String get language;
  @override
  String? get founderCommand;
  @override
  bool get debug;
  @override
  @JsonKey(ignore: true)
  _$$ChatMetadataImplCopyWith<_$ChatMetadataImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ChatResponse _$ChatResponseFromJson(Map<String, dynamic> json) {
  return _ChatResponse.fromJson(json);
}

/// @nodoc
mixin _$ChatResponse {
  String get text => throw _privateConstructorUsedError;
  String? get model => throw _privateConstructorUsedError;
  ChatUsage? get usage => throw _privateConstructorUsedError;
  int? get latencyMs => throw _privateConstructorUsedError;
  double? get costEstimateUsd => throw _privateConstructorUsedError;
  ChatRouting? get routing => throw _privateConstructorUsedError;
  ChatSafety? get safety => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ChatResponseCopyWith<ChatResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ChatResponseCopyWith<$Res> {
  factory $ChatResponseCopyWith(
          ChatResponse value, $Res Function(ChatResponse) then) =
      _$ChatResponseCopyWithImpl<$Res, ChatResponse>;
  @useResult
  $Res call(
      {String text,
      String? model,
      ChatUsage? usage,
      int? latencyMs,
      double? costEstimateUsd,
      ChatRouting? routing,
      ChatSafety? safety});

  $ChatUsageCopyWith<$Res>? get usage;
  $ChatRoutingCopyWith<$Res>? get routing;
  $ChatSafetyCopyWith<$Res>? get safety;
}

/// @nodoc
class _$ChatResponseCopyWithImpl<$Res, $Val extends ChatResponse>
    implements $ChatResponseCopyWith<$Res> {
  _$ChatResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? text = null,
    Object? model = freezed,
    Object? usage = freezed,
    Object? latencyMs = freezed,
    Object? costEstimateUsd = freezed,
    Object? routing = freezed,
    Object? safety = freezed,
  }) {
    return _then(_value.copyWith(
      text: null == text
          ? _value.text
          : text // ignore: cast_nullable_to_non_nullable
              as String,
      model: freezed == model
          ? _value.model
          : model // ignore: cast_nullable_to_non_nullable
              as String?,
      usage: freezed == usage
          ? _value.usage
          : usage // ignore: cast_nullable_to_non_nullable
              as ChatUsage?,
      latencyMs: freezed == latencyMs
          ? _value.latencyMs
          : latencyMs // ignore: cast_nullable_to_non_nullable
              as int?,
      costEstimateUsd: freezed == costEstimateUsd
          ? _value.costEstimateUsd
          : costEstimateUsd // ignore: cast_nullable_to_non_nullable
              as double?,
      routing: freezed == routing
          ? _value.routing
          : routing // ignore: cast_nullable_to_non_nullable
              as ChatRouting?,
      safety: freezed == safety
          ? _value.safety
          : safety // ignore: cast_nullable_to_non_nullable
              as ChatSafety?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $ChatUsageCopyWith<$Res>? get usage {
    if (_value.usage == null) {
      return null;
    }

    return $ChatUsageCopyWith<$Res>(_value.usage!, (value) {
      return _then(_value.copyWith(usage: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $ChatRoutingCopyWith<$Res>? get routing {
    if (_value.routing == null) {
      return null;
    }

    return $ChatRoutingCopyWith<$Res>(_value.routing!, (value) {
      return _then(_value.copyWith(routing: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $ChatSafetyCopyWith<$Res>? get safety {
    if (_value.safety == null) {
      return null;
    }

    return $ChatSafetyCopyWith<$Res>(_value.safety!, (value) {
      return _then(_value.copyWith(safety: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$ChatResponseImplCopyWith<$Res>
    implements $ChatResponseCopyWith<$Res> {
  factory _$$ChatResponseImplCopyWith(
          _$ChatResponseImpl value, $Res Function(_$ChatResponseImpl) then) =
      __$$ChatResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String text,
      String? model,
      ChatUsage? usage,
      int? latencyMs,
      double? costEstimateUsd,
      ChatRouting? routing,
      ChatSafety? safety});

  @override
  $ChatUsageCopyWith<$Res>? get usage;
  @override
  $ChatRoutingCopyWith<$Res>? get routing;
  @override
  $ChatSafetyCopyWith<$Res>? get safety;
}

/// @nodoc
class __$$ChatResponseImplCopyWithImpl<$Res>
    extends _$ChatResponseCopyWithImpl<$Res, _$ChatResponseImpl>
    implements _$$ChatResponseImplCopyWith<$Res> {
  __$$ChatResponseImplCopyWithImpl(
      _$ChatResponseImpl _value, $Res Function(_$ChatResponseImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? text = null,
    Object? model = freezed,
    Object? usage = freezed,
    Object? latencyMs = freezed,
    Object? costEstimateUsd = freezed,
    Object? routing = freezed,
    Object? safety = freezed,
  }) {
    return _then(_$ChatResponseImpl(
      text: null == text
          ? _value.text
          : text // ignore: cast_nullable_to_non_nullable
              as String,
      model: freezed == model
          ? _value.model
          : model // ignore: cast_nullable_to_non_nullable
              as String?,
      usage: freezed == usage
          ? _value.usage
          : usage // ignore: cast_nullable_to_non_nullable
              as ChatUsage?,
      latencyMs: freezed == latencyMs
          ? _value.latencyMs
          : latencyMs // ignore: cast_nullable_to_non_nullable
              as int?,
      costEstimateUsd: freezed == costEstimateUsd
          ? _value.costEstimateUsd
          : costEstimateUsd // ignore: cast_nullable_to_non_nullable
              as double?,
      routing: freezed == routing
          ? _value.routing
          : routing // ignore: cast_nullable_to_non_nullable
              as ChatRouting?,
      safety: freezed == safety
          ? _value.safety
          : safety // ignore: cast_nullable_to_non_nullable
              as ChatSafety?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ChatResponseImpl implements _ChatResponse {
  const _$ChatResponseImpl(
      {required this.text,
      this.model,
      this.usage,
      this.latencyMs,
      this.costEstimateUsd,
      this.routing,
      this.safety});

  factory _$ChatResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$ChatResponseImplFromJson(json);

  @override
  final String text;
  @override
  final String? model;
  @override
  final ChatUsage? usage;
  @override
  final int? latencyMs;
  @override
  final double? costEstimateUsd;
  @override
  final ChatRouting? routing;
  @override
  final ChatSafety? safety;

  @override
  String toString() {
    return 'ChatResponse(text: $text, model: $model, usage: $usage, latencyMs: $latencyMs, costEstimateUsd: $costEstimateUsd, routing: $routing, safety: $safety)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ChatResponseImpl &&
            (identical(other.text, text) || other.text == text) &&
            (identical(other.model, model) || other.model == model) &&
            (identical(other.usage, usage) || other.usage == usage) &&
            (identical(other.latencyMs, latencyMs) ||
                other.latencyMs == latencyMs) &&
            (identical(other.costEstimateUsd, costEstimateUsd) ||
                other.costEstimateUsd == costEstimateUsd) &&
            (identical(other.routing, routing) || other.routing == routing) &&
            (identical(other.safety, safety) || other.safety == safety));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, text, model, usage, latencyMs,
      costEstimateUsd, routing, safety);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ChatResponseImplCopyWith<_$ChatResponseImpl> get copyWith =>
      __$$ChatResponseImplCopyWithImpl<_$ChatResponseImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ChatResponseImplToJson(
      this,
    );
  }
}

abstract class _ChatResponse implements ChatResponse {
  const factory _ChatResponse(
      {required final String text,
      final String? model,
      final ChatUsage? usage,
      final int? latencyMs,
      final double? costEstimateUsd,
      final ChatRouting? routing,
      final ChatSafety? safety}) = _$ChatResponseImpl;

  factory _ChatResponse.fromJson(Map<String, dynamic> json) =
      _$ChatResponseImpl.fromJson;

  @override
  String get text;
  @override
  String? get model;
  @override
  ChatUsage? get usage;
  @override
  int? get latencyMs;
  @override
  double? get costEstimateUsd;
  @override
  ChatRouting? get routing;
  @override
  ChatSafety? get safety;
  @override
  @JsonKey(ignore: true)
  _$$ChatResponseImplCopyWith<_$ChatResponseImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

HealthResponse _$HealthResponseFromJson(Map<String, dynamic> json) {
  return _HealthResponse.fromJson(json);
}

/// @nodoc
mixin _$HealthResponse {
  String get status => throw _privateConstructorUsedError;
  String? get timestamp => throw _privateConstructorUsedError;
  String? get service => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $HealthResponseCopyWith<HealthResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $HealthResponseCopyWith<$Res> {
  factory $HealthResponseCopyWith(
          HealthResponse value, $Res Function(HealthResponse) then) =
      _$HealthResponseCopyWithImpl<$Res, HealthResponse>;
  @useResult
  $Res call({String status, String? timestamp, String? service});
}

/// @nodoc
class _$HealthResponseCopyWithImpl<$Res, $Val extends HealthResponse>
    implements $HealthResponseCopyWith<$Res> {
  _$HealthResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? status = null,
    Object? timestamp = freezed,
    Object? service = freezed,
  }) {
    return _then(_value.copyWith(
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
      timestamp: freezed == timestamp
          ? _value.timestamp
          : timestamp // ignore: cast_nullable_to_non_nullable
              as String?,
      service: freezed == service
          ? _value.service
          : service // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$HealthResponseImplCopyWith<$Res>
    implements $HealthResponseCopyWith<$Res> {
  factory _$$HealthResponseImplCopyWith(_$HealthResponseImpl value,
          $Res Function(_$HealthResponseImpl) then) =
      __$$HealthResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({String status, String? timestamp, String? service});
}

/// @nodoc
class __$$HealthResponseImplCopyWithImpl<$Res>
    extends _$HealthResponseCopyWithImpl<$Res, _$HealthResponseImpl>
    implements _$$HealthResponseImplCopyWith<$Res> {
  __$$HealthResponseImplCopyWithImpl(
      _$HealthResponseImpl _value, $Res Function(_$HealthResponseImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? status = null,
    Object? timestamp = freezed,
    Object? service = freezed,
  }) {
    return _then(_$HealthResponseImpl(
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
      timestamp: freezed == timestamp
          ? _value.timestamp
          : timestamp // ignore: cast_nullable_to_non_nullable
              as String?,
      service: freezed == service
          ? _value.service
          : service // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$HealthResponseImpl implements _HealthResponse {
  const _$HealthResponseImpl(
      {required this.status, this.timestamp, this.service});

  factory _$HealthResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$HealthResponseImplFromJson(json);

  @override
  final String status;
  @override
  final String? timestamp;
  @override
  final String? service;

  @override
  String toString() {
    return 'HealthResponse(status: $status, timestamp: $timestamp, service: $service)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$HealthResponseImpl &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.timestamp, timestamp) ||
                other.timestamp == timestamp) &&
            (identical(other.service, service) || other.service == service));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, status, timestamp, service);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$HealthResponseImplCopyWith<_$HealthResponseImpl> get copyWith =>
      __$$HealthResponseImplCopyWithImpl<_$HealthResponseImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$HealthResponseImplToJson(
      this,
    );
  }
}

abstract class _HealthResponse implements HealthResponse {
  const factory _HealthResponse(
      {required final String status,
      final String? timestamp,
      final String? service}) = _$HealthResponseImpl;

  factory _HealthResponse.fromJson(Map<String, dynamic> json) =
      _$HealthResponseImpl.fromJson;

  @override
  String get status;
  @override
  String? get timestamp;
  @override
  String? get service;
  @override
  @JsonKey(ignore: true)
  _$$HealthResponseImplCopyWith<_$HealthResponseImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

TelemetryData _$TelemetryDataFromJson(Map<String, dynamic> json) {
  return _TelemetryData.fromJson(json);
}

/// @nodoc
mixin _$TelemetryData {
  String get model => throw _privateConstructorUsedError;
  ChatUsage get usage => throw _privateConstructorUsedError;
  int get latencyMs => throw _privateConstructorUsedError;
  double get costEstimateUsd => throw _privateConstructorUsedError;
  DateTime get timestamp => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $TelemetryDataCopyWith<TelemetryData> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $TelemetryDataCopyWith<$Res> {
  factory $TelemetryDataCopyWith(
          TelemetryData value, $Res Function(TelemetryData) then) =
      _$TelemetryDataCopyWithImpl<$Res, TelemetryData>;
  @useResult
  $Res call(
      {String model,
      ChatUsage usage,
      int latencyMs,
      double costEstimateUsd,
      DateTime timestamp,
      String? error});

  $ChatUsageCopyWith<$Res> get usage;
}

/// @nodoc
class _$TelemetryDataCopyWithImpl<$Res, $Val extends TelemetryData>
    implements $TelemetryDataCopyWith<$Res> {
  _$TelemetryDataCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? model = null,
    Object? usage = null,
    Object? latencyMs = null,
    Object? costEstimateUsd = null,
    Object? timestamp = null,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      model: null == model
          ? _value.model
          : model // ignore: cast_nullable_to_non_nullable
              as String,
      usage: null == usage
          ? _value.usage
          : usage // ignore: cast_nullable_to_non_nullable
              as ChatUsage,
      latencyMs: null == latencyMs
          ? _value.latencyMs
          : latencyMs // ignore: cast_nullable_to_non_nullable
              as int,
      costEstimateUsd: null == costEstimateUsd
          ? _value.costEstimateUsd
          : costEstimateUsd // ignore: cast_nullable_to_non_nullable
              as double,
      timestamp: null == timestamp
          ? _value.timestamp
          : timestamp // ignore: cast_nullable_to_non_nullable
              as DateTime,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $ChatUsageCopyWith<$Res> get usage {
    return $ChatUsageCopyWith<$Res>(_value.usage, (value) {
      return _then(_value.copyWith(usage: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$TelemetryDataImplCopyWith<$Res>
    implements $TelemetryDataCopyWith<$Res> {
  factory _$$TelemetryDataImplCopyWith(
          _$TelemetryDataImpl value, $Res Function(_$TelemetryDataImpl) then) =
      __$$TelemetryDataImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String model,
      ChatUsage usage,
      int latencyMs,
      double costEstimateUsd,
      DateTime timestamp,
      String? error});

  @override
  $ChatUsageCopyWith<$Res> get usage;
}

/// @nodoc
class __$$TelemetryDataImplCopyWithImpl<$Res>
    extends _$TelemetryDataCopyWithImpl<$Res, _$TelemetryDataImpl>
    implements _$$TelemetryDataImplCopyWith<$Res> {
  __$$TelemetryDataImplCopyWithImpl(
      _$TelemetryDataImpl _value, $Res Function(_$TelemetryDataImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? model = null,
    Object? usage = null,
    Object? latencyMs = null,
    Object? costEstimateUsd = null,
    Object? timestamp = null,
    Object? error = freezed,
  }) {
    return _then(_$TelemetryDataImpl(
      model: null == model
          ? _value.model
          : model // ignore: cast_nullable_to_non_nullable
              as String,
      usage: null == usage
          ? _value.usage
          : usage // ignore: cast_nullable_to_non_nullable
              as ChatUsage,
      latencyMs: null == latencyMs
          ? _value.latencyMs
          : latencyMs // ignore: cast_nullable_to_non_nullable
              as int,
      costEstimateUsd: null == costEstimateUsd
          ? _value.costEstimateUsd
          : costEstimateUsd // ignore: cast_nullable_to_non_nullable
              as double,
      timestamp: null == timestamp
          ? _value.timestamp
          : timestamp // ignore: cast_nullable_to_non_nullable
              as DateTime,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$TelemetryDataImpl implements _TelemetryData {
  const _$TelemetryDataImpl(
      {required this.model,
      required this.usage,
      required this.latencyMs,
      required this.costEstimateUsd,
      required this.timestamp,
      this.error});

  factory _$TelemetryDataImpl.fromJson(Map<String, dynamic> json) =>
      _$$TelemetryDataImplFromJson(json);

  @override
  final String model;
  @override
  final ChatUsage usage;
  @override
  final int latencyMs;
  @override
  final double costEstimateUsd;
  @override
  final DateTime timestamp;
  @override
  final String? error;

  @override
  String toString() {
    return 'TelemetryData(model: $model, usage: $usage, latencyMs: $latencyMs, costEstimateUsd: $costEstimateUsd, timestamp: $timestamp, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$TelemetryDataImpl &&
            (identical(other.model, model) || other.model == model) &&
            (identical(other.usage, usage) || other.usage == usage) &&
            (identical(other.latencyMs, latencyMs) ||
                other.latencyMs == latencyMs) &&
            (identical(other.costEstimateUsd, costEstimateUsd) ||
                other.costEstimateUsd == costEstimateUsd) &&
            (identical(other.timestamp, timestamp) ||
                other.timestamp == timestamp) &&
            (identical(other.error, error) || other.error == error));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType, model, usage, latencyMs, costEstimateUsd, timestamp, error);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$TelemetryDataImplCopyWith<_$TelemetryDataImpl> get copyWith =>
      __$$TelemetryDataImplCopyWithImpl<_$TelemetryDataImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$TelemetryDataImplToJson(
      this,
    );
  }
}

abstract class _TelemetryData implements TelemetryData {
  const factory _TelemetryData(
      {required final String model,
      required final ChatUsage usage,
      required final int latencyMs,
      required final double costEstimateUsd,
      required final DateTime timestamp,
      final String? error}) = _$TelemetryDataImpl;

  factory _TelemetryData.fromJson(Map<String, dynamic> json) =
      _$TelemetryDataImpl.fromJson;

  @override
  String get model;
  @override
  ChatUsage get usage;
  @override
  int get latencyMs;
  @override
  double get costEstimateUsd;
  @override
  DateTime get timestamp;
  @override
  String? get error;
  @override
  @JsonKey(ignore: true)
  _$$TelemetryDataImplCopyWith<_$TelemetryDataImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

SessionMetrics _$SessionMetricsFromJson(Map<String, dynamic> json) {
  return _SessionMetrics.fromJson(json);
}

/// @nodoc
mixin _$SessionMetrics {
  int get totalMessages => throw _privateConstructorUsedError;
  int get totalTokens => throw _privateConstructorUsedError;
  double get totalCost => throw _privateConstructorUsedError;
  int get averageLatency => throw _privateConstructorUsedError;
  List<String> get modelsUsed => throw _privateConstructorUsedError;
  int get errorCount => throw _privateConstructorUsedError;
  DateTime get sessionStart => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $SessionMetricsCopyWith<SessionMetrics> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $SessionMetricsCopyWith<$Res> {
  factory $SessionMetricsCopyWith(
          SessionMetrics value, $Res Function(SessionMetrics) then) =
      _$SessionMetricsCopyWithImpl<$Res, SessionMetrics>;
  @useResult
  $Res call(
      {int totalMessages,
      int totalTokens,
      double totalCost,
      int averageLatency,
      List<String> modelsUsed,
      int errorCount,
      DateTime sessionStart});
}

/// @nodoc
class _$SessionMetricsCopyWithImpl<$Res, $Val extends SessionMetrics>
    implements $SessionMetricsCopyWith<$Res> {
  _$SessionMetricsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? totalMessages = null,
    Object? totalTokens = null,
    Object? totalCost = null,
    Object? averageLatency = null,
    Object? modelsUsed = null,
    Object? errorCount = null,
    Object? sessionStart = null,
  }) {
    return _then(_value.copyWith(
      totalMessages: null == totalMessages
          ? _value.totalMessages
          : totalMessages // ignore: cast_nullable_to_non_nullable
              as int,
      totalTokens: null == totalTokens
          ? _value.totalTokens
          : totalTokens // ignore: cast_nullable_to_non_nullable
              as int,
      totalCost: null == totalCost
          ? _value.totalCost
          : totalCost // ignore: cast_nullable_to_non_nullable
              as double,
      averageLatency: null == averageLatency
          ? _value.averageLatency
          : averageLatency // ignore: cast_nullable_to_non_nullable
              as int,
      modelsUsed: null == modelsUsed
          ? _value.modelsUsed
          : modelsUsed // ignore: cast_nullable_to_non_nullable
              as List<String>,
      errorCount: null == errorCount
          ? _value.errorCount
          : errorCount // ignore: cast_nullable_to_non_nullable
              as int,
      sessionStart: null == sessionStart
          ? _value.sessionStart
          : sessionStart // ignore: cast_nullable_to_non_nullable
              as DateTime,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$SessionMetricsImplCopyWith<$Res>
    implements $SessionMetricsCopyWith<$Res> {
  factory _$$SessionMetricsImplCopyWith(_$SessionMetricsImpl value,
          $Res Function(_$SessionMetricsImpl) then) =
      __$$SessionMetricsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {int totalMessages,
      int totalTokens,
      double totalCost,
      int averageLatency,
      List<String> modelsUsed,
      int errorCount,
      DateTime sessionStart});
}

/// @nodoc
class __$$SessionMetricsImplCopyWithImpl<$Res>
    extends _$SessionMetricsCopyWithImpl<$Res, _$SessionMetricsImpl>
    implements _$$SessionMetricsImplCopyWith<$Res> {
  __$$SessionMetricsImplCopyWithImpl(
      _$SessionMetricsImpl _value, $Res Function(_$SessionMetricsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? totalMessages = null,
    Object? totalTokens = null,
    Object? totalCost = null,
    Object? averageLatency = null,
    Object? modelsUsed = null,
    Object? errorCount = null,
    Object? sessionStart = null,
  }) {
    return _then(_$SessionMetricsImpl(
      totalMessages: null == totalMessages
          ? _value.totalMessages
          : totalMessages // ignore: cast_nullable_to_non_nullable
              as int,
      totalTokens: null == totalTokens
          ? _value.totalTokens
          : totalTokens // ignore: cast_nullable_to_non_nullable
              as int,
      totalCost: null == totalCost
          ? _value.totalCost
          : totalCost // ignore: cast_nullable_to_non_nullable
              as double,
      averageLatency: null == averageLatency
          ? _value.averageLatency
          : averageLatency // ignore: cast_nullable_to_non_nullable
              as int,
      modelsUsed: null == modelsUsed
          ? _value._modelsUsed
          : modelsUsed // ignore: cast_nullable_to_non_nullable
              as List<String>,
      errorCount: null == errorCount
          ? _value.errorCount
          : errorCount // ignore: cast_nullable_to_non_nullable
              as int,
      sessionStart: null == sessionStart
          ? _value.sessionStart
          : sessionStart // ignore: cast_nullable_to_non_nullable
              as DateTime,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$SessionMetricsImpl implements _SessionMetrics {
  const _$SessionMetricsImpl(
      {this.totalMessages = 0,
      this.totalTokens = 0,
      this.totalCost = 0,
      this.averageLatency = 0,
      final List<String> modelsUsed = const [],
      this.errorCount = 0,
      required this.sessionStart})
      : _modelsUsed = modelsUsed;

  factory _$SessionMetricsImpl.fromJson(Map<String, dynamic> json) =>
      _$$SessionMetricsImplFromJson(json);

  @override
  @JsonKey()
  final int totalMessages;
  @override
  @JsonKey()
  final int totalTokens;
  @override
  @JsonKey()
  final double totalCost;
  @override
  @JsonKey()
  final int averageLatency;
  final List<String> _modelsUsed;
  @override
  @JsonKey()
  List<String> get modelsUsed {
    if (_modelsUsed is EqualUnmodifiableListView) return _modelsUsed;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_modelsUsed);
  }

  @override
  @JsonKey()
  final int errorCount;
  @override
  final DateTime sessionStart;

  @override
  String toString() {
    return 'SessionMetrics(totalMessages: $totalMessages, totalTokens: $totalTokens, totalCost: $totalCost, averageLatency: $averageLatency, modelsUsed: $modelsUsed, errorCount: $errorCount, sessionStart: $sessionStart)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$SessionMetricsImpl &&
            (identical(other.totalMessages, totalMessages) ||
                other.totalMessages == totalMessages) &&
            (identical(other.totalTokens, totalTokens) ||
                other.totalTokens == totalTokens) &&
            (identical(other.totalCost, totalCost) ||
                other.totalCost == totalCost) &&
            (identical(other.averageLatency, averageLatency) ||
                other.averageLatency == averageLatency) &&
            const DeepCollectionEquality()
                .equals(other._modelsUsed, _modelsUsed) &&
            (identical(other.errorCount, errorCount) ||
                other.errorCount == errorCount) &&
            (identical(other.sessionStart, sessionStart) ||
                other.sessionStart == sessionStart));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      totalMessages,
      totalTokens,
      totalCost,
      averageLatency,
      const DeepCollectionEquality().hash(_modelsUsed),
      errorCount,
      sessionStart);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$SessionMetricsImplCopyWith<_$SessionMetricsImpl> get copyWith =>
      __$$SessionMetricsImplCopyWithImpl<_$SessionMetricsImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$SessionMetricsImplToJson(
      this,
    );
  }
}

abstract class _SessionMetrics implements SessionMetrics {
  const factory _SessionMetrics(
      {final int totalMessages,
      final int totalTokens,
      final double totalCost,
      final int averageLatency,
      final List<String> modelsUsed,
      final int errorCount,
      required final DateTime sessionStart}) = _$SessionMetricsImpl;

  factory _SessionMetrics.fromJson(Map<String, dynamic> json) =
      _$SessionMetricsImpl.fromJson;

  @override
  int get totalMessages;
  @override
  int get totalTokens;
  @override
  double get totalCost;
  @override
  int get averageLatency;
  @override
  List<String> get modelsUsed;
  @override
  int get errorCount;
  @override
  DateTime get sessionStart;
  @override
  @JsonKey(ignore: true)
  _$$SessionMetricsImplCopyWith<_$SessionMetricsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

QuickAction _$QuickActionFromJson(Map<String, dynamic> json) {
  return _QuickAction.fromJson(json);
}

/// @nodoc
mixin _$QuickAction {
  String get id => throw _privateConstructorUsedError;
  String get title => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;
  String get command => throw _privateConstructorUsedError;
  QuickActionType get type => throw _privateConstructorUsedError;
  String? get icon => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $QuickActionCopyWith<QuickAction> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $QuickActionCopyWith<$Res> {
  factory $QuickActionCopyWith(
          QuickAction value, $Res Function(QuickAction) then) =
      _$QuickActionCopyWithImpl<$Res, QuickAction>;
  @useResult
  $Res call(
      {String id,
      String title,
      String description,
      String command,
      QuickActionType type,
      String? icon});
}

/// @nodoc
class _$QuickActionCopyWithImpl<$Res, $Val extends QuickAction>
    implements $QuickActionCopyWith<$Res> {
  _$QuickActionCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? title = null,
    Object? description = null,
    Object? command = null,
    Object? type = null,
    Object? icon = freezed,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      title: null == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      command: null == command
          ? _value.command
          : command // ignore: cast_nullable_to_non_nullable
              as String,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as QuickActionType,
      icon: freezed == icon
          ? _value.icon
          : icon // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$QuickActionImplCopyWith<$Res>
    implements $QuickActionCopyWith<$Res> {
  factory _$$QuickActionImplCopyWith(
          _$QuickActionImpl value, $Res Function(_$QuickActionImpl) then) =
      __$$QuickActionImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String title,
      String description,
      String command,
      QuickActionType type,
      String? icon});
}

/// @nodoc
class __$$QuickActionImplCopyWithImpl<$Res>
    extends _$QuickActionCopyWithImpl<$Res, _$QuickActionImpl>
    implements _$$QuickActionImplCopyWith<$Res> {
  __$$QuickActionImplCopyWithImpl(
      _$QuickActionImpl _value, $Res Function(_$QuickActionImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? title = null,
    Object? description = null,
    Object? command = null,
    Object? type = null,
    Object? icon = freezed,
  }) {
    return _then(_$QuickActionImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      title: null == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      command: null == command
          ? _value.command
          : command // ignore: cast_nullable_to_non_nullable
              as String,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as QuickActionType,
      icon: freezed == icon
          ? _value.icon
          : icon // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$QuickActionImpl implements _QuickAction {
  const _$QuickActionImpl(
      {required this.id,
      required this.title,
      required this.description,
      required this.command,
      required this.type,
      this.icon});

  factory _$QuickActionImpl.fromJson(Map<String, dynamic> json) =>
      _$$QuickActionImplFromJson(json);

  @override
  final String id;
  @override
  final String title;
  @override
  final String description;
  @override
  final String command;
  @override
  final QuickActionType type;
  @override
  final String? icon;

  @override
  String toString() {
    return 'QuickAction(id: $id, title: $title, description: $description, command: $command, type: $type, icon: $icon)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$QuickActionImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.command, command) || other.command == command) &&
            (identical(other.type, type) || other.type == type) &&
            (identical(other.icon, icon) || other.icon == icon));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode =>
      Object.hash(runtimeType, id, title, description, command, type, icon);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$QuickActionImplCopyWith<_$QuickActionImpl> get copyWith =>
      __$$QuickActionImplCopyWithImpl<_$QuickActionImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$QuickActionImplToJson(
      this,
    );
  }
}

abstract class _QuickAction implements QuickAction {
  const factory _QuickAction(
      {required final String id,
      required final String title,
      required final String description,
      required final String command,
      required final QuickActionType type,
      final String? icon}) = _$QuickActionImpl;

  factory _QuickAction.fromJson(Map<String, dynamic> json) =
      _$QuickActionImpl.fromJson;

  @override
  String get id;
  @override
  String get title;
  @override
  String get description;
  @override
  String get command;
  @override
  QuickActionType get type;
  @override
  String? get icon;
  @override
  @JsonKey(ignore: true)
  _$$QuickActionImplCopyWith<_$QuickActionImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

AppConfig _$AppConfigFromJson(Map<String, dynamic> json) {
  return _AppConfig.fromJson(json);
}

/// @nodoc
mixin _$AppConfig {
  AppInfo get app => throw _privateConstructorUsedError;
  ApiConfig get api => throw _privateConstructorUsedError;
  FeatureConfig get features => throw _privateConstructorUsedError;
  UiConfig get ui => throw _privateConstructorUsedError;
  SecurityConfig get security => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $AppConfigCopyWith<AppConfig> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AppConfigCopyWith<$Res> {
  factory $AppConfigCopyWith(AppConfig value, $Res Function(AppConfig) then) =
      _$AppConfigCopyWithImpl<$Res, AppConfig>;
  @useResult
  $Res call(
      {AppInfo app,
      ApiConfig api,
      FeatureConfig features,
      UiConfig ui,
      SecurityConfig security});

  $AppInfoCopyWith<$Res> get app;
  $ApiConfigCopyWith<$Res> get api;
  $FeatureConfigCopyWith<$Res> get features;
  $UiConfigCopyWith<$Res> get ui;
  $SecurityConfigCopyWith<$Res> get security;
}

/// @nodoc
class _$AppConfigCopyWithImpl<$Res, $Val extends AppConfig>
    implements $AppConfigCopyWith<$Res> {
  _$AppConfigCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? app = null,
    Object? api = null,
    Object? features = null,
    Object? ui = null,
    Object? security = null,
  }) {
    return _then(_value.copyWith(
      app: null == app
          ? _value.app
          : app // ignore: cast_nullable_to_non_nullable
              as AppInfo,
      api: null == api
          ? _value.api
          : api // ignore: cast_nullable_to_non_nullable
              as ApiConfig,
      features: null == features
          ? _value.features
          : features // ignore: cast_nullable_to_non_nullable
              as FeatureConfig,
      ui: null == ui
          ? _value.ui
          : ui // ignore: cast_nullable_to_non_nullable
              as UiConfig,
      security: null == security
          ? _value.security
          : security // ignore: cast_nullable_to_non_nullable
              as SecurityConfig,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $AppInfoCopyWith<$Res> get app {
    return $AppInfoCopyWith<$Res>(_value.app, (value) {
      return _then(_value.copyWith(app: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $ApiConfigCopyWith<$Res> get api {
    return $ApiConfigCopyWith<$Res>(_value.api, (value) {
      return _then(_value.copyWith(api: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $FeatureConfigCopyWith<$Res> get features {
    return $FeatureConfigCopyWith<$Res>(_value.features, (value) {
      return _then(_value.copyWith(features: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $UiConfigCopyWith<$Res> get ui {
    return $UiConfigCopyWith<$Res>(_value.ui, (value) {
      return _then(_value.copyWith(ui: value) as $Val);
    });
  }

  @override
  @pragma('vm:prefer-inline')
  $SecurityConfigCopyWith<$Res> get security {
    return $SecurityConfigCopyWith<$Res>(_value.security, (value) {
      return _then(_value.copyWith(security: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$AppConfigImplCopyWith<$Res>
    implements $AppConfigCopyWith<$Res> {
  factory _$$AppConfigImplCopyWith(
          _$AppConfigImpl value, $Res Function(_$AppConfigImpl) then) =
      __$$AppConfigImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {AppInfo app,
      ApiConfig api,
      FeatureConfig features,
      UiConfig ui,
      SecurityConfig security});

  @override
  $AppInfoCopyWith<$Res> get app;
  @override
  $ApiConfigCopyWith<$Res> get api;
  @override
  $FeatureConfigCopyWith<$Res> get features;
  @override
  $UiConfigCopyWith<$Res> get ui;
  @override
  $SecurityConfigCopyWith<$Res> get security;
}

/// @nodoc
class __$$AppConfigImplCopyWithImpl<$Res>
    extends _$AppConfigCopyWithImpl<$Res, _$AppConfigImpl>
    implements _$$AppConfigImplCopyWith<$Res> {
  __$$AppConfigImplCopyWithImpl(
      _$AppConfigImpl _value, $Res Function(_$AppConfigImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? app = null,
    Object? api = null,
    Object? features = null,
    Object? ui = null,
    Object? security = null,
  }) {
    return _then(_$AppConfigImpl(
      app: null == app
          ? _value.app
          : app // ignore: cast_nullable_to_non_nullable
              as AppInfo,
      api: null == api
          ? _value.api
          : api // ignore: cast_nullable_to_non_nullable
              as ApiConfig,
      features: null == features
          ? _value.features
          : features // ignore: cast_nullable_to_non_nullable
              as FeatureConfig,
      ui: null == ui
          ? _value.ui
          : ui // ignore: cast_nullable_to_non_nullable
              as UiConfig,
      security: null == security
          ? _value.security
          : security // ignore: cast_nullable_to_non_nullable
              as SecurityConfig,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$AppConfigImpl implements _AppConfig {
  const _$AppConfigImpl(
      {required this.app,
      required this.api,
      required this.features,
      required this.ui,
      required this.security});

  factory _$AppConfigImpl.fromJson(Map<String, dynamic> json) =>
      _$$AppConfigImplFromJson(json);

  @override
  final AppInfo app;
  @override
  final ApiConfig api;
  @override
  final FeatureConfig features;
  @override
  final UiConfig ui;
  @override
  final SecurityConfig security;

  @override
  String toString() {
    return 'AppConfig(app: $app, api: $api, features: $features, ui: $ui, security: $security)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AppConfigImpl &&
            (identical(other.app, app) || other.app == app) &&
            (identical(other.api, api) || other.api == api) &&
            (identical(other.features, features) ||
                other.features == features) &&
            (identical(other.ui, ui) || other.ui == ui) &&
            (identical(other.security, security) ||
                other.security == security));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode =>
      Object.hash(runtimeType, app, api, features, ui, security);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$AppConfigImplCopyWith<_$AppConfigImpl> get copyWith =>
      __$$AppConfigImplCopyWithImpl<_$AppConfigImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$AppConfigImplToJson(
      this,
    );
  }
}

abstract class _AppConfig implements AppConfig {
  const factory _AppConfig(
      {required final AppInfo app,
      required final ApiConfig api,
      required final FeatureConfig features,
      required final UiConfig ui,
      required final SecurityConfig security}) = _$AppConfigImpl;

  factory _AppConfig.fromJson(Map<String, dynamic> json) =
      _$AppConfigImpl.fromJson;

  @override
  AppInfo get app;
  @override
  ApiConfig get api;
  @override
  FeatureConfig get features;
  @override
  UiConfig get ui;
  @override
  SecurityConfig get security;
  @override
  @JsonKey(ignore: true)
  _$$AppConfigImplCopyWith<_$AppConfigImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

AppInfo _$AppInfoFromJson(Map<String, dynamic> json) {
  return _AppInfo.fromJson(json);
}

/// @nodoc
mixin _$AppInfo {
  String get name => throw _privateConstructorUsedError;
  String get version => throw _privateConstructorUsedError;
  String get founder => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $AppInfoCopyWith<AppInfo> get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AppInfoCopyWith<$Res> {
  factory $AppInfoCopyWith(AppInfo value, $Res Function(AppInfo) then) =
      _$AppInfoCopyWithImpl<$Res, AppInfo>;
  @useResult
  $Res call({String name, String version, String founder, String description});
}

/// @nodoc
class _$AppInfoCopyWithImpl<$Res, $Val extends AppInfo>
    implements $AppInfoCopyWith<$Res> {
  _$AppInfoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? name = null,
    Object? version = null,
    Object? founder = null,
    Object? description = null,
  }) {
    return _then(_value.copyWith(
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      version: null == version
          ? _value.version
          : version // ignore: cast_nullable_to_non_nullable
              as String,
      founder: null == founder
          ? _value.founder
          : founder // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$AppInfoImplCopyWith<$Res> implements $AppInfoCopyWith<$Res> {
  factory _$$AppInfoImplCopyWith(
          _$AppInfoImpl value, $Res Function(_$AppInfoImpl) then) =
      __$$AppInfoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({String name, String version, String founder, String description});
}

/// @nodoc
class __$$AppInfoImplCopyWithImpl<$Res>
    extends _$AppInfoCopyWithImpl<$Res, _$AppInfoImpl>
    implements _$$AppInfoImplCopyWith<$Res> {
  __$$AppInfoImplCopyWithImpl(
      _$AppInfoImpl _value, $Res Function(_$AppInfoImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? name = null,
    Object? version = null,
    Object? founder = null,
    Object? description = null,
  }) {
    return _then(_$AppInfoImpl(
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      version: null == version
          ? _value.version
          : version // ignore: cast_nullable_to_non_nullable
              as String,
      founder: null == founder
          ? _value.founder
          : founder // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$AppInfoImpl implements _AppInfo {
  const _$AppInfoImpl(
      {required this.name,
      required this.version,
      required this.founder,
      required this.description});

  factory _$AppInfoImpl.fromJson(Map<String, dynamic> json) =>
      _$$AppInfoImplFromJson(json);

  @override
  final String name;
  @override
  final String version;
  @override
  final String founder;
  @override
  final String description;

  @override
  String toString() {
    return 'AppInfo(name: $name, version: $version, founder: $founder, description: $description)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AppInfoImpl &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.version, version) || other.version == version) &&
            (identical(other.founder, founder) || other.founder == founder) &&
            (identical(other.description, description) ||
                other.description == description));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode =>
      Object.hash(runtimeType, name, version, founder, description);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$AppInfoImplCopyWith<_$AppInfoImpl> get copyWith =>
      __$$AppInfoImplCopyWithImpl<_$AppInfoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$AppInfoImplToJson(
      this,
    );
  }
}

abstract class _AppInfo implements AppInfo {
  const factory _AppInfo(
      {required final String name,
      required final String version,
      required final String founder,
      required final String description}) = _$AppInfoImpl;

  factory _AppInfo.fromJson(Map<String, dynamic> json) = _$AppInfoImpl.fromJson;

  @override
  String get name;
  @override
  String get version;
  @override
  String get founder;
  @override
  String get description;
  @override
  @JsonKey(ignore: true)
  _$$AppInfoImplCopyWith<_$AppInfoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ApiConfig _$ApiConfigFromJson(Map<String, dynamic> json) {
  return _ApiConfig.fromJson(json);
}

/// @nodoc
mixin _$ApiConfig {
  String get baseUrl => throw _privateConstructorUsedError;
  int get timeout => throw _privateConstructorUsedError;
  int get retryAttempts => throw _privateConstructorUsedError;
  ApiEndpoints get endpoints => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ApiConfigCopyWith<ApiConfig> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ApiConfigCopyWith<$Res> {
  factory $ApiConfigCopyWith(ApiConfig value, $Res Function(ApiConfig) then) =
      _$ApiConfigCopyWithImpl<$Res, ApiConfig>;
  @useResult
  $Res call(
      {String baseUrl, int timeout, int retryAttempts, ApiEndpoints endpoints});

  $ApiEndpointsCopyWith<$Res> get endpoints;
}

/// @nodoc
class _$ApiConfigCopyWithImpl<$Res, $Val extends ApiConfig>
    implements $ApiConfigCopyWith<$Res> {
  _$ApiConfigCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? baseUrl = null,
    Object? timeout = null,
    Object? retryAttempts = null,
    Object? endpoints = null,
  }) {
    return _then(_value.copyWith(
      baseUrl: null == baseUrl
          ? _value.baseUrl
          : baseUrl // ignore: cast_nullable_to_non_nullable
              as String,
      timeout: null == timeout
          ? _value.timeout
          : timeout // ignore: cast_nullable_to_non_nullable
              as int,
      retryAttempts: null == retryAttempts
          ? _value.retryAttempts
          : retryAttempts // ignore: cast_nullable_to_non_nullable
              as int,
      endpoints: null == endpoints
          ? _value.endpoints
          : endpoints // ignore: cast_nullable_to_non_nullable
              as ApiEndpoints,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $ApiEndpointsCopyWith<$Res> get endpoints {
    return $ApiEndpointsCopyWith<$Res>(_value.endpoints, (value) {
      return _then(_value.copyWith(endpoints: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$ApiConfigImplCopyWith<$Res>
    implements $ApiConfigCopyWith<$Res> {
  factory _$$ApiConfigImplCopyWith(
          _$ApiConfigImpl value, $Res Function(_$ApiConfigImpl) then) =
      __$$ApiConfigImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String baseUrl, int timeout, int retryAttempts, ApiEndpoints endpoints});

  @override
  $ApiEndpointsCopyWith<$Res> get endpoints;
}

/// @nodoc
class __$$ApiConfigImplCopyWithImpl<$Res>
    extends _$ApiConfigCopyWithImpl<$Res, _$ApiConfigImpl>
    implements _$$ApiConfigImplCopyWith<$Res> {
  __$$ApiConfigImplCopyWithImpl(
      _$ApiConfigImpl _value, $Res Function(_$ApiConfigImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? baseUrl = null,
    Object? timeout = null,
    Object? retryAttempts = null,
    Object? endpoints = null,
  }) {
    return _then(_$ApiConfigImpl(
      baseUrl: null == baseUrl
          ? _value.baseUrl
          : baseUrl // ignore: cast_nullable_to_non_nullable
              as String,
      timeout: null == timeout
          ? _value.timeout
          : timeout // ignore: cast_nullable_to_non_nullable
              as int,
      retryAttempts: null == retryAttempts
          ? _value.retryAttempts
          : retryAttempts // ignore: cast_nullable_to_non_nullable
              as int,
      endpoints: null == endpoints
          ? _value.endpoints
          : endpoints // ignore: cast_nullable_to_non_nullable
              as ApiEndpoints,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ApiConfigImpl implements _ApiConfig {
  const _$ApiConfigImpl(
      {required this.baseUrl,
      this.timeout = 30000,
      this.retryAttempts = 3,
      required this.endpoints});

  factory _$ApiConfigImpl.fromJson(Map<String, dynamic> json) =>
      _$$ApiConfigImplFromJson(json);

  @override
  final String baseUrl;
  @override
  @JsonKey()
  final int timeout;
  @override
  @JsonKey()
  final int retryAttempts;
  @override
  final ApiEndpoints endpoints;

  @override
  String toString() {
    return 'ApiConfig(baseUrl: $baseUrl, timeout: $timeout, retryAttempts: $retryAttempts, endpoints: $endpoints)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ApiConfigImpl &&
            (identical(other.baseUrl, baseUrl) || other.baseUrl == baseUrl) &&
            (identical(other.timeout, timeout) || other.timeout == timeout) &&
            (identical(other.retryAttempts, retryAttempts) ||
                other.retryAttempts == retryAttempts) &&
            (identical(other.endpoints, endpoints) ||
                other.endpoints == endpoints));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode =>
      Object.hash(runtimeType, baseUrl, timeout, retryAttempts, endpoints);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ApiConfigImplCopyWith<_$ApiConfigImpl> get copyWith =>
      __$$ApiConfigImplCopyWithImpl<_$ApiConfigImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ApiConfigImplToJson(
      this,
    );
  }
}

abstract class _ApiConfig implements ApiConfig {
  const factory _ApiConfig(
      {required final String baseUrl,
      final int timeout,
      final int retryAttempts,
      required final ApiEndpoints endpoints}) = _$ApiConfigImpl;

  factory _ApiConfig.fromJson(Map<String, dynamic> json) =
      _$ApiConfigImpl.fromJson;

  @override
  String get baseUrl;
  @override
  int get timeout;
  @override
  int get retryAttempts;
  @override
  ApiEndpoints get endpoints;
  @override
  @JsonKey(ignore: true)
  _$$ApiConfigImplCopyWith<_$ApiConfigImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ApiEndpoints _$ApiEndpointsFromJson(Map<String, dynamic> json) {
  return _ApiEndpoints.fromJson(json);
}

/// @nodoc
mixin _$ApiEndpoints {
  String get health => throw _privateConstructorUsedError;
  String get chat => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ApiEndpointsCopyWith<ApiEndpoints> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ApiEndpointsCopyWith<$Res> {
  factory $ApiEndpointsCopyWith(
          ApiEndpoints value, $Res Function(ApiEndpoints) then) =
      _$ApiEndpointsCopyWithImpl<$Res, ApiEndpoints>;
  @useResult
  $Res call({String health, String chat});
}

/// @nodoc
class _$ApiEndpointsCopyWithImpl<$Res, $Val extends ApiEndpoints>
    implements $ApiEndpointsCopyWith<$Res> {
  _$ApiEndpointsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? health = null,
    Object? chat = null,
  }) {
    return _then(_value.copyWith(
      health: null == health
          ? _value.health
          : health // ignore: cast_nullable_to_non_nullable
              as String,
      chat: null == chat
          ? _value.chat
          : chat // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ApiEndpointsImplCopyWith<$Res>
    implements $ApiEndpointsCopyWith<$Res> {
  factory _$$ApiEndpointsImplCopyWith(
          _$ApiEndpointsImpl value, $Res Function(_$ApiEndpointsImpl) then) =
      __$$ApiEndpointsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({String health, String chat});
}

/// @nodoc
class __$$ApiEndpointsImplCopyWithImpl<$Res>
    extends _$ApiEndpointsCopyWithImpl<$Res, _$ApiEndpointsImpl>
    implements _$$ApiEndpointsImplCopyWith<$Res> {
  __$$ApiEndpointsImplCopyWithImpl(
      _$ApiEndpointsImpl _value, $Res Function(_$ApiEndpointsImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? health = null,
    Object? chat = null,
  }) {
    return _then(_$ApiEndpointsImpl(
      health: null == health
          ? _value.health
          : health // ignore: cast_nullable_to_non_nullable
              as String,
      chat: null == chat
          ? _value.chat
          : chat // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ApiEndpointsImpl implements _ApiEndpoints {
  const _$ApiEndpointsImpl({required this.health, required this.chat});

  factory _$ApiEndpointsImpl.fromJson(Map<String, dynamic> json) =>
      _$$ApiEndpointsImplFromJson(json);

  @override
  final String health;
  @override
  final String chat;

  @override
  String toString() {
    return 'ApiEndpoints(health: $health, chat: $chat)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ApiEndpointsImpl &&
            (identical(other.health, health) || other.health == health) &&
            (identical(other.chat, chat) || other.chat == chat));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, health, chat);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ApiEndpointsImplCopyWith<_$ApiEndpointsImpl> get copyWith =>
      __$$ApiEndpointsImplCopyWithImpl<_$ApiEndpointsImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ApiEndpointsImplToJson(
      this,
    );
  }
}

abstract class _ApiEndpoints implements ApiEndpoints {
  const factory _ApiEndpoints(
      {required final String health,
      required final String chat}) = _$ApiEndpointsImpl;

  factory _ApiEndpoints.fromJson(Map<String, dynamic> json) =
      _$ApiEndpointsImpl.fromJson;

  @override
  String get health;
  @override
  String get chat;
  @override
  @JsonKey(ignore: true)
  _$$ApiEndpointsImplCopyWith<_$ApiEndpointsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

FeatureConfig _$FeatureConfigFromJson(Map<String, dynamic> json) {
  return _FeatureConfig.fromJson(json);
}

/// @nodoc
mixin _$FeatureConfig {
  bool get founderMode => throw _privateConstructorUsedError;
  bool get telemetry => throw _privateConstructorUsedError;
  bool get autoTranslate => throw _privateConstructorUsedError;
  String get safetyLevel => throw _privateConstructorUsedError;
  int get tokenCap => throw _privateConstructorUsedError;
  int get maxLatency => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $FeatureConfigCopyWith<FeatureConfig> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $FeatureConfigCopyWith<$Res> {
  factory $FeatureConfigCopyWith(
          FeatureConfig value, $Res Function(FeatureConfig) then) =
      _$FeatureConfigCopyWithImpl<$Res, FeatureConfig>;
  @useResult
  $Res call(
      {bool founderMode,
      bool telemetry,
      bool autoTranslate,
      String safetyLevel,
      int tokenCap,
      int maxLatency});
}

/// @nodoc
class _$FeatureConfigCopyWithImpl<$Res, $Val extends FeatureConfig>
    implements $FeatureConfigCopyWith<$Res> {
  _$FeatureConfigCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? founderMode = null,
    Object? telemetry = null,
    Object? autoTranslate = null,
    Object? safetyLevel = null,
    Object? tokenCap = null,
    Object? maxLatency = null,
  }) {
    return _then(_value.copyWith(
      founderMode: null == founderMode
          ? _value.founderMode
          : founderMode // ignore: cast_nullable_to_non_nullable
              as bool,
      telemetry: null == telemetry
          ? _value.telemetry
          : telemetry // ignore: cast_nullable_to_non_nullable
              as bool,
      autoTranslate: null == autoTranslate
          ? _value.autoTranslate
          : autoTranslate // ignore: cast_nullable_to_non_nullable
              as bool,
      safetyLevel: null == safetyLevel
          ? _value.safetyLevel
          : safetyLevel // ignore: cast_nullable_to_non_nullable
              as String,
      tokenCap: null == tokenCap
          ? _value.tokenCap
          : tokenCap // ignore: cast_nullable_to_non_nullable
              as int,
      maxLatency: null == maxLatency
          ? _value.maxLatency
          : maxLatency // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$FeatureConfigImplCopyWith<$Res>
    implements $FeatureConfigCopyWith<$Res> {
  factory _$$FeatureConfigImplCopyWith(
          _$FeatureConfigImpl value, $Res Function(_$FeatureConfigImpl) then) =
      __$$FeatureConfigImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {bool founderMode,
      bool telemetry,
      bool autoTranslate,
      String safetyLevel,
      int tokenCap,
      int maxLatency});
}

/// @nodoc
class __$$FeatureConfigImplCopyWithImpl<$Res>
    extends _$FeatureConfigCopyWithImpl<$Res, _$FeatureConfigImpl>
    implements _$$FeatureConfigImplCopyWith<$Res> {
  __$$FeatureConfigImplCopyWithImpl(
      _$FeatureConfigImpl _value, $Res Function(_$FeatureConfigImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? founderMode = null,
    Object? telemetry = null,
    Object? autoTranslate = null,
    Object? safetyLevel = null,
    Object? tokenCap = null,
    Object? maxLatency = null,
  }) {
    return _then(_$FeatureConfigImpl(
      founderMode: null == founderMode
          ? _value.founderMode
          : founderMode // ignore: cast_nullable_to_non_nullable
              as bool,
      telemetry: null == telemetry
          ? _value.telemetry
          : telemetry // ignore: cast_nullable_to_non_nullable
              as bool,
      autoTranslate: null == autoTranslate
          ? _value.autoTranslate
          : autoTranslate // ignore: cast_nullable_to_non_nullable
              as bool,
      safetyLevel: null == safetyLevel
          ? _value.safetyLevel
          : safetyLevel // ignore: cast_nullable_to_non_nullable
              as String,
      tokenCap: null == tokenCap
          ? _value.tokenCap
          : tokenCap // ignore: cast_nullable_to_non_nullable
              as int,
      maxLatency: null == maxLatency
          ? _value.maxLatency
          : maxLatency // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$FeatureConfigImpl implements _FeatureConfig {
  const _$FeatureConfigImpl(
      {this.founderMode = false,
      this.telemetry = true,
      this.autoTranslate = false,
      this.safetyLevel = 'normal',
      this.tokenCap = 4000,
      this.maxLatency = 10000});

  factory _$FeatureConfigImpl.fromJson(Map<String, dynamic> json) =>
      _$$FeatureConfigImplFromJson(json);

  @override
  @JsonKey()
  final bool founderMode;
  @override
  @JsonKey()
  final bool telemetry;
  @override
  @JsonKey()
  final bool autoTranslate;
  @override
  @JsonKey()
  final String safetyLevel;
  @override
  @JsonKey()
  final int tokenCap;
  @override
  @JsonKey()
  final int maxLatency;

  @override
  String toString() {
    return 'FeatureConfig(founderMode: $founderMode, telemetry: $telemetry, autoTranslate: $autoTranslate, safetyLevel: $safetyLevel, tokenCap: $tokenCap, maxLatency: $maxLatency)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$FeatureConfigImpl &&
            (identical(other.founderMode, founderMode) ||
                other.founderMode == founderMode) &&
            (identical(other.telemetry, telemetry) ||
                other.telemetry == telemetry) &&
            (identical(other.autoTranslate, autoTranslate) ||
                other.autoTranslate == autoTranslate) &&
            (identical(other.safetyLevel, safetyLevel) ||
                other.safetyLevel == safetyLevel) &&
            (identical(other.tokenCap, tokenCap) ||
                other.tokenCap == tokenCap) &&
            (identical(other.maxLatency, maxLatency) ||
                other.maxLatency == maxLatency));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, founderMode, telemetry,
      autoTranslate, safetyLevel, tokenCap, maxLatency);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$FeatureConfigImplCopyWith<_$FeatureConfigImpl> get copyWith =>
      __$$FeatureConfigImplCopyWithImpl<_$FeatureConfigImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$FeatureConfigImplToJson(
      this,
    );
  }
}

abstract class _FeatureConfig implements FeatureConfig {
  const factory _FeatureConfig(
      {final bool founderMode,
      final bool telemetry,
      final bool autoTranslate,
      final String safetyLevel,
      final int tokenCap,
      final int maxLatency}) = _$FeatureConfigImpl;

  factory _FeatureConfig.fromJson(Map<String, dynamic> json) =
      _$FeatureConfigImpl.fromJson;

  @override
  bool get founderMode;
  @override
  bool get telemetry;
  @override
  bool get autoTranslate;
  @override
  String get safetyLevel;
  @override
  int get tokenCap;
  @override
  int get maxLatency;
  @override
  @JsonKey(ignore: true)
  _$$FeatureConfigImplCopyWith<_$FeatureConfigImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

UiConfig _$UiConfigFromJson(Map<String, dynamic> json) {
  return _UiConfig.fromJson(json);
}

/// @nodoc
mixin _$UiConfig {
  String get theme => throw _privateConstructorUsedError;
  String get primaryColor => throw _privateConstructorUsedError;
  String get secondaryColor => throw _privateConstructorUsedError;
  String get accentColor => throw _privateConstructorUsedError;
  String get fontFamily => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $UiConfigCopyWith<UiConfig> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $UiConfigCopyWith<$Res> {
  factory $UiConfigCopyWith(UiConfig value, $Res Function(UiConfig) then) =
      _$UiConfigCopyWithImpl<$Res, UiConfig>;
  @useResult
  $Res call(
      {String theme,
      String primaryColor,
      String secondaryColor,
      String accentColor,
      String fontFamily});
}

/// @nodoc
class _$UiConfigCopyWithImpl<$Res, $Val extends UiConfig>
    implements $UiConfigCopyWith<$Res> {
  _$UiConfigCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? theme = null,
    Object? primaryColor = null,
    Object? secondaryColor = null,
    Object? accentColor = null,
    Object? fontFamily = null,
  }) {
    return _then(_value.copyWith(
      theme: null == theme
          ? _value.theme
          : theme // ignore: cast_nullable_to_non_nullable
              as String,
      primaryColor: null == primaryColor
          ? _value.primaryColor
          : primaryColor // ignore: cast_nullable_to_non_nullable
              as String,
      secondaryColor: null == secondaryColor
          ? _value.secondaryColor
          : secondaryColor // ignore: cast_nullable_to_non_nullable
              as String,
      accentColor: null == accentColor
          ? _value.accentColor
          : accentColor // ignore: cast_nullable_to_non_nullable
              as String,
      fontFamily: null == fontFamily
          ? _value.fontFamily
          : fontFamily // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$UiConfigImplCopyWith<$Res>
    implements $UiConfigCopyWith<$Res> {
  factory _$$UiConfigImplCopyWith(
          _$UiConfigImpl value, $Res Function(_$UiConfigImpl) then) =
      __$$UiConfigImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String theme,
      String primaryColor,
      String secondaryColor,
      String accentColor,
      String fontFamily});
}

/// @nodoc
class __$$UiConfigImplCopyWithImpl<$Res>
    extends _$UiConfigCopyWithImpl<$Res, _$UiConfigImpl>
    implements _$$UiConfigImplCopyWith<$Res> {
  __$$UiConfigImplCopyWithImpl(
      _$UiConfigImpl _value, $Res Function(_$UiConfigImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? theme = null,
    Object? primaryColor = null,
    Object? secondaryColor = null,
    Object? accentColor = null,
    Object? fontFamily = null,
  }) {
    return _then(_$UiConfigImpl(
      theme: null == theme
          ? _value.theme
          : theme // ignore: cast_nullable_to_non_nullable
              as String,
      primaryColor: null == primaryColor
          ? _value.primaryColor
          : primaryColor // ignore: cast_nullable_to_non_nullable
              as String,
      secondaryColor: null == secondaryColor
          ? _value.secondaryColor
          : secondaryColor // ignore: cast_nullable_to_non_nullable
              as String,
      accentColor: null == accentColor
          ? _value.accentColor
          : accentColor // ignore: cast_nullable_to_non_nullable
              as String,
      fontFamily: null == fontFamily
          ? _value.fontFamily
          : fontFamily // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$UiConfigImpl implements _UiConfig {
  const _$UiConfigImpl(
      {this.theme = 'dark',
      this.primaryColor = '#0F172A',
      this.secondaryColor = '#1E293B',
      this.accentColor = '#3B82F6',
      this.fontFamily = 'Inter'});

  factory _$UiConfigImpl.fromJson(Map<String, dynamic> json) =>
      _$$UiConfigImplFromJson(json);

  @override
  @JsonKey()
  final String theme;
  @override
  @JsonKey()
  final String primaryColor;
  @override
  @JsonKey()
  final String secondaryColor;
  @override
  @JsonKey()
  final String accentColor;
  @override
  @JsonKey()
  final String fontFamily;

  @override
  String toString() {
    return 'UiConfig(theme: $theme, primaryColor: $primaryColor, secondaryColor: $secondaryColor, accentColor: $accentColor, fontFamily: $fontFamily)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$UiConfigImpl &&
            (identical(other.theme, theme) || other.theme == theme) &&
            (identical(other.primaryColor, primaryColor) ||
                other.primaryColor == primaryColor) &&
            (identical(other.secondaryColor, secondaryColor) ||
                other.secondaryColor == secondaryColor) &&
            (identical(other.accentColor, accentColor) ||
                other.accentColor == accentColor) &&
            (identical(other.fontFamily, fontFamily) ||
                other.fontFamily == fontFamily));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, theme, primaryColor,
      secondaryColor, accentColor, fontFamily);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$UiConfigImplCopyWith<_$UiConfigImpl> get copyWith =>
      __$$UiConfigImplCopyWithImpl<_$UiConfigImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$UiConfigImplToJson(
      this,
    );
  }
}

abstract class _UiConfig implements UiConfig {
  const factory _UiConfig(
      {final String theme,
      final String primaryColor,
      final String secondaryColor,
      final String accentColor,
      final String fontFamily}) = _$UiConfigImpl;

  factory _UiConfig.fromJson(Map<String, dynamic> json) =
      _$UiConfigImpl.fromJson;

  @override
  String get theme;
  @override
  String get primaryColor;
  @override
  String get secondaryColor;
  @override
  String get accentColor;
  @override
  String get fontFamily;
  @override
  @JsonKey(ignore: true)
  _$$UiConfigImplCopyWith<_$UiConfigImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

SecurityConfig _$SecurityConfigFromJson(Map<String, dynamic> json) {
  return _SecurityConfig.fromJson(json);
}

/// @nodoc
mixin _$SecurityConfig {
  String get founderPasscode => throw _privateConstructorUsedError;
  bool get enableBiometrics => throw _privateConstructorUsedError;
  int get sessionTimeout => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $SecurityConfigCopyWith<SecurityConfig> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $SecurityConfigCopyWith<$Res> {
  factory $SecurityConfigCopyWith(
          SecurityConfig value, $Res Function(SecurityConfig) then) =
      _$SecurityConfigCopyWithImpl<$Res, SecurityConfig>;
  @useResult
  $Res call(
      {String founderPasscode, bool enableBiometrics, int sessionTimeout});
}

/// @nodoc
class _$SecurityConfigCopyWithImpl<$Res, $Val extends SecurityConfig>
    implements $SecurityConfigCopyWith<$Res> {
  _$SecurityConfigCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? founderPasscode = null,
    Object? enableBiometrics = null,
    Object? sessionTimeout = null,
  }) {
    return _then(_value.copyWith(
      founderPasscode: null == founderPasscode
          ? _value.founderPasscode
          : founderPasscode // ignore: cast_nullable_to_non_nullable
              as String,
      enableBiometrics: null == enableBiometrics
          ? _value.enableBiometrics
          : enableBiometrics // ignore: cast_nullable_to_non_nullable
              as bool,
      sessionTimeout: null == sessionTimeout
          ? _value.sessionTimeout
          : sessionTimeout // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$SecurityConfigImplCopyWith<$Res>
    implements $SecurityConfigCopyWith<$Res> {
  factory _$$SecurityConfigImplCopyWith(_$SecurityConfigImpl value,
          $Res Function(_$SecurityConfigImpl) then) =
      __$$SecurityConfigImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String founderPasscode, bool enableBiometrics, int sessionTimeout});
}

/// @nodoc
class __$$SecurityConfigImplCopyWithImpl<$Res>
    extends _$SecurityConfigCopyWithImpl<$Res, _$SecurityConfigImpl>
    implements _$$SecurityConfigImplCopyWith<$Res> {
  __$$SecurityConfigImplCopyWithImpl(
      _$SecurityConfigImpl _value, $Res Function(_$SecurityConfigImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? founderPasscode = null,
    Object? enableBiometrics = null,
    Object? sessionTimeout = null,
  }) {
    return _then(_$SecurityConfigImpl(
      founderPasscode: null == founderPasscode
          ? _value.founderPasscode
          : founderPasscode // ignore: cast_nullable_to_non_nullable
              as String,
      enableBiometrics: null == enableBiometrics
          ? _value.enableBiometrics
          : enableBiometrics // ignore: cast_nullable_to_non_nullable
              as bool,
      sessionTimeout: null == sessionTimeout
          ? _value.sessionTimeout
          : sessionTimeout // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$SecurityConfigImpl implements _SecurityConfig {
  const _$SecurityConfigImpl(
      {this.founderPasscode = '0000',
      this.enableBiometrics = false,
      this.sessionTimeout = 3600});

  factory _$SecurityConfigImpl.fromJson(Map<String, dynamic> json) =>
      _$$SecurityConfigImplFromJson(json);

  @override
  @JsonKey()
  final String founderPasscode;
  @override
  @JsonKey()
  final bool enableBiometrics;
  @override
  @JsonKey()
  final int sessionTimeout;

  @override
  String toString() {
    return 'SecurityConfig(founderPasscode: $founderPasscode, enableBiometrics: $enableBiometrics, sessionTimeout: $sessionTimeout)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$SecurityConfigImpl &&
            (identical(other.founderPasscode, founderPasscode) ||
                other.founderPasscode == founderPasscode) &&
            (identical(other.enableBiometrics, enableBiometrics) ||
                other.enableBiometrics == enableBiometrics) &&
            (identical(other.sessionTimeout, sessionTimeout) ||
                other.sessionTimeout == sessionTimeout));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType, founderPasscode, enableBiometrics, sessionTimeout);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$SecurityConfigImplCopyWith<_$SecurityConfigImpl> get copyWith =>
      __$$SecurityConfigImplCopyWithImpl<_$SecurityConfigImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$SecurityConfigImplToJson(
      this,
    );
  }
}

abstract class _SecurityConfig implements SecurityConfig {
  const factory _SecurityConfig(
      {final String founderPasscode,
      final bool enableBiometrics,
      final int sessionTimeout}) = _$SecurityConfigImpl;

  factory _SecurityConfig.fromJson(Map<String, dynamic> json) =
      _$SecurityConfigImpl.fromJson;

  @override
  String get founderPasscode;
  @override
  bool get enableBiometrics;
  @override
  int get sessionTimeout;
  @override
  @JsonKey(ignore: true)
  _$$SecurityConfigImplCopyWith<_$SecurityConfigImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
