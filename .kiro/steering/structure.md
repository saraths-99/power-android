---
inclusion: always
---

# Project Structure

## Power Layout

This is a Kiro Power for scaffolding Android projects. The power itself follows this structure:

```
power-android-project-initial-setup/
├── plugin.json                          # Power manifest with metadata and keywords
├── README.md                            # Power documentation
├── .kiro/
│   └── steering/                        # Steering files for the power itself
│       ├── product.md
│       ├── tech.md
│       └── structure.md
└── skills/
    └── create-android-project/          # Single skill handling both jobs
        ├── SKILL.md                     # Main workflow instructions for the agent
        ├── assets/
        │   ├── steering/                # Steering templates for generated projects
        │   │   ├── module-architecture-mvvm.md
        │   │   ├── module-architecture-clean-mvvm.md
        │   │   ├── build-conventions-mvvm.md
        │   │   ├── build-conventions-clean-mvvm.md
        │   │   └── code-patterns.md     # Shared, with architecture-aware sections
        │   └── templates/               # Source templates (real Kotlin/Gradle/XML files)
        │       ├── root/                # Project root files
        │       ├── build-logic/         # Convention plugin build config
        │       ├── convention-sources/  # Convention plugin implementations
        │       ├── app-build/           # app/build.gradle.kts per architecture
        │       ├── kotlin/              # Kotlin source templates
        │       └── readme/              # Generated project README templates
        └── references/                  # Agent reference documentation
            ├── architecture-selection.md
            ├── token-map.md            # Token computation and substitution rules
            ├── file-manifest.md        # Template → destination mappings
            ├── project-structure.md    # Module graphs and package layouts
            ├── project-interview.md    # Interview questions and flow
            ├── post-setup.md           # Post-scaffolding tasks
            ├── modularization.md       # Module boundaries and dependencies
            ├── architecture.md         # Layer patterns and responsibilities
            ├── compose-patterns.md     # Compose conventions
            ├── gradle-setup.md         # Build system details
            ├── testing.md              # Testing approach
            ├── single-module-mvvm-reference.md      # MVVM feature templates
            └── clean-mvvm-reference.md              # Clean Architecture feature templates
```

## Key Directories

### `/skills/create-android-project/`
Contains the single skill that handles both bootstrapping new projects and adding features to existing ones.

**SKILL.md**: The main instruction file that guides the agent through:
- Interviewing the user for project settings
- Computing tokens from user inputs
- Mapping templates to destination files
- Performing token substitution
- Verifying the output

### `/assets/steering/`
Template steering files that are **copied into generated Android projects**. Each generated project gets its own `.kiro/steering/` directory with:
- Architecture-specific module boundaries
- Build conventions for that architecture
- Code patterns and naming conventions

These ensure future Kiro sessions in the generated project remain consistent with how it was scaffolded.

### `/assets/templates/`
Real source files used as templates. Each file contains `{{TOKEN}}` placeholders that get substituted during scaffolding.

**Why real files?** So templates are:
- Syntax-highlighted in the editor
- Lintable and type-checkable
- Diffable as the language they represent
- Not buried in strings inside a generator script

**Subdirectories:**
- `root/` — `settings.gradle.kts`, version catalog, `.gitignore`, etc.
- `build-logic/` — Build-logic module configuration (Clean Architecture only)
- `convention-sources/` — Convention plugin implementations (Clean Architecture only)
- `app-build/` — `app/build.gradle.kts` variants per architecture
- `kotlin/` — Application class, ViewModels, repositories, UI, entities, DAOs, etc.
- `readme/` — Generated project README templates

### `/references/`
Documentation the agent consults during scaffolding:

| File | Purpose |
|---|---|
| `token-map.md` | How to compute every `{{TOKEN}}` from user inputs |
| `file-manifest.md` | Which template file maps to which destination path |
| `project-structure.md` | Module graphs and package layouts per architecture |
| `project-interview.md` | Interview questions and validation rules |
| `post-setup.md` | What to do after scaffolding (build, verify, add features) |
| `architecture-selection.md` | Guidance on choosing MVVM vs Clean Architecture |
| `modularization.md` | Module boundaries and dependency rules |
| `architecture.md` | Layer responsibilities and data flow |
| `compose-patterns.md` | Compose UI conventions |
| `gradle-setup.md` | Build system and convention plugin details |
| `testing.md` | Testing philosophy and tools |
| `single-module-mvvm-reference.md` | Copy-adaptable templates for adding features to MVVM projects |
| `clean-mvvm-reference.md` | Copy-adaptable templates for adding features to Clean projects |

## Generated Project Structures

### MVVM Architecture (Single Module)

```
<project-name>/
├── app/
│   ├── src/
│   │   └── main/
│   │       ├── kotlin/
│   │       │   └── <package>/
│   │       │       ├── <AppName>Application.kt
│   │       │       ├── MainActivity.kt
│   │       │       ├── ui/
│   │       │       │   ├── theme/
│   │       │       │   └── <feature>/
│   │       │       │       ├── <Feature>Screen.kt
│   │       │       │       ├── <Feature>UiState.kt
│   │       │       │       ├── <Feature>ViewModel.kt
│   │       │       │       └── navigation/
│   │       │       │           └── <Feature>Navigation.kt
│   │       │       ├── data/
│   │       │       │   ├── repository/
│   │       │       │   │   ├── <Thing>Repository.kt (interface)
│   │       │       │   │   └── <Thing>RepositoryImpl.kt
│   │       │       │   ├── local/      # If includeDatabase
│   │       │       │   │   ├── <Thing>Dao.kt
│   │       │       │   │   ├── <Thing>Entity.kt
│   │       │       │   │   ├── <AppName>Database.kt
│   │       │       │   │   └── di/
│   │       │       │   ├── remote/     # If includeNetwork
│   │       │       │   │   ├── <Thing>RemoteDataSource.kt
│   │       │       │   │   ├── <Thing>Dto.kt
│   │       │       │   │   └── di/
│   │       │       │   └── preferences/  # If includeDatastore
│   │       │       │       ├── UserPreferences.kt
│   │       │       │       └── di/
│   │       │       └── core/
│   │       │           └── common/
│   │       │               ├── Dispatchers.kt
│   │       │               └── di/
│   │       └── res/
│   │           └── values/
│   │               └── strings.xml
│   ├── build.gradle.kts
│   └── proguard-rules.pro
├── gradle/
│   ├── libs.versions.toml
│   └── wrapper/
│       └── gradle-wrapper.properties
├── settings.gradle.kts
├── .gitignore
├── .kiro/
│   └── steering/
│       ├── module-architecture-mvvm.md
│       ├── build-conventions-mvvm.md
│       └── code-patterns.md
└── README.md
```

**Package Structure:**
- `ui/` — Composables, screens, ViewModels, theme, navigation
- `data/` — Repositories, data sources (local/remote/preferences), entities, DTOs
- `core/common/` — Dispatchers and shared utilities

### Clean Architecture + MVVM (Multi-Module)

```
<project-name>/
├── app/
│   ├── src/main/kotlin/<package>/
│   │   ├── <AppName>Application.kt
│   │   ├── MainActivity.kt
│   │   └── navigation/
│   │       └── <AppName>NavHost.kt
│   └── build.gradle.kts
├── feature/
│   └── <feature>/
│       ├── src/main/kotlin/<package>/feature/<feature>/
│       │   ├── <Feature>Screen.kt
│       │   ├── <Feature>UiState.kt
│       │   ├── <Feature>ViewModel.kt
│       │   └── navigation/
│       │       └── <Feature>Navigation.kt
│       ├── src/main/res/values/
│       │   └── strings.xml
│       └── build.gradle.kts
├── core/
│   ├── ui/
│   │   ├── src/main/kotlin/<package>/core/ui/
│   │   │   ├── theme/
│   │   │   └── components/
│   │   └── build.gradle.kts
│   ├── domain/                          # Pure Kotlin, no Android
│   │   ├── src/main/kotlin/<package>/core/domain/
│   │   │   ├── model/
│   │   │   │   └── <Thing>.kt
│   │   │   ├── repository/
│   │   │   │   └── <Thing>Repository.kt
│   │   │   └── usecase/
│   │   │       └── Get<Thing>UseCase.kt
│   │   └── build.gradle.kts             # JVM library, not Android
│   ├── data/
│   │   ├── src/main/kotlin/<package>/core/data/
│   │   │   ├── repository/
│   │   │   │   └── <Thing>RepositoryImpl.kt
│   │   │   ├── mapper/
│   │   │   └── di/
│   │   └── build.gradle.kts
│   ├── database/                        # If includeDatabase
│   │   ├── src/main/kotlin/<package>/core/database/
│   │   │   ├── <Thing>Dao.kt
│   │   │   ├── <Thing>Entity.kt
│   │   │   ├── <AppName>Database.kt
│   │   │   └── di/
│   │   └── build.gradle.kts
│   ├── network/                         # If includeNetwork
│   │   ├── src/main/kotlin/<package>/core/network/
│   │   │   ├── <Thing>RemoteDataSource.kt
│   │   │   ├── <Thing>Dto.kt
│   │   │   └── di/
│   │   └── build.gradle.kts
│   ├── datastore/                       # If includeDatastore
│   │   ├── src/main/kotlin/<package>/core/datastore/
│   │   │   ├── UserPreferences.kt
│   │   │   └── di/
│   │   └── build.gradle.kts
│   ├── common/
│   │   ├── src/main/kotlin/<package>/core/common/
│   │   │   ├── Dispatchers.kt
│   │   │   └── di/
│   │   └── build.gradle.kts
│   └── testing/                         # If includeTestUtilities
│       ├── src/main/kotlin/<package>/core/testing/
│       │   ├── repository/
│       │   │   └── Test<Thing>Repository.kt
│       │   └── rules/
│       └── build.gradle.kts
├── build-logic/
│   ├── convention/
│   │   ├── src/main/kotlin/
│   │   │   ├── AndroidApplicationConventionPlugin.kt
│   │   │   ├── AndroidApplicationComposeConventionPlugin.kt
│   │   │   ├── AndroidLibraryConventionPlugin.kt
│   │   │   ├── AndroidLibraryComposeConventionPlugin.kt
│   │   │   ├── AndroidFeatureConventionPlugin.kt
│   │   │   ├── AndroidRoomConventionPlugin.kt
│   │   │   ├── HiltConventionPlugin.kt
│   │   │   ├── JvmLibraryConventionPlugin.kt
│   │   │   ├── ComposeConfig.kt
│   │   │   ├── KotlinConfig.kt
│   │   │   └── ProjectExtensions.kt
│   │   └── build.gradle.kts
│   └── settings.gradle.kts
├── gradle/
│   ├── libs.versions.toml
│   └── wrapper/
│       └── gradle-wrapper.properties
├── settings.gradle.kts
├── .gitignore
├── .kiro/
│   └── steering/
│       ├── module-architecture-clean-mvvm.md
│       ├── build-conventions-clean-mvvm.md
│       └── code-patterns.md
└── README.md
```

**Module Dependencies (Clean Architecture):**
```
app → feature/* → core/ui, core/domain
feature/* → core/ui, core/domain
core/data → core/domain, core/database, core/network, core/datastore, core/common
core/database → core/common
core/network → core/common
core/datastore → core/common
core/domain → (pure Kotlin, no dependencies)
core/ui → core/domain
core/testing → all core modules (test utilities)
```

**Critical Rule:** `core/domain/` must remain **pure Kotlin** with zero Android framework dependencies. It uses `build.gradle.kts` with `kotlin("jvm")` plugin, not Android library plugin.

## Module Boundaries

### Feature Modules
- Depend on `core/ui` and `core/domain` only
- Contain UI (Screen, ViewModel, Navigation) for one feature
- Own their strings in `res/values/strings.xml`
- Prefix strings with feature name to avoid collisions
- Internal visibility for most types

### Core Modules

#### `core/domain` (Clean Architecture only)
- **Pure Kotlin** — No Android dependencies
- Domain models, repository interfaces, use cases
- Business logic only
- JVM library module

#### `core/data`
- Implements repository interfaces from `core/domain`
- Coordinates data sources (database, network, preferences)
- Contains mappers between layers
- Depends on core/database, core/network, core/datastore

#### `core/database`
- Room database, DAOs, entities
- Android library module
- Depends only on `core/common`

#### `core/network`
- Retrofit services, DTOs, remote data sources
- Android library module
- Depends only on `core/common`

#### `core/datastore`
- DataStore preferences
- Android library module
- Depends only on `core/common`

#### `core/common`
- Dispatcher qualifiers and DI
- Shared utilities
- No other dependencies

#### `core/ui`
- Material 3 theme
- Reusable composables
- Navigation utilities
- Depends on `core/domain` for models

#### `core/testing`
- Test doubles for repositories
- Test rules (MainDispatcherRule)
- Shared test utilities
- Depends on all core modules it provides doubles for

## Token Substitution

Templates use `{{TOKEN}}` placeholders that get replaced during scaffolding:

| Token | Example Value | Source |
|---|---|---|
| `{{PACKAGE_NAME}}` | `com.example.myapp` | User input |
| `{{APP_NAME}}` | `MyApp` | User input (PascalCase) |
| `{{PROJECT_NAME}}` | `my-app` | Computed (kebab-case) |
| `{{FEATURE}}` | `home` | User input or default |
| `{{MIN_SDK}}` | `24` | User input or default |
| `{{COMPILE_SDK}}` | `34` | User input or default |
| `{{GRADLE_VERSION}}` | `8.6` | Default |

Architecture-specific tokens in `code-patterns.md`:
- `{{VM_CONSTRUCTOR}}` — ViewModel constructor params (repository vs use cases)
- `{{VM_SOURCE}}` — Data source in ViewModel (repository call vs use case)
- `{{VM_DEPENDENCY_RULE}}` — What ViewModels depend on
- `{{USE_CASE_SECTION}}` — Use case documentation (Clean only)
- `{{REPO_INTERFACE_HOME}}` — Where repository interfaces live
- `{{REPO_BINDING_HOME}}` — Where repository bindings live
- `{{COMPONENT_HOME}}` — Where reusable components live
- `{{TEST_DOUBLE_HOME}}` — Where test doubles live

See `references/token-map.md` for complete computation rules.

## File Naming Conventions

### Kotlin Files
- `<Feature>Screen.kt` — Stateless screen composable
- `<Feature>Route.kt` — Stateful route composable (may be in same file as Screen)
- `<Feature>ViewModel.kt` — ViewModel
- `<Feature>UiState.kt` — UI state sealed interface (may be in ViewModel file)
- `<Feature>Navigation.kt` — Navigation extension
- `<Thing>Repository.kt` — Repository interface
- `<Thing>RepositoryImpl.kt` — Repository implementation
- `Get<Thing>UseCase.kt` — Use case (Clean Architecture)
- `<Thing>Entity.kt` — Room entity
- `<Thing>Dao.kt` — Room DAO
- `<Thing>Dto.kt` — Network DTO
- `<Thing>RemoteDataSource.kt` — Retrofit service

### Build Files
- `build.gradle.kts` — Module build file (Kotlin DSL)
- `settings.gradle.kts` — Project settings
- `libs.versions.toml` — Version catalog
- `proguard-rules.pro` — ProGuard configuration

### Resources
- `strings.xml` — String resources
- `ic_*.xml` — Vector icons
- No XML layouts (Compose-only)

## Steering Files in Generated Projects

Every generated project includes `.kiro/steering/` with documentation of its own architecture:

### Copied to All Projects
- `code-patterns.md` — Class-level patterns, with architecture-specific sections substituted

### MVVM Projects Get
- `module-architecture-mvvm.md` — Single-module structure and package layout
- `build-conventions-mvvm.md` — Gradle configuration for single-module setup

### Clean Architecture Projects Get
- `module-architecture-clean-mvvm.md` — Multi-module structure and dependency graph
- `build-conventions-clean-mvvm.md` — Convention plugins and Gradle setup

These files ensure future Kiro interactions in the generated project follow the same patterns used during scaffolding.
