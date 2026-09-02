---
inclusion: always
---

# Technology Stack

## Language and Platform

### Kotlin
- **Version:** 1.9.22
- Primary language for all source code
- Kotlin Gradle DSL for build scripts
- kotlinx.serialization for JSON parsing

### Android
- **Minimum SDK:** 24 (Android 7.0)
- **Target SDK:** 34 (Android 14)
- **Compile SDK:** 34
- **Java Version:** 17

## Build System

### Gradle
- **Gradle Version:** 8.6
- **AGP Version:** 8.2.2
- Version catalog in `gradle/libs.versions.toml` for centralized dependency management
- Convention plugins for Clean Architecture projects (in `build-logic/`)

### Convention Plugins (Clean Architecture Only)
Located in `build-logic/convention/src/main/kotlin/`:
- `AndroidApplicationConventionPlugin` — App module configuration
- `AndroidApplicationComposeConventionPlugin` — Compose setup for app
- `AndroidLibraryConventionPlugin` — Library module configuration
- `AndroidLibraryComposeConventionPlugin` — Compose setup for libraries
- `AndroidFeatureConventionPlugin` — Feature module conventions
- `AndroidRoomConventionPlugin` — Room database configuration
- `HiltConventionPlugin` — Hilt dependency injection setup
- `JvmLibraryConventionPlugin` — Pure Kotlin modules (domain layer)

## UI Framework

### Jetpack Compose
- **Compose BOM:** 2024.02.00
- **Compose Compiler:** 1.5.10
- Declarative UI with Material 3
- `collectAsStateWithLifecycle()` for state collection
- Stateless/stateful composable split pattern
- Navigation Compose for screen routing

**Critical Dependency:** Kotlin and Compose Compiler versions are tightly coupled. See [Compose to Kotlin Compatibility Table](https://developer.android.com/jetpack/androidx/releases/compose-kotlin).

### Material Design 3
- Material 3 theming and components
- Dynamic color support
- Theme defined in `ui/theme/` directory

## Architecture Patterns

### Two Architecture Options

#### MVVM (Single Module)
- **Structure:** Single `app` module
- **Pattern:** UI → ViewModel → Repository → Data Sources
- **Best for:** Small projects, prototypes, MVPs
- **No domain layer**

#### Clean Architecture + MVVM (Multi-Module)
- **Structure:** 10-12 modules
- **Pattern:** UI → ViewModel → Use Cases → Repository → Data Sources
- **Domain layer:** Pure Kotlin in separate module
- **Best for:** Large, long-lived projects
- **Convention plugins:** Yes

### Common Patterns (Both Architectures)
- Unidirectional data flow
- Offline-first approach
- Repository pattern
- Dependency injection with Hilt
- StateFlow for reactive state management
- Sealed interfaces for UI state

## Dependency Injection

### Hilt
- **Version:** 2.50
- Constructor injection for all injectable types
- `@HiltViewModel` for ViewModels
- `@InstallIn(SingletonComponent::class)` for app-scoped dependencies
- `@Binds` for interface-to-implementation binding
- `@Provides` for constructed types
- DI modules in `di/` package

## Data Layer

### Local Storage — Room
- **Version:** 2.6.1
- Source of truth for offline-first architecture
- Kotlin Coroutines support with Flow
- Type converters for complex types
- Database defined in `data/local/` or `core/database/` module

**Components:**
- `*Entity` — Database tables
- `*Dao` — Data access objects with suspend functions and Flow
- `*Database` — Room database definition

### Network — Retrofit
- Retrofit 2 with kotlinx.serialization converter
- OkHttp for HTTP client
- Network data sources in `data/remote/` or `core/network/` module
- DTOs (Data Transfer Objects) for API models
- `*RemoteDataSource` interfaces

### User Preferences — DataStore
- Preferences DataStore for key-value settings
- Type-safe access via extension properties
- Flow-based observation
- Located in `data/preferences/` or `core/datastore/` module

## Concurrency

### Kotlin Coroutines
- `viewModelScope` for ViewModel coroutines
- `Flow` for reactive streams
- `StateFlow` for state management
- `suspend` functions for asynchronous operations

### Dispatcher Injection
- **Never reference `Dispatchers.IO` directly**
- Inject via custom `@Dispatcher` qualifier
- Allows test dispatcher substitution
- Defined in `core/common/` or shared location

## Testing

### Frameworks
- JUnit 4 for unit tests
- Turbine for Flow testing
- `MainDispatcherRule` for ViewModel tests
- Hand-written test doubles (no mocking libraries)

### Philosophy
- Test doubles implement real interfaces (fail-fast on changes)
- Shared test utilities in `core/testing/` module
- Unit tests in `src/test/`
- Instrumented tests in `src/androidTest/` (critical flows only)
- Test stateless Screen composables, not Routes

## Code Generation

### KSP (Kotlin Symbol Processing)
Used by:
- Hilt for dependency injection
- Room for DAO implementation
- Any annotation processors

## File Formats

### Configuration
- **Gradle:** Kotlin DSL (`.gradle.kts`)
- **Version Catalog:** TOML (`libs.versions.toml`)
- **Properties:** Standard Java properties format

### Resources
- **Strings:** XML (`strings.xml`)
- **Layouts:** Compose (Kotlin) — no XML layouts
- **Icons:** Vector XML drawables

## Version Compatibility Matrix

| Component | Version | Notes |
|---|---|---|
| Gradle | 8.6 | Required for AGP 8.2.2 |
| AGP | 8.2.2 | Android Gradle Plugin |
| Kotlin | 1.9.22 | Matched with Compose Compiler |
| Compose Compiler | 1.5.10 | Must match Kotlin version |
| Compose BOM | 2024.02.00 | All Compose dependencies |
| Hilt | 2.50 | DI framework |
| Room | 2.6.1 | Local database |
| Java Toolchain | 17 | Required by AGP 8.x |

## Dependencies Not Included

The power does **not** include:
- Image loading libraries (Coil, Glide)
- Logging libraries (Timber)
- Crash reporting (Firebase Crashlytics)
- Analytics
- Feature flags
- Performance monitoring
- Additional network libraries beyond Retrofit

Add these based on project needs after scaffolding.

## Build Configuration

### ProGuard/R8
- Enabled by default in release builds (`minifyRelease` flag)
- ProGuard rules in `proguard-rules.pro`
- Consumer ProGuard rules in libraries when needed

### Build Types
- **Debug:** No minification, debuggable
- **Release:** Minified, optimized, ready for distribution

### APK Outputs
- Generated in `app/build/outputs/apk/`
- Unsigned release APK requires signing configuration

## Environment Setup Requirements

### Developer Machine
- Android Studio (latest stable)
- Android SDK via Android Studio or standalone
- Java 17 JDK
- `ANDROID_HOME` or `ANDROID_SDK_ROOT` environment variable set
- **OR** `local.properties` with `sdk.dir` pointing to Android SDK

### First Build
- Downloads Gradle wrapper (if not present)
- Downloads AGP, Kotlin compiler, Compose compiler
- Syncs dependencies from Maven Central and Google Maven
- Typical first build: 2-5 minutes

### CI/CD Requirements
- Same environment variables as local
- Gradle wrapper checked into repository
- Dependencies cached for faster builds
- Release signing keys managed securely
