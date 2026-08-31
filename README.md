# Android Project - Initial Setup

This is a power that scaffolds a new Android project
from scratch. It interviews you for the basics of your app, then generates a
complete, buildable project in one of two selectable architectures.

Author: Sarath Satheesh

## Two architectures

| | `mvvm` | `clean-mvvm` |
|---|---|---|
| Layout | single module | 10 to 12 modules |
| Domain layer | none | `domain/` (pure Kotlin) |
| ViewModel depends on | repository | use cases |
| Convention plugins | no | yes, in `build-logic/` |
| Best for | small projects, prototypes | large or long-lived projects |

Shared by both: Jetpack Compose with Material 3, Hilt, an offline-first Room data
layer, Retrofit with kotlinx.serialization, Preferences DataStore, a version
catalog, unidirectional data flow, and a first feature wired end to end.

Every generated project also gets a `.kiro/steering/` directory describing its own
module boundaries, build conventions and code patterns, rendered for the
architecture it was scaffolded with. That keeps later Kiro sessions in the project
consistent with how it was set up.

## Install

1. Open Kiro, go to the Powers panel and choose **Add Custom Power**.
2. Choose **Import power from a folder** and select this directory.
3. Mention Android work in chat to activate it, for example:
   *"set up a new Android project"*.

To share it, push the directory to a public GitHub repository and install with
**Add Custom Power** > **Import power from GitHub**.

## Contents

```
plugin.json                                   Agent Plugins manifest
skills/create-android-project/
├── SKILL.md                                  Interview and scaffolding workflow
├── scripts/
│   ├── scaffold_android_project.py           Orchestration: config, validation, assembly
│   └── init_gradle_wrapper.sh                Gradle wrapper helper
├── assets/
│   ├── steering/                              Steering emitted into each new project
│   │   ├── module-architecture-mvvm.md
│   │   ├── module-architecture-clean-mvvm.md
│   │   ├── build-conventions-mvvm.md
│   │   ├── build-conventions-clean-mvvm.md
│   │   └── code-patterns.md                  Shared, with architecture-aware sections
│   └── templates/                             Kotlin/Gradle/XML/Markdown source, as real files
│       ├── root/                              settings.gradle.kts, version catalog, gitignore, etc.
│       ├── build-logic/                       build-logic/ settings and root build file
│       ├── convention-sources/                 One .kt file per convention plugin
│       ├── app-build/                          app/build.gradle.kts, per architecture
│       ├── kotlin/                             Application/domain/data/UI source templates
│       └── readme/                             The two generated project READMEs
└── references/
    ├── architecture-selection.md             Choosing between the two architectures
    ├── project-interview.md                  Interview wording and follow-ups
    ├── post-setup.md                         What to do after scaffolding
    ├── modularization.md                     Module boundaries and dependency rules
    ├── architecture.md                       UI / domain / data layer patterns
    ├── compose-patterns.md                   Compose conventions
    ├── gradle-setup.md                       Gradle and convention plugin details
    └── testing.md                            Testing approach

skills/single-module-mvvm-reference/
└── SKILL.md                                  Copy-adaptable per-layer MVVM templates
```

## Two skills

| Skill | Use when |
|---|---|
| `create-android-project` | Bootstrapping a brand-new Android project from scratch (interview + full scaffold, `mvvm` or `clean-mvvm`). |
| `single-module-mvvm-reference` | Adding an MVVM feature/screen to an existing single-module app, or you just need the per-layer code templates (model, repository, UiState, ViewModel, Compose route/content) without running the scaffolder. |

`scaffold_android_project.py` holds only orchestration: config validation,
package-layout resolution, `{{TOKEN}}` substitution, and file assembly. Every
piece of generated-language source — Kotlin, Gradle Kotlin DSL, XML, TOML,
Markdown — lives as a real file under `assets/templates/`, loaded at runtime via
`_load_template()`. This keeps the script itself short and keeps each template
readable, lintable, and diffable as the language it actually is, rather than as
an escaped Python string. The split is a pure refactor: given the same config,
the generated project is byte-for-byte identical to what the all-in-one script
produced.

## Using the generator directly

The skill drives this for you, but it also works standalone.

```bash
cd skills/create-android-project

# See every option, with the architecture pre-filled
python3 scripts/scaffold_android_project.py --print-config-template --architecture clean-mvvm
python3 scripts/scaffold_android_project.py --print-config-template --architecture mvvm

# Preview without writing
python3 scripts/scaffold_android_project.py --config my-app.json --output-dir ~/projects --dry-run

# Generate
python3 scripts/scaffold_android_project.py --config my-app.json --output-dir ~/projects
```

`architecture`, `appName` and `packageName` must be set explicitly. Everything
else has a default. Unknown keys are rejected rather than ignored.

### Editing the generated output

To change what a generated file looks like, edit the matching file under
`assets/templates/` — not the Python script. For example, to change the app
module's `build.gradle.kts` for the `mvvm` architecture, edit
`assets/templates/app-build/T_APP_BUILD_MVVM.gradle.kts` directly; it is real
Gradle Kotlin DSL with `{{TOKEN}}` placeholders, not a Python string. The script
only decides *which* templates get used and *what* the tokens resolve to.

### Config keys

| Key | Default | Notes |
|---|---|---|
| `architecture` | — | `mvvm` or `clean-mvvm`. Required. |
| `appName` | — | Display name. Required. Drives the class prefix. |
| `packageName` | — | applicationId and root package. Required. |
| `projectDirName` | kebab-case app name | Folder created under `--output-dir`. |
| `rootProjectName` | PascalCase app name | `rootProject.name`, and the convention plugin prefix. |
| `initialFeature` | `home` | One lowercase word. |
| `minSdk` | `24` | 21 or higher. |
| `compileSdk` / `targetSdk` | `34` | |
| `includeDatabase` | `true` | Room. Off gives an in-memory repository. |
| `includeNetwork` | `true` | Retrofit. Requires `includeDatabase`. |
| `includeDatastore` | `true` | Preferences DataStore, plus theme settings wiring. |
| `includeTestUtilities` | `true` | Test helpers, not test cases. |
| `minifyRelease` | `true` | R8 on the release build. |
| `gradleVersion` | `8.6` | Written to the wrapper properties. |

Requires Python 3.8 or newer. No third-party Python packages.

## The Gradle wrapper

`gradle-wrapper.jar` is a binary, so it cannot be generated as text. The
scaffolder writes `gradle/wrapper/gradle-wrapper.properties` and leaves the rest
to you:

```bash
skills/create-android-project/scripts/init_gradle_wrapper.sh <project-dir>
```

The helper uses a local `gradle` install. If there is not one it stops and lists
the options rather than downloading a JAR on its own. Opening the project in
Android Studio also creates the wrapper.

## Generated dependency versions

Set in `gradle/libs.versions.toml` as a matched, tested combination:

AGP 8.2.2, Gradle 8.6, Kotlin 1.9.22, Compose compiler 1.5.10, Compose BOM
2024.02.00, Hilt 2.50, Room 2.6.1, Java 17.

Kotlin and the Compose compiler are a matched pair. Bumping one without the other
breaks the build; the mapping is in the
[Compose to Kotlin compatibility table](https://developer.android.com/jetpack/androidx/releases/compose-kotlin).

## Activation keywords

The power loads when a conversation mentions any of its `keywords`, which cover
`android`, `new android app`, `android setup`, `scaffold`, `jetpack compose`,
`hilt`, `room`, `mvvm`, `clean architecture`, `multi-module` and related terms.
Adjust the list in `plugin.json` if it activates too eagerly or not often enough.

## Note on `plugin.json`

The manifest needs a `$schema` key as its first entry:

```json
"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
```

It's already set in this power's `plugin.json`. Preserve it if you regenerate or
edit the file, since some write tools refuse to insert a remote schema reference
directly and it has to be added with a scripted edit instead.
