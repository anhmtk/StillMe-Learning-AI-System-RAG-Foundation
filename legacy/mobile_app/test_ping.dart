#!/usr/bin/env dart

import 'dart:convert';
import 'dart:io';

/// Test script to ping StillMe VPS server
/// Usage: dart test_ping.dart [base_url]

void main(List<String> args) async {
  final baseUrl = args.isNotEmpty ? args[0] : 'http://160.191.89.99:21568';
  
  print('🔍 Testing StillMe VPS Connection');
  print('================================');
  print('Base URL: $baseUrl');
  print('');
  
  try {
    // Test health endpoint
    print('📡 Testing health endpoint...');
    final healthResponse = await _testHealth(baseUrl);
    print('✅ Health check: ${healthResponse['status']}');
    print('');
    
    // Test chat endpoint
    print('💬 Testing chat endpoint...');
    final chatResponse = await _testChat(baseUrl);
    print('✅ Chat response: ${chatResponse['response']?.substring(0, 50)}...');
    print('');
    
    // Display response details
    print('📊 Response Details:');
    print('  - Model: ${chatResponse['model'] ?? 'N/A'}');
    print('  - Latency: ${chatResponse['latency_ms'] ?? 'N/A'}ms');
    print('  - Tokens: ${chatResponse['usage']?['total_tokens'] ?? 'N/A'}');
    print('  - Cost: \$${chatResponse['cost_estimate_usd']?.toStringAsFixed(4) ?? 'N/A'}');
    print('');
    
    print('🎉 All tests passed! Server is ready for mobile app.');
    
  } catch (e) {
    print('❌ Test failed: $e');
    exit(1);
  }
}

Future<Map<String, dynamic>> _testHealth(String baseUrl) async {
  final client = HttpClient();
  
  try {
    final request = await client.getUrl(Uri.parse('$baseUrl/health'));
    final response = await request.close();
    
    if (response.statusCode != 200) {
      throw Exception('Health check failed with status: ${response.statusCode}');
    }
    
    final responseBody = await response.transform(utf8.decoder).join();
    return json.decode(responseBody);
    
  } finally {
    client.close();
  }
}

Future<Map<String, dynamic>> _testChat(String baseUrl) async {
  final client = HttpClient();
  
  try {
    final request = await client.postUrl(Uri.parse('$baseUrl/chat'));
    request.headers.set('Content-Type', 'application/json');
    
    final requestBody = json.encode({
      'message': 'Hello StillMe! This is a test from mobile app.',
      'session_id': 'test-session-${DateTime.now().millisecondsSinceEpoch}',
      'metadata': {
        'persona': 'assistant',
        'language': 'en',
        'debug': true,
      }
    });
    
    request.write(requestBody);
    final response = await request.close();
    
    if (response.statusCode != 200) {
      throw Exception('Chat request failed with status: ${response.statusCode}');
    }
    
    final responseBody = await response.transform(utf8.decoder).join();
    return json.decode(responseBody);
    
  } finally {
    client.close();
  }
}
