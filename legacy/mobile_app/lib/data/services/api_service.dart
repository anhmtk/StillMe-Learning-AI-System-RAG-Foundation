import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/config/app_config_service.dart';

final apiServiceProvider = Provider<ApiService>((ref) {
  final config = ref.watch(appConfigProvider).value;
  return ApiService(config);
});

class ApiService {
  late final Dio _dio;
  final AppConfig? _config;

  ApiService(this._config) {
    _dio = Dio(BaseOptions(
      baseUrl: _config?.api.baseUrl ?? 'http://160.191.89.99:21568',
      connectTimeout: Duration(milliseconds: _config?.api.timeout ?? 30000),
      receiveTimeout: Duration(milliseconds: _config?.api.timeout ?? 30000),
      sendTimeout: Duration(milliseconds: _config?.api.timeout ?? 30000),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));

    // Add interceptors
    _dio.interceptors.add(LogInterceptor(
      requestBody: true,
      responseBody: true,
      logPrint: (object) => print('[API] $object'),
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        // Add any custom headers here
        options.headers['X-Client'] = 'StillMe-Mobile';
        options.headers['X-Version'] = '1.0.0';
        handler.next(options);
      },
      onResponse: (response, handler) {
        handler.next(response);
      },
      onError: (error, handler) {
        // Handle common errors
        if (error.type == DioExceptionType.connectionTimeout ||
            error.type == DioExceptionType.receiveTimeout) {
          error = DioException(
            requestOptions: error.requestOptions,
            error: 'Connection timeout. Please check your internet connection.',
            type: error.type,
          );
        } else if (error.type == DioExceptionType.connectionError) {
          error = DioException(
            requestOptions: error.requestOptions,
            error: 'Unable to connect to server. Please check the server URL.',
            type: error.type,
          );
        }
        handler.next(error);
      },
    ));
  }

  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    try {
      return await _dio.get<T>(
        path,
        queryParameters: queryParameters,
        options: options,
      );
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    try {
      return await _dio.post<T>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
      );
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  Future<Response<T>> put<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    try {
      return await _dio.put<T>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
      );
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  Future<Response<T>> delete<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    try {
      return await _dio.delete<T>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
      );
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  Exception _handleDioError(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
        return ApiException('Connection timeout. Please check your internet connection.');
      case DioExceptionType.sendTimeout:
        return ApiException('Request timeout. Please try again.');
      case DioExceptionType.receiveTimeout:
        return ApiException('Response timeout. The server is taking too long to respond.');
      case DioExceptionType.badResponse:
        final statusCode = error.response?.statusCode;
        final message = error.response?.data?['message'] ?? error.response?.data?['error'] ?? 'Server error';
        return ApiException('Server error ($statusCode): $message');
      case DioExceptionType.cancel:
        return ApiException('Request was cancelled.');
      case DioExceptionType.connectionError:
        return ApiException('Unable to connect to server. Please check the server URL and your internet connection.');
      case DioExceptionType.badCertificate:
        return ApiException('SSL certificate error. Please check the server configuration.');
      case DioExceptionType.unknown:
      default:
        return ApiException('An unexpected error occurred: ${error.message}');
    }
  }

  void updateBaseUrl(String newBaseUrl) {
    _dio.options.baseUrl = newBaseUrl;
  }

  void updateTimeout(int timeoutMs) {
    _dio.options.connectTimeout = Duration(milliseconds: timeoutMs);
    _dio.options.receiveTimeout = Duration(milliseconds: timeoutMs);
    _dio.options.sendTimeout = Duration(milliseconds: timeoutMs);
  }
}

class ApiException implements Exception {
  final String message;
  ApiException(this.message);

  @override
  String toString() => 'ApiException: $message';
}
