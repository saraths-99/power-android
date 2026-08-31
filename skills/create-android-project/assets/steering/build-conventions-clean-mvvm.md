# {{PROJECT_NAME}} — Build Conventions

Owns the Gradle setup: version catalog, convention plugins, and the rules for
changing either. Module boundaries live in `module-architecture.md`.

## 1. Versions live in exactly one place

Every dependency and plugin version belongs in `gradle/libs.versions.toml`.

```kotlin
// correct
implementation(libs.androidx.core.ktx)

// wrong — never inline a coordinate or version in a module build file
implementation("androidx.core:core-ktx:1.12.0")
```

To add a dependency: add a `[versions]` entry if the version is new, add the
`[libraries]` alias, then reference it as `libs.<alias-with-dots>`. Catalog
aliases use dashes; the Gradle accessor converts them to dots
(`androidx-core-ktx` becomes `libs.androidx.core.ktx`).

Compose artifacts are pinned by `androidx-compose-bom`. Add Compose libraries
**without** a version so the BOM controls them.

## 2. Kotlin and the Compose compiler are a matched pair

`kotlin` and `androidxComposeCompiler` in the catalog must stay compatible. Bumping
one without the other breaks the build. Check the compatibility table before
changing either:
https://developer.android.com/jetpack/androidx/releases/compose-kotlin

Same care applies to `ksp`, whose version is derived from the Kotlin version
(`<kotlin>-<ksp>`), and to `androidxRoom`, which supplies both the Room runtime and
the Room Gradle plugin.

## 3. Module build files stay thin

Shared build logic lives in `build-logic/convention/`. A module build file should
be a plugin list, a namespace, and dependencies — nothing else.

```kotlin
plugins {
    alias(libs.plugins.{{PREFIX}}.android.library)
    alias(libs.plugins.{{PREFIX}}.hilt)
}

android {
    namespace = "{{PACKAGE_NAME}}.core.example"
}

dependencies {
    api(projects.domain)
}
```

Available convention plugins:

| Alias | Applies |
|---|---|
| `{{PREFIX}}.android.application` | AGP application, Kotlin, SDK levels, Java {{JAVA_VERSION}} |
| `{{PREFIX}}.android.application.compose` | Compose for the app module |
| `{{PREFIX}}.android.library` | AGP library, Kotlin, SDK levels, JUnit |
| `{{PREFIX}}.android.library.compose` | Compose for a library module |
| `{{PREFIX}}.android.feature` | library + compose + hilt + `domain`, `core:ui`, `core:designsystem` |
| `{{PREFIX}}.android.room` | Room plugin, KSP, Room dependencies, schema export |
| `{{PREFIX}}.hilt` | KSP, Hilt plugin, Hilt dependencies |
| `{{PREFIX}}.jvm.library` | Kotlin JVM, used by `domain` so it stays framework-free |

`{{PREFIX}}.android.feature` deliberately does **not** bring in `data`. Feature
modules see use cases from `domain`; only `app` depends on `data`. If a feature
build file needs `projects.data`, the design has gone wrong, not the convention
plugin.

If the same configuration block is being copied into a third module, move it into a
convention plugin instead.

## 4. Changing a convention plugin

Convention plugin sources are in
`build-logic/convention/src/main/kotlin/`. To add one:

1. Write the `Plugin<Project>` class.
2. Register it in `build-logic/convention/build.gradle.kts` under `gradlePlugin`,
   with an id in the `{{PREFIX}}.*` namespace.
3. Add a matching `[plugins]` alias in `gradle/libs.versions.toml` with
   `version = "unspecified"`.

Third-party Gradle plugins that a convention plugin applies by id must also be
declared with `apply false` in the root `build.gradle.kts`. That is what puts them
on the classpath so `pluginManager.apply("…")` can resolve them. Skipping this step
produces a "plugin not found" failure at configuration time.

Types from a Gradle plugin's API (for example `RoomExtension`) additionally need a
`compileOnly` entry in `build-logic/convention/build.gradle.kts`.

Convention plugins configure the concrete `ApplicationExtension` and
`LibraryExtension` types rather than the star-projected `CommonExtension`. Keep it
that way: `CommonExtension`'s type-parameter count changes between AGP releases.

## 5. SDK and toolchain

- `compileSdk {{COMPILE_SDK}}`, `targetSdk {{TARGET_SDK}}`, `minSdk {{MIN_SDK}}`,
  set once in the convention plugins, never per module.
- Java {{JAVA_VERSION}} for both Java and Kotlin targets.
- `targetSdk` is an application concern. Do not set it in library modules.

## 6. Build commands

```bash
./gradlew :app:assembleDebug          # debug APK
./gradlew testDebugUnitTest           # unit tests
./gradlew build                       # everything, including lint and release
```

The wrapper needs `gradle/wrapper/gradle-wrapper.jar`. If it is missing, run
`gradle wrapper --gradle-version <version>` or open the project in Android Studio.

The Android SDK location must come from `ANDROID_HOME`, `ANDROID_SDK_ROOT`, or
`local.properties`. `local.properties` is machine-specific and must stay
gitignored.

## 7. Release builds

The release build type runs R8 with `proguard-android-optimize.txt` plus
`app/proguard-rules.pro`. No signing config is generated. Add one, keep the
keystore and its credentials out of version control, and verify a minified release
build before shipping — R8 problems do not show up in debug builds.