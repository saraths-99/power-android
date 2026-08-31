---
name: create-android-project
description: Interview the user for the basics of their app, help them pick between MVVM (single module) and Clean Architecture + MVVM (multi module), then scaffold the whole project from scratch with Compose, Hilt, an offline-first data layer, and a first feature wired end to end.
---

# Create an Android project from scratch

Use this when someone wants to start a new Android app, bootstrap an Android
project, or set up an Android codebase from nothing.

Do **not** use it to add a feature to an existing project. For that, read
`references/modularization.md` and follow the feature-module pattern.

## Two selectable architectures

Both are fully supported. The choice drives the entire generated layout, so make
it deliberately and never silently default.

### `mvvm` — single module, no domain layer

```
app/src/main/kotlin/<pkg>/
├── model/          Domain models
├── data/           local/ remote/ preferences/ mapper/ repository/
├── di/             Hilt modules
├── common/         Injected dispatcher qualifiers
└── ui/             theme/ components/ <feature>/ navigation/
```

The ViewModel talks to the repository directly. No use cases, no convention
plugins, no module graph. Recommend this for **small projects**: prototypes, a
handful of screens, one or two developers. The advantage is that there is very
little indirection to read through.

### `clean-mvvm` — multi module, Clean Architecture with MVVM on top

```
app/                  Entry point, DI wiring, NavHost
domain/               Pure Kotlin: models, repository interfaces, use cases
data/                 Repository implementations and mappers
core/common           Injected dispatcher qualifiers
core/designsystem     Theme, colours, typography
core/ui               Reusable composables
core/database         Room entities, DAO, database
core/network          Retrofit DTOs and remote data source
core/datastore        DataStore-backed settings
core/testing          Test doubles, Main dispatcher rule
feature/<name>/api    Navigation contract
feature/<name>/impl   Screen, ViewModel, UiState, Hilt bindings
build-logic/          Convention plugins shared by every module
```

The ViewModel depends on use cases, never on a repository. Three rules hold it
together, and breaking any one of them removes the benefit:

1. `domain` never depends on Android, so its tests run on the JVM.
2. Feature modules never depend on `data`; only `app` wires `data` in.
3. Features never depend on another feature's `impl`, only on its `api`.

Recommend this for **large or long-lived projects**: many screens, multiple
developers or teams, build times that matter, business rules that need reuse.

### Helping the user choose

Ask directly, and recommend based on what they tell you about scope. Reasonable
defaults if they are unsure:

| Signal | Recommend |
|---|---|
| Prototype, demo, side project, under ~5 screens | `mvvm` |
| Solo developer, wants to move fast | `mvvm` |
| Production app expected to grow | `clean-mvvm` |
| More than 2 developers, or separate teams | `clean-mvvm` |
| Shared business rules, or a KMP move later | `clean-mvvm` |

Say plainly that starting with `mvvm` is not a dead end: the generated README
explains how to extract `domain` and `data` modules later. Do not oversell
`clean-mvvm` for a small app; the extra indirection has a real cost.

## Step 1: Establish the target directory

Ask where the project should go if it is not obvious. Default to the current
workspace root. Confirm the resolved absolute path before writing anything, and
never scaffold over an existing project without saying so.

## Step 2: Interview the user

Ask for everything in **one message**, as a short numbered list with the defaults
shown. Do not ask one question per turn. Tell the user they can reply "defaults"
to accept everything except the required answers.

**Required — do not guess these:**

1. **Architecture** — `mvvm` or `clean-mvvm`. Present the tradeoff in one or two
   lines each, as above.
2. **App name** — the display name under the launcher icon, e.g. `Trail Log`.
3. **Package name** — the applicationId and Kotlin root package, e.g.
   `com.acme.traillog`. Lowercase dotted segments. If they give a name but no
   package, propose one from a reverse domain they choose rather than assuming
   `com.example`.

**Everything else has a default — offer, do not interrogate:**

4. **Project folder name** — default: kebab-case of the app name.
5. **First screen / feature name** — one lowercase word, default `home`.
6. **minSdk** — default `24`. Mention the tradeoff only if asked.
7. **compileSdk / targetSdk** — default `34` for both.
8. **Local database (Room)** — default yes.
9. **Remote API (Retrofit + kotlinx.serialization)** — default yes. Requires
   Room, because the generated repository is offline-first and needs a local
   source of truth. If they want network without a database, explain that and let
   them decide.
10. **User settings storage (Preferences DataStore)** — default yes. Also wires
    dark-theme and dynamic-colour preferences through the app.
11. **Test utilities** — default yes. In `clean-mvvm` this is a `core:testing`
    module; in `mvvm` it is a `src/test` package. Either way it generates test
    *helpers*, not test cases.
12. **Minify the release build (R8)** — default yes.

See `references/project-interview.md` for wording, follow-ups, and how to map
vague answers onto these options.

## Step 3: Settle the settings, then validate them

This skill scaffolds the project by copying the templates under
`assets/templates/` and substituting tokens — there is no generator script to
run. So the values you resolve here are used directly; get them right before
writing any file.

Collect these into a small settings block:

```
architecture      mvvm | clean-mvvm     (required)
appName           display name          (required)
packageName       applicationId/root    (required)
projectDirName    kebab-case of appName
rootProjectName   PascalCase of appName
initialFeature    one lowercase word    (default: home)
minSdk 24  compileSdk 34  targetSdk 34
includeDatabase / includeNetwork / includeDatastore / includeTestUtilities / minifyRelease  (default true)
gradleVersion     8.6
```

**Validate them yourself — nothing else will.** Reject and fix before proceeding
if any of these fail:

- `packageName` matches `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$` (lowercase dotted
  segments), and no segment is a Kotlin/Java reserved word (`class`, `object`,
  `fun`, `val`, `var`, `is`, `in`, `data`, `enum`, `interface`, …).
- `initialFeature` is a single lowercase word and not a reserved word.
- `minSdk >= 21`, `targetSdk <= compileSdk`, `minSdk <= targetSdk`.
- `includeNetwork` implies `includeDatabase` — the generated repository is
  offline-first, so remote data needs a local source of truth. If the user wants
  network without a database, explain this and let them decide.

Echo the resolved settings back in two or three lines and get a yes before
writing files. This is the last cheap moment to fix a wrong package name or a
wrong architecture. There is no `--dry-run` and no `--force`: you are writing
files directly, so never write into a non-empty target directory without the
user's explicit go-ahead.

## Step 4: Scaffold the project by copying templates

Resolve every token once, then create each file. Work from these references:

- `references/token-map.md` — how to compute every token (`PKG`, `APP_CLASS`,
  `APP_ROOT`, `PREFIX`, `DB_NAME`, the ~20 architecture-specific `PKG_*` package
  roots, and the conditional same-package import tokens).
- `references/file-manifest.md` — which template maps to which destination path,
  and which files each `include*` flag adds or drops.
- `references/project-structure.md` — the module graph and package layout you are
  reproducing.

Procedure:

1. **Compute the tokens** for the chosen architecture (token-map.md §1–3). Do
   this once; reuse the values everywhere.
2. **Create the files** in the manifest that apply to this architecture and flag
   set. For each: read the template from `assets/templates/…`, replace **every**
   `{{TOKEN}}` (longest names first), and write it to
   `<module>/src/main/kotlin/<package-as-path>/<FileName>.kt` (or the resource /
   root path given in the manifest).
3. **Assemble the flag-driven lists** by hand: the plugin and dependency lists in
   each `build.gradle.kts`, the `settings.gradle.kts` includes, and the version
   catalog (append the convention section only for `clean-mvvm`). See
   project-structure.md §3 for exactly what each flag adds.
4. **Emit the project's own steering** into `.kiro/steering/`
   (`module-architecture.md`, `build-conventions.md`, `code-patterns.md`) from
   `assets/steering/…`, rendered for the chosen architecture. These keep later
   sessions in the new repository consistent with how it was scaffolded, so
   mention them in the final report.
5. **Substitution is exhaustive.** After writing everything, search the output
   tree for `{{` and `}}`; there must be zero matches. A leftover token is a bug —
   fix it before continuing.

Because you are doing the substitution and the conditional wiring by hand, the
output is only as correct as this pass. Double-check the two most common mistakes:
a `package` line that does not match the file's directory, and a same-package
import that should have been elided (token-map.md §3).

## Step 5: Add launcher icons (vector, not PNG)

There is no image generator here. Provide an **adaptive icon defined in XML** so
resource resolution works without any binary asset:

- `app/src/main/res/values/ic_launcher_background.xml` — a color resource.
- `app/src/main/res/drawable/ic_launcher_foreground.xml` — a simple vector
  drawable (a monochrome glyph on transparent is fine).
- `app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml` and
  `ic_launcher_round.xml` — `<adaptive-icon>` referencing the two above.

This is a placeholder the user is expected to replace with real assets (mention
it in the report). If the user needs density-specific PNG mipmaps, they add those
in Android Studio's Image Asset tool.

## Step 6: Generate the Gradle wrapper

The wrapper needs a binary JAR, which cannot be authored as text, so it is not
scaffolded. Have the user run one of:

```bash
gradle wrapper --gradle-version <gradleVersion>   # if a local gradle is installed
```

or open the project in Android Studio, which creates the wrapper with no manual
download. Do not download `gradle-wrapper.jar` from the internet on the user's
behalf; that is a supply-chain decision that belongs to them.

## Step 7: Verify

Run the build and fix anything that breaks before reporting success:

```bash
cd <project-dir>
./gradlew :app:assembleDebug
```

The first run downloads AGP, Kotlin and the Compose compiler, so expect a few
minutes. It also needs the Android SDK: if `ANDROID_HOME` / `ANDROID_SDK_ROOT` is
unset and there is no `local.properties`, Gradle fails with
`SDK location not found`. That is an environment problem, not a scaffolding bug.

For `clean-mvvm`, `./gradlew :domain:test` is a useful extra check: it proves the
domain layer really is framework-free.

If you cannot run a build in this environment, say so plainly. Do not call the
project verified when it has only been generated. At minimum confirm:

- no `{{TOKEN}}` remains anywhere in the tree (grep for `{{`)
- `settings.gradle.kts` includes every module directory that exists
- every `alias(libs.plugins.…)` and `libs.…` reference resolves in
  `gradle/libs.versions.toml`
- each Kotlin file's `package` matches its directory
- for `clean-mvvm`: nothing under `domain/` imports `android.`, `androidx.` or
  `dagger.`, and no feature module depends on `:data`

## Step 8: Report

Tell the user:

- the absolute project path, the architecture, and the module list
- which optional layers were included
- whether the build ran, and the result
- the placeholders they must replace: the vector launcher icon under
  `app/src/main/res/` (Step 5), brand colours in the design system, `BASE_URL` in
  the network layer, the sample `Item` model, and the missing release signing
  config

Then read `references/post-setup.md` and offer the obvious next step: renaming
the sample model to their real domain, or adding a second feature.

## Reference material

| Topic | File |
|---|---|
| Interview wording and follow-ups | `references/project-interview.md` |
| Choosing between the two architectures | `references/architecture-selection.md` |
| Token computation and substitution rules | `references/token-map.md` |
| Which template goes where (per architecture/flags) | `references/file-manifest.md` |
| Per-architecture module/package layout and inclusion matrix | `references/project-structure.md` |
| What to do after scaffolding | `references/post-setup.md` |
| Module boundaries and dependency rules | `references/modularization.md` |
| UI / domain / data layer patterns | `references/architecture.md` |
| Compose conventions | `references/compose-patterns.md` |
| Gradle and convention plugin details | `references/gradle-setup.md` |
| Testing approach and test doubles | `references/testing.md` |

## Conventions the generated code follows

Both architectures share these. Match them when you extend the project.

- **Unidirectional data flow.** Screens receive state and emit actions; only the
  ViewModel mutates state.
- **Offline-first.** The database is the source of truth; the network refreshes it.
- **Reactive streams.** Repositories expose `Flow`, not suspend getters that
  return a snapshot.
- **Injected dispatchers.** Never reference `Dispatchers.IO` directly; inject it
  with the `@Dispatcher` qualifier so tests can substitute a test dispatcher.
- **Stateless, previewable composables.** A stateful `…Route` reads the
  ViewModel; a stateless `…Screen` renders and carries the `@Preview`.
- **Separate models per layer.** Entities and DTOs are mapped to domain models;
  neither ever reaches the UI.
- **Hand-written test doubles.** No mocking library. Doubles fail to compile when
  an interface changes, instead of failing at runtime.
- **Versions in one place.** Add dependencies to `gradle/libs.versions.toml`,
  never inline in a module's `build.gradle.kts`.

The Kotlin version and the Compose compiler version in the catalog are a matched
pair. Bumping one without the other breaks the build.

Additional to `clean-mvvm` only:

- **Use cases carry business operations**, one class per operation, invoked with
  `operator fun invoke`.
- **Repository interfaces live in `domain`**, implementations in `data`. That
  inversion is the whole point of the layout.
