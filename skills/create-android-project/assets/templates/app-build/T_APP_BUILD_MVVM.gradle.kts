plugins {
{{PLUGINS}}
}

android {
    namespace = "{{PKG}}"
    compileSdk = {{COMPILE_SDK}}

    defaultConfig {
        applicationId = "{{PKG}}"
        minSdk = {{MIN_SDK}}
        targetSdk = {{TARGET_SDK}}
        versionCode = 1
        versionName = "1.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = {{MINIFY}}
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
            // No release signing config is generated. Add one before publishing.
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_{{JAVA_VERSION}}
        targetCompatibility = JavaVersion.VERSION_{{JAVA_VERSION}}
    }

    kotlinOptions {
        jvmTarget = "{{JAVA_VERSION}}"
    }

    buildFeatures {
        compose = true
    }

    composeOptions {
        // Must stay compatible with the Kotlin version in the catalog.
        kotlinCompilerExtensionVersion = libs.versions.androidxComposeCompiler.get()
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}
{{ROOM_BLOCK}}
dependencies {
{{DEPENDENCIES}}
}
