# Token map and substitution rules

Every template under `assets/templates/` is real source (Kotlin, Gradle Kotlin
DSL, XML, TOML, Markdown) containing `{{TOKEN}}` placeholders. To scaffold a
project you copy each template to its destination and replace every token. **No
token may remain** in a written file — an unresolved `{{...}}` is a bug.

Resolve longest token names first (so `{{PKG_MODEL}}` is never partially matched
by `{{PKG}}`).

## 1. Derived identifier tokens

From the interview answers, compute:

| Token | How to derive it | Example (`appName="Trail Log"`, `packageName="com.acme.traillog"`, `rootProjectName="TrailLog"`, `initialFeature="home"`) |
|---|---|---|
| `PKG` | the package name verbatim | `com.acme.traillog` |
| `APP_NAME` | app name verbatim | `Trail Log` |
| `APP_NAME_XML` | app name, XML-escaped | `Trail Log` |
| `APP_NAME_KT` | app name, escaped for a Kotlin `"..."` literal | `Trail Log` |
| `APP_CLASS` | PascalCase of app name | `TrailLog` |
| `APP_ROOT` | `APP_CLASS`, plus `App` unless it already ends in `App` | `TrailLogApp` |
| `ROOT_PROJECT` | rootProjectName | `TrailLog` |
| `PREFIX` | lowercased alphanumerics of `ROOT_PROJECT` | `traillog` |
| `DB_NAME` | kebab-case of `ROOT_PROJECT` + `-database` | `trail-log-database` |
| `FEATURE` | the feature word (lowercase) | `home` |
| `FEATURE_CLASS` | PascalCase of feature | `Home` |
| `FEATURE_UPPER` | uppercase feature | `HOME` |
| `MIN_SDK`/`COMPILE_SDK`/`TARGET_SDK` | the SDK integers | `24`/`34`/`34` |
| `JAVA_VERSION` | always `17` | `17` |
| `GRADLE_VERSION` | chosen Gradle version | `8.6` |
| `ARCHITECTURE` | `mvvm` or `clean-mvvm` | `clean-mvvm` |

## 2. Package tokens (differ per architecture)

Use the table below. These map every role to its package root. Full layout and
rationale: `references/project-structure.md`.

| Token | `mvvm` | `clean-mvvm` |
|---|---|---|
| `PKG_MODEL` | `{PKG}.model` | `{PKG}.domain.model` |
| `PKG_REPO` | `{PKG}.data.repository` | `{PKG}.domain.repository` |
| `PKG_USECASE` | `{PKG}.data.repository` (unused) | `{PKG}.domain.usecase` |
| `PKG_REPO_IMPL` | `{PKG}.data.repository` | `{PKG}.data.repository` |
| `PKG_MAPPER` | `{PKG}.data.mapper` | `{PKG}.data.mapper` |
| `PKG_DATA_DI` | `{PKG}.di` | `{PKG}.data.di` |
| `PKG_RESULT` | `{PKG}.common` | `{PKG}.core.common.result` |
| `PKG_DISPATCHERS` | `{PKG}.common` | `{PKG}.core.common.dispatcher` |
| `PKG_DISPATCHERS_DI` | `{PKG}.di` | `{PKG}.core.common.dispatcher.di` |
| `PKG_DB` | `{PKG}.data.local` | `{PKG}.core.database` |
| `PKG_DB_DI` | `{PKG}.di` | `{PKG}.core.database.di` |
| `PKG_NET` | `{PKG}.data.remote` | `{PKG}.core.network` |
| `PKG_NET_DI` | `{PKG}.di` | `{PKG}.core.network.di` |
| `PKG_PREFS` | `{PKG}.data.preferences` | `{PKG}.core.datastore` |
| `PKG_PREFS_DI` | `{PKG}.di` | `{PKG}.core.datastore.di` |
| `PKG_THEME` | `{PKG}.ui.theme` | `{PKG}.core.designsystem.theme` |
| `PKG_COMPONENTS` | `{PKG}.ui.components` | `{PKG}.core.ui` |
| `PKG_FEATURE` | `{PKG}.ui.{FEATURE}` | `{PKG}.feature.{FEATURE}.impl` |
| `PKG_FEATURE_NAV` | `{PKG}.ui.navigation` | `{PKG}.feature.{FEATURE}.impl.navigation` |
| `PKG_FEATURE_API` | `{PKG}.ui.navigation` | `{PKG}.feature.{FEATURE}.api` |
| `PKG_NAV` | `{PKG}.ui.navigation` | `{PKG}.navigation` |
| `PKG_APP_UI` | `{PKG}.ui` | `{PKG}.ui` |
| `PKG_TESTING` | `{PKG}.testing` | `{PKG}.core.testing` |

## 3. Conditional (same-package) tokens

In the single-module `mvvm` layout several roles share one package, so an import
between them would be redundant (and in some cases a compile error). Emit these
tokens as an **import line** only when the two packages differ; otherwise emit an
**empty string**.

| Token | `mvvm` value | `clean-mvvm` value |
|---|---|---|
| `R_IMPORT` | `import {PKG}.R\n` (R is at the app namespace) | `` (empty; feature module namespace == package) |
| `REPO_IFACE_IMPORT` | `` (interface + impl share `{PKG}.data.repository`) | `import {PKG}.domain.repository.ItemRepository\n` |
| `USER_REPO_IFACE_IMPORT` | `` | `import {PKG}.domain.repository.UserDataRepository\n` |
| `ROUTE_IMPORT` | `` (api + nav share `{PKG}.ui.navigation`) | `import {PKG}.feature.{FEATURE}.api.{FEATURE_UPPER}_ROUTE\n` |
| `NAVHOST_IMPORTS` | `` | `import {PKG}.feature.{FEATURE}.api.{FEATURE_UPPER}_ROUTE\nimport {PKG}.feature.{FEATURE}.impl.navigation.{FEATURE}Screen\n` |
| `ACTIVITY_VM_IMPORT` | `import {PKG}.data.repository.UserDataRepository\n` | `import {PKG}.domain.usecase.ObserveUserDataUseCase\n` |
| `ACTIVITY_VM_PARAM` | `userDataRepository: UserDataRepository,` | `observeUserData: ObserveUserDataUseCase,` |
| `ACTIVITY_VM_SOURCE` | `userDataRepository.userData` | `observeUserData()` |

General rule for any "same-package import" token: if the symbol's package equals
the consuming file's package, the token is empty; otherwise it is a full
`import <pkg>.<Symbol>\n` line.

## 4. Verify before finishing

After writing every file, grep the output tree for `{{` and `}}`. Any hit means a
token was missed. There must be zero.
