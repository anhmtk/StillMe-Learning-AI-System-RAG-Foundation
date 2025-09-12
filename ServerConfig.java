// Android Server Configuration for StillMe
// Cấu hình server cho StillMe Android App

package com.stillme.android.config;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;
import org.json.JSONObject;
import java.io.IOException;
import java.util.concurrent.TimeUnit;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

public class ServerConfig {
    private static final String TAG = "ServerConfig";
    private static final String PREFS_NAME = "stillme_server_config";
    private static final String KEY_BASE_URL = "base_url";
    private static final String KEY_TIMEOUT = "timeout";
    private static final String KEY_RETRY_ATTEMPTS = "retry_attempts";
    private static final String KEY_RETRY_DELAY = "retry_delay";
    
    // Default values
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
        
        // 2. Check runtime config file (if available)
        String runtimeUrl = readRuntimeConfig();
        if (runtimeUrl != null && !runtimeUrl.isEmpty()) {
            return runtimeUrl;
        }
        
        // 3. Check shared preferences
        return prefs.getString(KEY_BASE_URL, DEFAULT_BASE_URL);
    }
    
    public void setBaseUrl(String baseUrl) {
        prefs.edit().putString(KEY_BASE_URL, baseUrl).apply();
        // Recreate HTTP client with new URL
        this.httpClient = createHttpClient();
    }
    
    public int getTimeout() {
        return prefs.getInt(KEY_TIMEOUT, DEFAULT_TIMEOUT);
    }
    
    public void setTimeout(int timeout) {
        prefs.edit().putInt(KEY_TIMEOUT, timeout).apply();
        this.httpClient = createHttpClient();
    }
    
    public int getRetryAttempts() {
        return prefs.getInt(KEY_RETRY_ATTEMPTS, DEFAULT_RETRY_ATTEMPTS);
    }
    
    public void setRetryAttempts(int attempts) {
        prefs.edit().putInt(KEY_RETRY_ATTEMPTS, attempts).apply();
    }
    
    public int getRetryDelay() {
        return prefs.getInt(KEY_RETRY_DELAY, DEFAULT_RETRY_DELAY);
    }
    
    public void setRetryDelay(int delay) {
        prefs.edit().putInt(KEY_RETRY_DELAY, delay).apply();
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
    
    public String getLivezEndpoint() {
        return getEndpoint("/livez");
    }
    
    public String getReadyzEndpoint() {
        return getEndpoint("/readyz");
    }
    
    public String getInferenceEndpoint() {
        return getEndpoint("/inference");
    }
    
    private String readRuntimeConfig() {
        try {
            // Try to read from assets or internal storage
            // This would need to be implemented based on your app's file sync mechanism
            return null;
        } catch (Exception e) {
            Log.w(TAG, "Could not read runtime config: " + e.getMessage());
            return null;
        }
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
                status.environment = json.optString("environment", "");
                
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
        public String environment;
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
