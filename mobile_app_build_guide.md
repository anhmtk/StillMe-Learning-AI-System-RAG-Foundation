# 📱 Mobile App Build Guide - StillMe Android

## 🚀 Quick Start

### **1. Update Build Configuration**

Add to your `android/app/build.gradle`:

```gradle
android {
    buildTypes {
        debug {
            // Debug configuration
            buildConfigField "String", "SERVER_BASE_URL", "\"http://192.168.1.8:8000\""
            buildConfigField "int", "SERVER_TIMEOUT", "10000"
            buildConfigField "int", "RETRY_ATTEMPTS", "3"
            buildConfigField "int", "RETRY_DELAY", "1000"
            
            // Enable cleartext traffic for development
            manifestPlaceholders = [usesCleartextTraffic: "true"]
        }
        
        release {
            // Production configuration
            buildConfigField "String", "SERVER_BASE_URL", "\"https://api.stillme.ai\""
            buildConfigField "int", "SERVER_TIMEOUT", "15000"
            buildConfigField "int", "RETRY_ATTEMPTS", "5"
            buildConfigField "int", "RETRY_DELAY", "2000"
            
            manifestPlaceholders = [usesCleartextTraffic: "false"]
        }
    }
}
```

### **2. Add Network Security Config**

Create `android/app/src/main/res/xml/network_security_config.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <!-- Tailscale IP range -->
        <domain includeSubdomains="true">100.64.0.0</domain>
        <!-- LAN IP ranges -->
        <domain includeSubdomains="true">192.168.0.0</domain>
        <domain includeSubdomains="true">10.0.0.0</domain>
        <!-- Localhost for emulator -->
        <domain includeSubdomains="true">localhost</domain>
        <domain includeSubdomains="true">127.0.0.1</domain>
        <domain includeSubdomains="true">10.0.2.2</domain>
    </domain-config>
</network-security-config>
```

### **3. Update AndroidManifest.xml**

Add to `android/app/src/main/AndroidManifest.xml`:

```xml
<application
    android:networkSecurityConfig="@xml/network_security_config"
    android:usesCleartextTraffic="true">
    
    <!-- Your existing application content -->
    
</application>
```

### **4. Add Server Configuration Class**

Create `android/app/src/main/java/com/stillme/android/config/ServerConfig.java`:

```java
package com.stillme.android.config;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;
import org.json.JSONObject;
import java.util.concurrent.TimeUnit;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

public class ServerConfig {
    private static final String TAG = "ServerConfig";
    private static final String PREFS_NAME = "stillme_server_config";
    private static final String KEY_BASE_URL = "base_url";
    
    // Default values from BuildConfig
    private static final String DEFAULT_BASE_URL = BuildConfig.SERVER_BASE_URL;
    private static final int DEFAULT_TIMEOUT = BuildConfig.SERVER_TIMEOUT;
    private static final int DEFAULT_RETRY_ATTEMPTS = BuildConfig.RETRY_ATTEMPTS;
    private static final int DEFAULT_RETRY_DELAY = BuildConfig.RETRY_DELAY;
    
    private Context context;
    private SharedPreferences prefs;
    private OkHttpClient httpClient;
    
    public ServerConfig(Context context) {
        this.context = context;
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        this.httpClient = createHttpClient();
    }
    
    private OkHttpClient createHttpClient() {
        return new OkHttpClient.Builder()
                .connectTimeout(getTimeout(), TimeUnit.MILLISECONDS)
                .readTimeout(getTimeout(), TimeUnit.MILLISECONDS)
                .writeTimeout(getTimeout(), TimeUnit.MILLISECONDS)
                .build();
    }
    
    public String getBaseUrl() {
        // 1. Check environment variable (if available)
        String envUrl = System.getenv("SERVER_BASE_URL");
        if (envUrl != null && !envUrl.isEmpty()) {
            return envUrl;
        }
        
        // 2. Check shared preferences
        return prefs.getString(KEY_BASE_URL, DEFAULT_BASE_URL);
    }
    
    public void setBaseUrl(String baseUrl) {
        prefs.edit().putString(KEY_BASE_URL, baseUrl).apply();
        this.httpClient = createHttpClient();
    }
    
    public int getTimeout() {
        return prefs.getInt("timeout", DEFAULT_TIMEOUT);
    }
    
    public int getRetryAttempts() {
        return prefs.getInt("retry_attempts", DEFAULT_RETRY_ATTEMPTS);
    }
    
    public int getRetryDelay() {
        return prefs.getInt("retry_delay", DEFAULT_RETRY_DELAY);
    }
    
    public String getEndpoint(String endpoint) {
        String baseUrl = getBaseUrl();
        if (endpoint.startsWith("/")) {
            return baseUrl + endpoint;
        } else {
            return baseUrl + "/" + endpoint;
        }
    }
    
    public String getVersionEndpoint() {
        return getEndpoint("/version");
    }
    
    public String getHealthEndpoint() {
        return getEndpoint("/health");
    }
    
    public String getWebSocketEndpoint(String clientId) {
        return getEndpoint("/ws/" + clientId).replace("http://", "ws://").replace("https://", "wss://");
    }
    
    public String getApiMessageEndpoint() {
        return getEndpoint("/api/message");
    }
    
    public ServerStatus testConnection() {
        ServerStatus status = new ServerStatus();
        status.baseUrl = getBaseUrl();
        
        try {
            Request request = new Request.Builder()
                    .url(getVersionEndpoint())
                    .build();
            
            Response response = httpClient.newCall(request).execute();
            
            if (response.isSuccessful()) {
                String responseBody = response.body().string();
                JSONObject json = new JSONObject(responseBody);
                
                status.isConnected = true;
                status.serverName = json.optString("name", "Unknown");
                status.serverVersion = json.optString("version", "Unknown");
                status.buildTime = json.optString("build_time", "");
                
                Log.i(TAG, "Server connection successful: " + status.serverName + " v" + status.serverVersion);
            } else {
                status.isConnected = false;
                status.error = "HTTP " + response.code() + ": " + response.message();
                Log.e(TAG, "Server connection failed: " + status.error);
            }
            
            response.close();
            
        } catch (Exception e) {
            status.isConnected = false;
            status.error = e.getMessage();
            Log.e(TAG, "Server connection error: " + status.error);
        }
        
        return status;
    }
    
    public OkHttpClient getHttpClient() {
        return httpClient;
    }
    
    public static class ServerStatus {
        public String baseUrl;
        public boolean isConnected;
        public String serverName;
        public String serverVersion;
        public String buildTime;
        public String error;
        
        @Override
        public String toString() {
            if (isConnected) {
                return String.format("Connected to %s v%s at %s", 
                        serverName, serverVersion, baseUrl);
            } else {
                return String.format("Connection failed to %s: %s", baseUrl, error);
            }
        }
    }
}
```

### **5. Build Commands**

```bash
# Clean and rebuild
cd android
./gradlew clean
./gradlew assembleDebug

# Install on device
./gradlew installDebug

# Or use React Native CLI
npx react-native run-android
```

### **6. Test Connection**

Add this to your main activity or app initialization:

```java
// Test server connection
ServerConfig config = new ServerConfig(this);
ServerConfig.ServerStatus status = config.testConnection();

if (status.isConnected) {
    Log.i("StillMe", "Connected to server: " + status.serverName + " v" + status.serverVersion);
    // Proceed with app initialization
} else {
    Log.e("StillMe", "Failed to connect to server: " + status.error);
    // Show error message to user
}
```

## 🔧 Configuration Summary

- **Server URL**: `http://192.168.1.8:8000` (Gateway)
- **WebSocket**: `ws://192.168.1.8:8000/ws/{client_id}`
- **REST API**: `http://192.168.1.8:8000/api/message`
- **Health Check**: `http://192.168.1.8:8000/health`
- **Version**: `http://192.168.1.8:8000/version`

## 🚨 Important Notes

1. **Development Only**: Cleartext traffic is enabled for development
2. **Production**: Use HTTPS and disable cleartext traffic
3. **Network Security**: Only allow specific IP ranges
4. **Testing**: Test on both emulator and real device
5. **Firewall**: Ensure port 8000 is accessible

## 🎯 Expected Results

After rebuilding:
- ✅ App connects to Gateway at `http://192.168.1.8:8000`
- ✅ WebSocket connection established
- ✅ REST API calls work
- ✅ Health checks pass
- ✅ AI messages flow through Gateway

---

**Ready for Mobile App Rebuild!** 📱
