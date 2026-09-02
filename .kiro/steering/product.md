---
inclusion: always
---

# Product Overview

## Purpose

The **power-android-project-initial-setup** is a Kiro Power that automates the scaffolding of production-ready Android projects from scratch. It serves two primary functions:

1. **Bootstrap new Android projects** — Interviews developers about their app requirements and generates a complete, buildable project with modern Android architecture
2. **Add features to existing projects** — Helps extend MVVM or Clean Architecture projects with new screens/features using consistent, copy-adaptable templates

## Target Users

- Android developers starting new projects who want a production-ready foundation
- Teams adopting modern Android architecture (MVVM or Clean Architecture)
- Developers working with Jetpack Compose, Hilt, and offline-first patterns
- Projects requiring consistent code patterns and module boundaries

## Key Value Propositions

### Time Savings
- Eliminates hours of boilerplate setup
- Pre-configured build system with convention plugins (for Clean Architecture)
- Includes version catalog with tested, compatible dependencies

### Architecture Flexibility
Two scaffolding options to match project scale:
- **MVVM** — Single module, ideal for small projects and prototypes
- **Clean Architecture + MVVM** — 10-12 modules with domain layer, best for large or long-lived projects

### Production-Ready Foundation
- Jetpack Compose with Material 3
- Hilt dependency injection
- Offline-first Room data layer
- Retrofit networking with kotlinx.serialization
- Preferences DataStore for user settings
- Unidirectional data flow
- First feature wired end-to-end as reference implementation

### Consistency Maintenance
- Generates `.kiro/steering/` files describing the project's own architecture
- Future Kiro sessions automatically follow the established patterns
- Copy-adaptable templates for adding new features

## Scope

### In Scope
- Initial project scaffolding for both architectures
- Feature addition to existing MVVM or Clean Architecture projects
- Build configuration with Gradle and convention plugins
- Template-based code generation for all layers (UI, domain, data)
- Architecture-specific steering files for consistency

### Out of Scope
- Migration of existing projects to new architecture
- Custom build script generation (uses instruction-driven approach)
- Binary assets like launcher icons (provides vector XML placeholders)
- CI/CD configuration (depends on provider)
- Machine-specific files like `local.properties`

## User Workflow

### New Project Creation
1. User requests "set up a new Android project"
2. Power interviews for: app name, package name, architecture choice, feature flags
3. Agent computes project tokens and creates file structure
4. Agent copies and substitutes templates per the chosen architecture
5. Agent verifies output (no leftover tokens, correct package structure)
6. User runs Gradle sync and builds the project

### Adding Features
1. User requests "add a [feature name] screen"
2. Agent identifies existing architecture from steering files or code structure
3. Agent applies per-layer templates for that architecture
4. Agent wires the feature into navigation and dependency injection
5. User tests the new feature

## Success Metrics

- **Buildability** — Generated project builds without errors on first Gradle sync
- **Completeness** — All architectural layers present and properly wired
- **Consistency** — Code follows established patterns with no leftover template tokens
- **Verification** — Package names match directory structure, domain layer (if Clean) stays framework-free

## Known Limitations

### Tradeoffs of Instruction-Driven Approach
- **No byte-for-byte determinism** — Two runs with same settings may differ slightly
- **No automated validation** — Relies on agent following instructions rather than enforced rules
- **No dry-run mode** — Files written directly; agent must confirm before overwriting
- **Manual Gradle wrapper** — `gradle-wrapper.jar` not generated; user must run `gradle wrapper` or open in Android Studio

### Environment Requirements
- Android SDK must be configured via `ANDROID_HOME`, `ANDROID_SDK_ROOT`, or `local.properties`
- First build downloads AGP, Kotlin, and Compose compiler (takes a few minutes)
- Requires Gradle 8.6, Java 17

## Dependencies and Versioning

Pre-configured versions (tested combination):
- AGP 8.2.2
- Gradle 8.6
- Kotlin 1.9.22
- Compose Compiler 1.5.10
- Compose BOM 2024.02.00
- Hilt 2.50
- Room 2.6.1
- Target/Compile SDK 34
- Minimum SDK 24 (default)

**Critical:** Kotlin and Compose Compiler are a matched pair. Follow the [Compose to Kotlin compatibility table](https://developer.android.com/jetpack/androidx/releases/compose-kotlin) when updating.
