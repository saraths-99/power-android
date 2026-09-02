---
inclusion: always
---

# Power Overview

## What This Power Does

The **power-android-project-initial-setup** automates the creation of production-ready Android applications following modern architecture patterns. It eliminates the manual setup burden and ensures consistency from the start.

## Two Main Functions

### 1. Bootstrap New Android Projects
Interviews you about your app (name, package, architecture choice, required features) and generates a complete, buildable project in minutes instead of hours.

**You get:**
- Complete build configuration with Gradle and version catalog
- Material 3 UI with Jetpack Compose
- Hilt dependency injection wired throughout
- Offline-first Room database (optional)
- Retrofit networking (optional)
- DataStore preferences (optional)
- A working feature screen as reference implementation
- Architecture-specific steering files for consistency

### 2. Add Features to Existing Projects
Helps you extend MVVM or Clean Architecture Android projects with new screens/features using consistent, copy-adaptable per-layer templates.

**Works with:**
- Projects created by this power
- Existing projects following MVVM or Clean Architecture patterns
- Uses reference templates from `single-module-mvvm-reference.md` or `clean-mvvm-reference.md`

## Architecture Choices

### MVVM (Single Module)
**Best for:** Small projects, prototypes, MVPs, solo developers

**Structure:** Everything in the `app` module
- UI layer (Compose, ViewModels, Navigation)
- Data layer (Repositories, Room, Retrofit, DataStore)
- No domain layer

**Pros:** Simple, fast to navigate, minimal build configuration
**Cons:** Harder to scale, tighter coupling as project grows

### Clean Architecture + MVVM (Multi-Module)
**Best for:** Large apps, long-lived projects, team development

**Structure:** 10-12 modules with clear boundaries
- Feature modules for UI
- Core modules (domain, data, database, network, ui, common)
- Convention plugins in `build-logic/`
- Pure Kotlin domain layer

**Pros:** Clear separation of concerns, testable, scales well, parallel builds
**Cons:** More complex setup, longer initial build times, navigation complexity

See `references/architecture-selection.md` for detailed comparison.

## How It Works

### Instruction-Driven Scaffolding
Unlike traditional generator scripts, this power uses **instructions** that guide the agent through scaffolding. The agent:
1. Reads `SKILL.md` for the workflow
2. Interviews you for project settings
3. Computes tokens from your inputs (using `token-map.md`)
4. Maps templates to destinations (using `file-manifest.md`)
5. Copies templates and performs token substitution
6. Verifies the output

### Why No Generator Script?
Templates are **real source files** (Kotlin, Gradle, XML) with `{{TOKEN}}` placeholders, not strings buried in a script. This means:
- You can read, edit, and lint templates as actual code
- Diffs show real language changes
- Syntax highlighting works in your editor
- Templates are the documentation

**Tradeoff:** The agent performs validation by instruction rather than enforced code checks. Always review the output.

## Key Technologies

All generated projects use:
- **Kotlin 1.9.22** with Coroutines and Flow
- **Jetpack Compose** with Material 3 for UI
- **Hilt 2.50** for dependency injection
- **Room 2.6.1** for local database (optional)
- **Retrofit** with kotlinx.serialization for networking (optional)
- **DataStore** for user preferences (optional)
- **Gradle 8.6** with version catalog
- **AGP 8.2.2** targeting Android 14 (SDK 34)

## What Gets Generated

### Project Files
- Build system (Gradle, version catalog, settings)
- Convention plugins (Clean Architecture only)
- Application class with Hilt
- MainActivity with Compose setup
- Material 3 theme
- First feature screen (fully wired)
- `.gitignore` with Android-specific entries
- Project README

### Steering Files
Each generated project gets its own `.kiro/steering/` directory with:
- `code-patterns.md` — Coding conventions and patterns
- `module-architecture-*.md` — Module structure for chosen architecture
- `build-conventions-*.md` — Gradle and build setup

These ensure future Kiro sessions maintain consistency with the scaffolded structure.

### Data Layer Components (Based on Flags)
- **Database:** Room database, DAOs, entities, type converters
- **Network:** Retrofit service, DTOs, remote data sources
- **Preferences:** DataStore with type-safe accessors
- **Repositories:** Interface + implementation with offline-first pattern

## Typical Workflow

### Creating a New Project
```
You: "Set up a new Android project"
Agent: Activates power, starts interview
You: Provide app name, package, choose architecture, select features
Agent: Generates complete project structure
You: Open in Android Studio, sync Gradle, build
Result: Working app with sample feature in 5-10 minutes
```

### Adding a Feature
```
You: "Add a profile screen to my app"
Agent: Identifies architecture from steering files
Agent: Applies per-layer templates (Screen, ViewModel, Repository, etc.)
Agent: Wires navigation and dependency injection
You: Test the new feature
Result: Consistent implementation matching existing patterns
```

## Requirements

### Before Using This Power
- **Android SDK** installed and configured
- **Environment variable** `ANDROID_HOME` or `ANDROID_SDK_ROOT` set
  - OR `local.properties` file with `sdk.dir=/path/to/android/sdk`
- **Java 17** JDK
- **Kiro IDE** with this power installed

### First Build Expectations
- Downloads Gradle wrapper (if needed)
- Downloads AGP, Kotlin compiler, Compose compiler
- Syncs dependencies from Maven Central
- **Takes 2-5 minutes** — this is normal

### Common Setup Issues
- **"SDK location not found"** → Set `ANDROID_HOME` or create `local.properties`
- **Kotlin version mismatch** → Ensure Kotlin 1.9.22 matches Compose Compiler 1.5.10
- **Gradle daemon timeout** → First sync is slow, be patient

## What This Power Does NOT Do

- **Migrate existing projects** to new architecture
- **Generate launcher icons** — provides vector XML placeholder only
- **Create `local.properties`** — machine-specific, you create it manually
- **Configure CI/CD** — depends on your provider
- **Add extra libraries** beyond the core stack (Coil, Timber, etc.)
- **Guarantee byte-for-byte reproducibility** — instruction-driven, may vary slightly

## File Organization

All power contents live in this repository:

```
power-android-project-initial-setup/
├── skills/create-android-project/
│   ├── SKILL.md                    # Agent workflow
│   ├── assets/
│   │   ├── steering/               # Steering templates
│   │   └── templates/              # Kotlin/Gradle/XML templates
│   └── references/                 # Agent documentation
├── .kiro/steering/                 # Power's own steering files
└── plugin.json                     # Power manifest
```

## Getting Help

### During Project Creation
The agent follows `SKILL.md` step by step. If scaffolding seems stuck or produces errors:
1. Check that interview questions were answered completely
2. Verify package name is valid (no reserved words, proper format)
3. Confirm architecture choice is clear (`mvvm` or `clean-mvvm`)
4. Let the agent finish before opening in IDE

### After Project Creation
1. **Build fails?** Check Android SDK is configured and `ANDROID_HOME` is set
2. **Leftover `{{TOKEN}}`?** Report to power maintainer — token substitution missed something
3. **Package structure wrong?** Verify `SKILL.md` Step 7 verification ran
4. **Want to add a feature?** Request "add a [name] screen" and agent will use reference templates

### Common Questions
- **Can I change versions?** Yes, edit `gradle/libs.versions.toml` but maintain Kotlin ↔ Compose Compiler compatibility
- **Can I add more modules?** Yes, follow module patterns in `module-architecture-*.md` steering file
- **Can I switch architectures?** Not easily — better to scaffold a new project
- **What if I need a library not included?** Add it to version catalog and use convention plugins (Clean) or direct dependency (MVVM)

## Customizing the Power

### Editing Templates
All templates are real files in `skills/create-android-project/assets/templates/`. To change generated code:
1. Edit the template file (it's actual Kotlin/Gradle/XML)
2. Use `{{TOKEN}}` for values that vary per project
3. Check `references/token-map.md` for token definitions
4. Update `references/file-manifest.md` if adding new templates

### Adjusting Default Values
Defaults are in `SKILL.md`:
- `minSdk`: 24
- `compileSdk` / `targetSdk`: 34
- `gradleVersion`: 8.6
- `initialFeature`: "home"
- All feature flags default to `true`

### Adding New Architecture Patterns
Would require:
1. New architecture-specific templates in `assets/templates/`
2. New steering files in `assets/steering/`
3. Updates to `token-map.md`, `file-manifest.md`, `project-structure.md`
4. Modifications to `SKILL.md` interview and workflow

## Version Information

**Current Power Version:** 1.0.0
**Author:** Sarath Satheesh
**Tested Dependency Versions:** See `tech.md` for complete version matrix
**Last Updated:** 2026
