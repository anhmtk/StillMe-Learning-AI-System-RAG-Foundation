plugins {
    id("com.android.application")
    id("kotlin-android")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "com.stillme.mobile"
    compileSdk = 36
    ndkVersion = flutter.ndkVersion
    
    buildFeatures {
        buildConfig = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_11.toString()
    }

    defaultConfig {
        applicationId = "com.stillme.mobile"
        minSdk = flutter.minSdkVersion
        targetSdk = 34
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    flavorDimensions += "environment"
    productFlavors {
        create("dev") {
            dimension = "environment"
            applicationIdSuffix = ".dev"
            versionNameSuffix = "-dev"
            buildConfigField("boolean", "ENABLE_LOGGING", "true")
            buildConfigField("boolean", "ALLOW_HTTP", "true")
            manifestPlaceholders["allowHttp"] = "true"
            manifestPlaceholders["flavor"] = "dev"
        }
        create("prod") {
            dimension = "environment"
            buildConfigField("boolean", "ENABLE_LOGGING", "false")
            buildConfigField("boolean", "ALLOW_HTTP", "false")
            manifestPlaceholders["allowHttp"] = "false"
            manifestPlaceholders["flavor"] = "prod"
        }
    }

    buildTypes {
        debug {
            isDebuggable = true
            applicationIdSuffix = ".debug"
        }
        release {
            isMinifyEnabled = false
            isShrinkResources = false
            signingConfig = signingConfigs.getByName("debug") // TODO: Use release signing
        }
    }
}

flutter {
    source = "../.."
}
