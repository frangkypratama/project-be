plugins {
    id("com.android.application")
    // Seperti templat Flutter terkini (AGP 9): plugin Kotlin dipasang otomatis oleh plugin Flutter;
    // menuliskannya di sini hanya memicu peringatan "will cause build failures in future versions".
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "com.bukuende.hkbp"
    compileSdk = 36
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        applicationId = "com.bukuende.hkbp"
        minSdk = 24
        targetSdk = 36
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        create("rilis") {
            val ks = System.getenv("KS_FILE")
            if (ks != null) {
                storeFile = file(ks)
                storePassword = System.getenv("KS_PASS")
                keyAlias = System.getenv("KS_ALIAS")
                keyPassword = System.getenv("KS_PASS")
            }
        }
    }

    lint {
        checkReleaseBuilds = false
        abortOnError = false
    }

    buildTypes {
        release {
            signingConfig = if (System.getenv("KS_FILE") != null) signingConfigs.getByName("rilis") else signingConfigs.getByName("debug")
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
    }
}

flutter {
    source = "../.."
}
