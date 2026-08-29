plugins {
    alias(libs.plugins.{{PREFIX}}.android.application)
    alias(libs.plugins.{{PREFIX}}.android.application.compose)
    alias(libs.plugins.{{PREFIX}}.hilt)
}

android {
    namespace = "{{PKG}}"

    defaultConfig {
        applicationId = "{{PKG}}"
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

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
{{APP_DEPENDENCIES}}
}
