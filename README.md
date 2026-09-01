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
├── SKILL.md                                  Interview + instruction-driven scaffolding workflow
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
    ├── token-map.md                          Token computation + substitution rules
    ├── file-manifest.md                      Which template goes where, per arch/flags
    ├── project-structure.md                  Per-architecture module/package layout + inclusion matrix
    ├── project-interview.md                  Interview wording and follow-ups
    ├── post-setup.md                         What to do after scaffolding, incl. adding a feature
    ├── modularization.md                     Module boundaries and dependency rules
    ├── architecture.md                       UI / domain / data layer patterns
    ├── compose-patterns.md                   Compose conventions
    ├── gradle-setup.md                       Gradle and convention plugin details
    ├── testing.md                            Testing approach
    ├── single-module-mvvm-reference.md       Copy-adaptable per-layer MVVM templates (adding a feature)
    └── clean-mvvm-reference.md               Copy-adaptable Clean Architecture + MVVM templates (adding a feature)
```

## Skills

This power is a single skill. `create-android-project` covers two jobs, described
in its own `SKILL.md`:

| Job | Use when |
|---|---|
| Bootstrap a new project | Starting a brand-new Android project from scratch (interview + full scaffold, `mvvm` or `clean-mvvm`). |
| Add a feature to an existing project | Adding a feature/screen to an app that already follows MVVM or Clean Architecture + MVVM — whether or not this skill scaffolded it. Uses the per-layer templates in `references/single-module-mvvm-reference.md` / `references/clean-mvvm-reference.md` plus the module/Gradle wiring in `references/post-setup.md`. |

There used to be two separate reference skills (`single-module-mvvm-reference`,
`clean-mvvm-reference`) for the second job. They were merged into
`create-android-project/references/` so the whole power is one skill with one
entry point, instead of relying on Claude picking the right one of three
similarly-described skills.

## How scaffolding works (no generator script)

There is no generator script. The skill is **instruction-driven**: the agent
follows `SKILL.md`, computes the project's tokens, and creates each file by
copying the matching template from `assets/templates/` and substituting its
`{{TOKEN}}` placeholders. Every piece of generated-language source — Kotlin,
Gradle Kotlin DSL, XML, TOML, Markdown — lives as a real file under
`assets/templates/`, readable and diffable as the language it actually is.

The agent works from three references:

- `references/token-map.md` — how to compute every token and the per-architecture
  package map, plus the conditional same-package import rules.
- `references/file-manifest.md` — which template maps to which destination, and
  which files each `include*` flag adds or drops.
- `references/project-structure.md` — the module graph and package layout.

### Settings the agent resolves

`architecture` (`mvvm` or `clean-mvvm`), `appName`, and `packageName` are required
and have no default. Everything else defaults: `projectDirName` (kebab-case app
name), `rootProjectName` (PascalCase app name), `initialFeature` (`home`),
`minSdk` `24`, `compileSdk`/`targetSdk` `34`, `includeDatabase`/`includeNetwork`/
`includeDatastore`/`includeTestUtilities`/`minifyRelease` (all `true`),
`gradleVersion` `8.6`. `includeNetwork` requires `includeDatabase` (offline-first).

### Editing the output

To change what a scaffolded file looks like, edit the matching template under
`assets/templates/` — for example
`assets/templates/app-build/T_APP_BUILD_MVVM.gradle.kts`. It is real Gradle Kotlin
DSL with `{{TOKEN}}` placeholders.

### Tradeoffs of the instruction-driven approach

Removing the generator script removes the guarantees it enforced. The agent now
performs these by hand, so treat the output as needing review:

- **No byte-for-byte determinism.** Two runs may differ; the script guaranteed
  identical output for identical settings.
- **No automated validation.** Package-name/reserved-word/SDK-ordering checks and
  the network-requires-database rule are now instructions the agent must apply,
  not code that enforces them.
- **No `--dry-run` / `--force`.** The agent writes files directly; it must not
  overwrite a non-empty directory without the user's go-ahead.
- **Launcher icons are a vector-XML placeholder**, not generated PNG mipmaps.

Always verify the result (SKILL.md Step 7): no leftover `{{TOKEN}}`, every
`package` matches its directory, and — for `clean-mvvm` — `domain/` stays
framework-free.

## The Gradle wrapper

`gradle-wrapper.jar` is a binary and cannot be authored as text. The scaffolded
project includes `gradle/wrapper/gradle-wrapper.properties`; generate the rest
with `gradle wrapper --gradle-version <version>` or by opening the project in
Android Studio. Do not download `gradle-wrapper.jar` from the internet on the
user's behalf.

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
