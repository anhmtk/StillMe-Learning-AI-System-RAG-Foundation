import 'dart:convert';
import 'package:http/http.dart' as http;

void main() async {
  print('🔍 Testing StillMe Mobile App Connection...');
  
  final baseUrl = 'http://160.191.89.99:21568';
  
  try {
    // Test health endpoint
    print('\n📡 Testing /health endpoint...');
    final healthResponse = await http.get(
      Uri.parse('$baseUrl/health'),
      headers: {'Content-Type': 'application/json'},
    ).timeout(const Duration(seconds: 10));
    
    print('Status: ${healthResponse.statusCode}');
    print('Headers: ${healthResponse.headers}');
    print('Body: ${healthResponse.body}');
    
    if (healthResponse.statusCode == 200) {
      print('✅ Health check PASSED');
    } else {
      print('❌ Health check FAILED');
    }
    
    // Test chat endpoint with standardized body
    print('\n💬 Testing /chat endpoint...');
    final chatBody = {
      "message": "ping from mobile",
      "session_id": "test_${DateTime.now().millisecondsSinceEpoch}",
      "metadata": {
        "persona": "assistant",
        "language": "vi",
        "founder_command": false,
        "debug": true
      }
    };
    
    final chatResponse = await http.post(
      Uri.parse('$baseUrl/chat'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(chatBody),
    ).timeout(const Duration(seconds: 30));
    
    print('Status: ${chatResponse.statusCode}');
    print('Headers: ${chatResponse.headers}');
    print('Body: ${chatResponse.body}');
    
    if (chatResponse.statusCode == 200) {
      final data = jsonDecode(chatResponse.body);
      print('✅ Chat endpoint PASSED');
      
      // Extract text with same logic as mobile app
      String? extractText(dynamic d) {
        if (d == null) return null;
        if (d is Map<String, dynamic>) {
          return d['response'] ??  // StillMe VPS uses 'response'
                 d['text'] ??
                 d['reply'] ??
                 d['message'] ??
                 (d['choices'] is List && d['choices'].isNotEmpty ? d['choices'][0]['text'] : null) ??
                 (d['choices']?[0]?['message']?['content']);
        }
        return null;
      }
      
      final text = extractText(data);
      print('Extracted text: $text');
      print('Model: ${data['model'] ?? 'unknown'}');
      print('Usage: ${data['usage'] ?? 'none'}');
    } else {
      print('❌ Chat endpoint FAILED');
    }
    
  } catch (e) {
    print('❌ Connection failed: $e');
  }
  
  print('\n🏁 Test completed');
}
