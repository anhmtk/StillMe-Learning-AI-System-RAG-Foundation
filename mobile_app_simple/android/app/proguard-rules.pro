# Flutter specific rules
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.**  { *; }
-keep class io.flutter.util.**  { *; }
-keep class io.flutter.view.**  { *; }
-keep class io.flutter.**  { *; }
-keep class io.flutter.plugins.**  { *; }

# Keep native methods
-keepclasseswithmembernames class * {
    native <methods>;
}

# Keep Gson classes
-keepattributes Signature
-keepattributes *Annotation*
-dontwarn sun.misc.**
-keep class com.google.gson.** { *; }
-keep class * implements com.google.gson.TypeAdapterFactory
-keep class * implements com.google.gson.JsonSerializer
-keep class * implements com.google.gson.JsonDeserializer

# Keep Dio classes
-keep class dio.** { *; }
-keep class okhttp3.** { *; }
-keep class okio.** { *; }

# Security: Remove logging
-assumenosideeffects class android.util.Log {
    public static *** d(...);
    public static *** v(...);
    public static *** i(...);
}

# Security: Remove debug info
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile

# Security: Obfuscate package names
-repackageclasses ''
-flattenpackagehierarchy ''

# Keep essential classes for reflection
-keep class * extends java.lang.Exception
-keep class * implements java.io.Serializable
