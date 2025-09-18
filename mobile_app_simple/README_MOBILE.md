# StillMe Mobile App

## Response Schema Adapter

The mobile app uses a flexible response adapter to handle different server response formats:

### Supported Response Fields (in priority order):
1. `response` - StillMe VPS format
2. `text` - Standard format
3. `reply` - Alternative format
4. `message` - Generic format
5. `choices[0].text` - OpenAI format
6. `choices[0].message.content` - OpenAI chat format

### Example VPS Response:
```json
{
  "meta": {
    "confidence": {"in": 1.0, "out": 1.0},
    "engines": {"in": "none", "out": "none"},
    "input_translated": false,
    "orig_lang": "vi",
    "target_lang": "vi"
  },
  "model": "StillMe-VPS-Placeholder",
  "response": "Chào bạn! Mình là StillMe AI...",
  "timestamp": "2025-09-18T17:44:45.420720"
}
```

## Troubleshooting: No AI Response

### Common Issues:

1. **"Không có phản hồi từ AI"**
   - Check network connection
   - Verify VPS is running: `http://160.191.89.99:21568/health`
   - Check Dio logs in debug console

2. **"Schema mismatch"**
   - Server response doesn't contain expected text fields
   - Check raw response in logs
   - Update adapter if server format changed

3. **Network errors**
   - Check Android network permissions
   - Verify network security config allows cleartext traffic
   - Test with curl: `curl -X POST http://160.191.89.99:21568/chat -H "Content-Type: application/json" -d '{"message":"test"}'`

### Debug Steps:

1. Enable verbose logging: `flutter run -v`
2. Check Dio interceptor logs for request/response
3. Use Test Connection in Settings to verify endpoints
4. Run `dart test_ping.dart` for standalone testing

### Network Configuration:

- **Base URL**: `http://160.191.89.99:21568`
- **Timeout**: 20 seconds
- **Cleartext Traffic**: Enabled for VPS IP
- **Network Security**: Whitelisted IP in `network_security_config.xml`
