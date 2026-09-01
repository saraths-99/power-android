---
name: create-android-project
description: Bootstrap a brand-new Android app from scratch — interview the user, pick between MVVM (single module) and Clean Architecture + MVVM (multi module), then scaffold the whole project with Compose, Hilt, an offline-first data layer, a first feature wired end to end, and matching steering docs. Also covers adding a feature/screen to an existing MVVM or Clean Architecture + MVVM Android app, using copy-adaptable per-layer templates. Use whenever someone wants to start a new Android app, scaffold/bootstrap an Android project or codebase "from scratch" or "from nothing", asks which Android architecture to pick for a new app, or wants to add a feature/screen to an existing MVVM or Clean Architecture Android app.
---

# Create an Android project, or add a feature to one

This skill covers two different jobs. Figure out which one applies before doing
anything.

## Job 1: Bootstrap a brand-new project

Use this when someone wants to start a new Android app, bootstrap an Android
project, or set up an Android codebase from nothing. Follow Steps 1–8 below:
interview, scaffold, verify, report.

## Job 2: Add a feature to an existing project

Use this when someone wants to add a feature or screen to an Android app that
already exists and already follows MVVM or Clean Architecture + MVVM — whether or
not this skill scaffolded it. Skip Steps 1–8 entirely; they are the from-scratch
scaffold flow and would overwrite or duplicate what's already there. Instead:

1. Find out (or infer from the existing code) which architecture the project
   uses — single-module `mvvm` or multi-module `clean-mvvm` — and its actual
   package name and module layout. Never assume `com.example.app`.
2. Read `references/post-setup.md` §"Adding a second feature" for the
   module/Gradle wiring the target architecture needs (new package or new Gradle
   modules, `settings.gradle.kts` registration, route wiring). For `clean-mvvm`,
   `references/modularization.md` has the fuller module-dependency-rules picture
   if the project's module graph needs it.
3. Read `references/single-module-mvvm-reference.md` (mvvm) or
   `references/clean-mvvm-reference.md` (clean-mvvm) for the per-layer code
   templates — UiState, ViewModel, Route/Content, Repository, and for
   `clean-mvvm` also UseCase and the repository interface.
4. Adapt every template to the existing project's real package name, entity, and
   naming conventions — the templates use a placeholder `com.example.app`/`User`
   throughout, which must not leak into the output.

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
and the generated `.kiro/steering/module-architecture.md` both explain how to
extract `domain` and `data` modules later (see that file's own §5/§6). Do not
oversell `clean-mvvm` for a small app; the extra indirection has a real cost.

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
11. **Test utilities** — default no. In `clean-mvvm` this is a `core:testing`
    module; in `mvvm` it is a `src/test` package. Either way it generates test
    *helpers*, not test cases.
12. **Minify the release build (R8)** — default yes.
13. **Java/Kotlin JVM target** — default `17` (matches AGP 8.x / Kotlin 1.9+ and
    `compileSdk 34`).

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
minSdk 24  compileSdk 34  targetSdk 34  javaVersion 17
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
- `javaVersion` is `11` or `17` (17 unless the user has a specific reason to pin
  older).
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

- `references/token-map.md` — how to compute every project-wide token (`PKG`,
  `APP_CLASS`, `APP_ROOT`, `PREFIX`, `DB_NAME`, the ~20 architecture-specific
  `PKG_*` package roots, and the conditional same-package import tokens). The
  steering-file tokens below are a separate, self-contained set — they don't
  need token-map.md.
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
   root path given in the manifest). For the Gradle wrapper files (gradlew,
   gradlew.bat, gradle-wrapper.jar), copy them directly from the templates
   without token substitution. Set executable permissions on gradlew for Unix
   systems (use execute_bash with chmod +x).
3. **Assemble the flag-driven lists** by hand: the plugin and dependency lists in
   each `build.gradle.kts`, the `settings.gradle.kts` includes, and the version
   catalog (append the convention section only for `clean-mvvm`). See
   project-structure.md §3 for exactly what each flag adds.
4. **Emit the project's own steering** into `.kiro/steering/` — see the dedicated
   subsection immediately below; it is exhaustive and self-contained.
5. **Substitution is exhaustive.** After writing everything, search the output
   tree for `{{` and `}}`; there must be zero matches. A leftover token is a bug —
   fix it before continuing. Verify gradle-wrapper.jar is exactly 43453 bytes
   (the Gradle 8.7 wrapper JAR size). Verify gradlew has Unix executable
   permissions (755 or +x).

Because you are doing the substitution and the conditional wiring by hand, the
output is only as correct as this pass. Double-check the two most common mistakes:
a `package` line that does not match the file's directory, and a same-package
import that should have been elided (token-map.md §3).

### Emitting steering docs (`.kiro/steering/`)

Three files go to `.kiro/steering/`, one architecture-selected pair plus one
shared-but-conditional template:

| Output file | Source template | Selection |
|---|---|---|
| `.kiro/steering/module-architecture.md` | `assets/steering/module-architecture-mvvm.md` or `-clean-mvvm.md` | pick by `architecture` |
| `.kiro/steering/build-conventions.md` | `assets/steering/build-conventions-mvvm.md` or `-clean-mvvm.md` | pick by `architecture` |
| `.kiro/steering/code-patterns.md` | `assets/steering/code-patterns.md` (single file, both architectures) | always this one, tokens differ by `architecture` |

`module-architecture.md` and `build-conventions.md` only need the ordinary
project-wide tokens (`PROJECT_NAME`, `PREFIX`, `PACKAGE_NAME`, `PACKAGE_PATH`,
`APP_CLASS`, `FEATURE`, `COMPILE_SDK`, `TARGET_SDK`, `MIN_SDK`, `JAVA_VERSION`)
from Step 4.1 — substitute and copy, no architecture branching needed inside the
file itself since you already picked the right variant.

`code-patterns.md` is the one file that's genuinely shared, so it carries extra
tokens whose value depends on `architecture`. Resolve them from this table —
don't guess, these are load-bearing for whether the generated code matches the
generated `module-architecture.md`:

| Token | `mvvm` value | `clean-mvvm` value |
|---|---|---|
| `{{COMPONENT_HOME}}` | `ui/components/` | `core:ui` |
| `{{DATA_FLOW_DIAGRAM}}` | `Screen ⇄ ViewModel (StateFlow down, Action up) ⇄ Repository ⇄ local/remote source` | `Screen ⇄ ViewModel (StateFlow down, Action up) ⇄ UseCase ⇄ Repository (domain interface) ⇄ RepositoryImpl (data) ⇄ local/remote source` |
| `{{VM_CONSTRUCTOR}}` | `    private val itemRepository: ItemRepository,\n` | `    private val observeItemsUseCase: ObserveItemsUseCase,\n` |
| `{{VM_SOURCE}}` | `itemRepository.observeItems()` | `observeItemsUseCase()` |
| `{{VM_DEPENDENCY_RULE}}` | "The ViewModel depends on the repository interface directly. There is no use-case layer at this module size — see `module-architecture.md` §2." | "The ViewModel depends only on use cases from `domain`, never on a repository. See `module-architecture.md` §2 and §4." |
| `{{USE_CASE_SECTION}}` | *(empty string — section omitted)* | Short paragraph: "Use cases are the only thing a ViewModel is allowed to see. One class per business operation, invoked with `operator fun invoke` — see `module-architecture.md` §4 for the full pattern.\n\n" |
| `{{REPO_INTERFACE_HOME}}` | `data/repository/` | `domain/repository/` |
| `{{REPO_BINDING_HOME}}` | `di/` (an `@Provides` Hilt module, e.g. `di/AppModule.kt`) | `data/di/` (an `@Binds` Hilt module, e.g. `data/di/RepositoryModule.kt`) |
| `{{USE_CASE_NAMING_ROW}}` | *(empty string — table row omitted)* | `\| Use case \| \`<Verb><Noun>UseCase\`, one class per operation \|\n` |
| `{{TEST_DOUBLE_HOME}}` | `src/test/kotlin/{{PACKAGE_PATH}}/fake/` | `core:testing` |

These ten tokens are independent of `references/token-map.md` — resolve them
directly from the table above using the already-known `architecture` setting.
`{{FEATURE}}`, `{{APP_CLASS}}`, `{{PROJECT_NAME}}`, and `{{PACKAGE_PATH}}` inside
`code-patterns.md` reuse the ordinary project-wide token values.

After substitution, `.kiro/steering/code-patterns.md` should read as one
coherent document with no visible seam — the empty-string tokens (`mvvm` case)
must not leave a blank line or a dangling table row behind; the non-empty ones
(`clean-mvvm` case) must not collide with the numbered-heading sequence in the
surrounding text.

## Step 5: Add launcher icons (vector, not PNG)

There is no image generator here. Provide an **adaptive icon defined in XML** so
resource resolution works without any binary asset. The manifest references
`@mipmap/ic_launcher` and `@mipmap/ic_launcher_round` unconditionally, and the
default `minSdk` is 24, so you must supply a fallback that also resolves below
API 26 — not only the `-v26` adaptive icon. Create:

- `app/src/main/res/values/ic_launcher_background.xml` — a color resource.
- `app/src/main/res/drawable/ic_launcher_foreground.xml` — a simple vector
  drawable (a monochrome glyph on transparent is fine).
- `app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml` and
  `ic_launcher_round.xml` — `<adaptive-icon>` referencing the two above (API 26+).
- `app/src/main/res/drawable/ic_launcher.xml` — a plain vector drawable used as
  the pre-API-26 fallback, and
  `app/src/main/res/mipmap-anydpi/ic_launcher.xml` + `ic_launcher_round.xml` that
  alias it (`<bitmap>`/`<inset>` or a simple `<vector>`), so both mipmap names
  resolve on API 24–25 as well.

This is a placeholder the user is expected to replace with real assets (mention
it in the report). If the user needs density-specific PNG mipmaps, they add those
in Android Studio's Image Asset tool.

## Step 6: Verify Gradle wrapper

The Gradle wrapper files (gradlew, gradlew.bat, gradle-wrapper.jar, gradle-wrapper.properties) are 
now generated as part of the scaffolding process in Step 4. No additional gradle command is needed.

Verify the wrapper is complete:
- `gradle/wrapper/gradle-wrapper.properties` exists and specifies Gradle 8.7
- `gradle/wrapper/gradle-wrapper.jar` exists and is ~60KB
- `gradlew` exists and is executable (Unix systems)
- `gradlew.bat` exists (Windows systems)

If any wrapper component is missing, re-run Step 4 to regenerate the project structure.

## Step 7: Verify

Run the build using the generated Gradle wrapper to verify the project is correctly configured:

```bash
cd <project-dir>
./gradlew :app:assembleDebug
```

The first run downloads AGP, Kotlin and the Compose compiler, so expect a few
minutes. It also needs the Android SDK: if `ANDROID_HOME` / `ANDROID_SDK_ROOT` is
unset and there is no `local.properties`, Gradle fails with
`SDK location not found`. That is an environment problem, not a scaffolding bug.

For `clean-mvvm`, `./gradlew :domain:test` is a useful extra check: it proves the
domain layer really is framework-free — the same check `module-architecture.md`
§7 documents for later in the project's life.

If you cannot run a build in this environment, say so plainly. Do not call the
project verified when it has only been generated. At minimum confirm:

- no `{{TOKEN}}` remains anywhere in the tree (grep for `{{`), including inside
  `.kiro/steering/`
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
- that `.kiro/steering/module-architecture.md`, `build-conventions.md`, and
  `code-patterns.md` were generated for the chosen architecture, and that later
  sessions in this repo will read them automatically
- the placeholders they must replace: the vector launcher icon under
  `app/src/main/res/` (Step 5), brand colours in the design system, `BASE_URL` in
  the network layer, the sample `Item` model, and the missing release signing
  config

Then read `references/post-setup.md` and offer the obvious next step: renaming
the sample model to their real domain, or adding a second feature. For the
latter, mention that this same skill handles it (see "Job 2" above) — no need to
start a new conversation for it.

## Reference material

| Topic | File |
|---|---|
| Interview wording and follow-ups | `references/project-interview.md` |
| Choosing between the two architectures | `references/architecture-selection.md` |
| Token computation and substitution rules | `references/token-map.md` |
| Which template goes where (per architecture/flags) | `references/file-manifest.md` |
| Per-architecture module/package layout and inclusion matrix | `references/project-structure.md` |
| Steering-doc templates and their conditional tokens | `assets/steering/` (see Step 4 table) |
| What to do after scaffolding | `references/post-setup.md` |
| Module boundaries and dependency rules | `references/modularization.md` |
| UI / domain / data layer patterns | `references/architecture.md` |
| Compose conventions | `references/compose-patterns.md` |
| Gradle and convention plugin details | `references/gradle-setup.md` |
| Testing approach and test doubles | `references/testing.md` |
| Per-layer code templates for adding a feature (Job 2) | `references/single-module-mvvm-reference.md` (mvvm) or `references/clean-mvvm-reference.md` (clean-mvvm) |

## Conventions the generated code follows

Both architectures share these. Match them when you extend the project — they
are also what `.kiro/steering/code-patterns.md` documents for later sessions.

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