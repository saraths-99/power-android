# {{PROJECT_NAME}} — Build Conventions

Owns the Gradle setup: version catalog, the single module build file, and the rules
for changing either. Package boundaries live in `module-architecture.md`.

## 1. Versions live in exactly one place

Every dependency and plugin version belongs in `gradle/libs.versions.toml`.

```kotlin
// correct
implementation(libs.androidx.core.ktx)

// wrong — never inline a coordinate or version in a build file
implementation("androidx.core:core-ktx:1.12.0")
```

To add a dependency: add a `[versions]` entry if the version is new, add the
`[libraries]` alias, then reference it as `libs.<alias-with-dots>`. Catalog aliases
use dashes; the Gradle accessor converts them to dots (`androidx-core-ktx` becomes
`libs.androidx.core.ktx`).

Compose artifacts are pinned by `androidx-compose-bom`. Add Compose libraries
**without** a version so the BOM controls them.

## 2. Kotlin and the Compose compiler are a matched pair

`kotlin` and `androidxComposeCompiler` in the catalog must stay compatible. Bumping
one without the other breaks the build. Check the table before changing either:
https://developer.android.com/jetpack/androidx/releases/compose-kotlin

The same care applies to `ksp`, whose version is derived from the Kotlin version
(`<kotlin>-<ksp>`), and to `androidxRoom`, which supplies both the Room runtime and
the Room Gradle plugin.

`composeOptions.kotlinCompilerExtensionVersion` reads from the catalog
(`libs.versions.androidxComposeCompiler.get()`), so there is only one place to
change it.

## 3. There are no convention plugins, on purpose

This project has one module, so shared build logic has nothing to be shared with.
`app/build.gradle.kts` applies AGP, Kotlin, KSP and Hilt directly and configures the
SDK levels inline. That is the correct trade at this size: a `build-logic` module for
a single consumer is pure overhead.

If the project grows into multiple modules, that is the point to introduce
`build-logic/convention/` — and the point to reconsider the architecture as a whole.
See section 5 of `module-architecture.md`.

## 4. Keep the build file readable

`app/build.gradle.kts` is the only build file that matters. Keep its sections in the
order they are in now: `plugins`, `android { }`, `room { }` if present,
`dependencies { }`. Group dependencies by purpose with a blank line between groups,
as the scaffold does.

Do not add `buildFeatures.buildConfig = true` unless something actually reads
`BuildConfig`; it is disabled project-wide in `gradle.properties` because it costs
build time.

## 5. SDK and toolchain

- `compileSdk {{COMPILE_SDK}}`, `targetSdk {{TARGET_SDK}}`, `minSdk {{MIN_SDK}}`,
  set once in `app/build.gradle.kts`.
- Java {{JAVA_VERSION}} for both the Java and Kotlin targets. `compileOptions` and
  `kotlinOptions` must agree; a mismatch produces confusing errors from KSP.

## 6. Build commands

```bash
./gradlew :app:assembleDebug          # debug APK
./gradlew testDebugUnitTest           # unit tests
./gradlew build                       # everything, including lint and release
```

The wrapper needs `gradle/wrapper/gradle-wrapper.jar`. If it is missing, run
`gradle wrapper --gradle-version <version>` or open the project in Android Studio.

The Android SDK location must come from `ANDROID_HOME`, `ANDROID_SDK_ROOT`, or
`local.properties`. `local.properties` is machine-specific and must stay gitignored.

## 7. Release builds

The release build type runs R8 with `proguard-android-optimize.txt` plus
`app/proguard-rules.pro`. No signing config is generated. Add one, keep the keystore
and its credentials out of version control, and verify a minified release build
before shipping — R8 problems never show up in debug builds.
