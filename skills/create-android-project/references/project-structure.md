# Project structure reference

The authoritative source for what the scaffolder produces is
`scripts/scaffold_android_project.py` (`build_mvvm`, `build_clean`, and the
`build_context` package map). This document mirrors that logic in human-readable
form so the structure can be reviewed, but **it is derived — the script wins if
they ever disagree**, and the script must not be hand-reimplemented from this doc.

Two architectures are produced, selected by the required `architecture` config
key. The choice changes the entire module graph and the package layout.

---

## 1. `mvvm` — single module

One `:app` module. No domain layer, no convention plugins. The ViewModel talks to
a repository directly.

### Module graph

```
:app        # the only module
```

`settings.gradle.kts` contains just `include(":app")`.

### Package layout (under `app/src/main/kotlin/<pkg>/`)

Package roots come from `build_context`. For `mvvm`:

| Role | Package |
|---|---|
| Domain models | `<pkg>.model` |
| Repository interface | `<pkg>.data.repository` |
| Repository implementation | `<pkg>.data.repository` |
| Mappers | `<pkg>.data.mapper` |
| Room / local | `<pkg>.data.local` |
| Network / remote | `<pkg>.data.remote` |
| Preferences (DataStore) | `<pkg>.data.preferences` |
| Dispatchers | `<pkg>.common` |
| DI (Hilt modules) | `<pkg>.di` |
| Theme | `<pkg>.ui.theme` |
| Reusable components | `<pkg>.ui.components` |
| Feature screen/VM/UiState | `<pkg>.ui.<feature>` |
| Navigation (nav contract in `Routes.kt`) | `<pkg>.ui.navigation` |
| Test doubles | `<pkg>.testing` (in `src/test`) |

```
app/src/main/kotlin/<pkg>/
├── model/                     Domain models (Item, UserData, DarkThemeConfig)
├── common/                    AppDispatchers
├── data/
│   ├── local/                 Room entity, DAO, database, DI          [database]
│   ├── remote/                DTO, RemoteDataSource, Retrofit impl, DI [network]
│   ├── preferences/           DataStore source                        [datastore]
│   ├── mapper/                Entity/DTO/prefs → domain mappers
│   └── repository/            ItemRepository (+impl), UserDataRepository
├── di/                        Hilt modules (Repository, Database, Network, ...)
└── ui/
    ├── theme/
    ├── components/
    ├── navigation/            NavHost + routes
    └── <feature>/             Route, Screen, ViewModel, UiState
```

The ViewModel constructor takes the repository interface directly
(`private val itemRepository: ItemRepository`).

---

## 2. `clean-mvvm` — multi module, Clean Architecture + MVVM

A pure-Kotlin `domain` module owns models, repository interfaces and use cases;
`data` implements them; feature modules depend on `domain` only. Convention
plugins in `build-logic/` are shared by every module.

### Module graph

```
build-logic/               Convention plugins (composite build)
app/                        Entry point, DI wiring, NavHost; the only wirer of :data
domain/                     Pure Kotlin: models, repository interfaces, use cases
data/                       Repository implementations + mappers
core/common                Injected dispatchers                        [always]
core/designsystem          Theme                                       [always]
core/ui                    Reusable composables                        [always]
core/database              Room entities, DAO, database                [database]
core/network               Retrofit DTOs + remote data source          [network]
core/datastore             DataStore-backed settings                   [datastore]
core/testing               Test doubles + Main dispatcher rule         [testUtilities]
feature/<name>/api         Navigation contract
feature/<name>/impl        Screen, ViewModel, UiState, Hilt bindings
```

`settings.gradle.kts` includes `:app`, `:domain`, `:data`, every present
`:core:*`, and `:feature:<name>:api` + `:impl`, and `includeBuild("build-logic")`.

### Package layout

Package roots for `clean-mvvm` (from `build_context`):

| Role | Module | Package |
|---|---|---|
| Domain models | `domain` | `<pkg>.domain.model` |
| Repository interface | `domain` | `<pkg>.domain.repository` |
| Use cases | `domain` | `<pkg>.domain.usecase` |
| Repository implementation | `data` | `<pkg>.data.repository` |
| Mappers | `data` | `<pkg>.data.mapper` |
| Data DI (repository bindings) | `data` | `<pkg>.data.di` |
| Dispatchers | `core/common` | `<pkg>.core.common.dispatcher` |
| Room / local | `core/database` | `<pkg>.core.database` |
| Network / remote | `core/network` | `<pkg>.core.network` |
| Preferences (DataStore) | `core/datastore` | `<pkg>.core.datastore` |
| Theme | `core/designsystem` | `<pkg>.core.designsystem.theme` |
| Reusable components | `core/ui` | `<pkg>.core.ui` |
| Feature nav contract (`<Feature>Navigation.kt`) | `feature/<f>/api` | `<pkg>.feature.<f>.api` |
| Feature screen/VM/UiState | `feature/<f>/impl` | `<pkg>.feature.<f>.impl` |
| App NavHost | `app` | `<pkg>.navigation` |
| Test doubles | `core/testing` | `<pkg>.core.testing` |

The ViewModel constructor takes **use cases**, never a repository
(e.g. `observeItems: ObserveItemsUseCase, private val syncItems: SyncItemsUseCase`).

### Dependency rules (enforced by the module graph)

1. `domain` depends on nothing Android — pure Kotlin (`jvm.library` plugin,
   only `kotlinx-coroutines-core` + `javax.inject`). Its tests run on the JVM.
2. `data` depends on `domain` (`api`) and the relevant `core:*` sources; it is
   the only place that maps entities/DTOs to domain models.
3. `core:database` / `core:network` do **not** depend on `domain`; mapping to
   domain models happens in `data`, keeping those modules swappable.
4. Feature `impl` depends only on its own `api` (+ `core:testing` for tests);
   never on `data` and never on another feature's `impl`.
5. Only `app` wires in `:data`. Features see only `:domain`.

---

## 3. Conditional inclusion matrix

Five boolean config flags add or remove whole files/modules. `mvvm` adds files to
`:app`; `clean-mvvm` adds whole modules. `includeNetwork` requires
`includeDatabase` (validated — the generated repository is offline-first).

| Flag (default) | `mvvm` adds | `clean-mvvm` adds |
|---|---|---|
| `includeDatabase` (true) | `data/local/` entity, DAO, database, `DatabaseModule`; offline `ItemRepositoryImpl` + `ItemMappers` | whole `core:database` module; offline repo impl + mappers in `:data` |
| `includeNetwork` (true, needs database) | `data/remote/` DTO, `ItemRemoteDataSource`, Retrofit impl, `NetworkModule` | whole `core:network` module |
| `includeDatastore` (true) | `data/preferences/` source, `DataStoreModule`, `PreferencesMappers`; `UserData`/`DarkThemeConfig` models; `UserDataRepository` (+impl); theme-settings wiring | same, split across `core:datastore` (+ models/repo in `domain`/`data`) |
| `includeTestUtilities` (true) | `MainDispatcherRule` + `FakeItemRepository` in `src/test`; Turbine dep | whole `core:testing` module |
| `minifyRelease` (true) | R8 on release build in `app/build.gradle.kts` | same |

When `includeDatabase` is false, the repository implementation is the in-memory
variant (`T_REPO_ITEM_IMPL_MEMORY`) instead of the offline-first one.

---

## 4. Files generated regardless of architecture (contents vary)

These are written for both architectures, though several differ in content per
architecture: `settings.gradle.kts` (contents
differ), root `build.gradle.kts`, `gradle.properties`, `gradle/libs.versions.toml`
(the convention section is appended only for `clean-mvvm`),
`gradle/wrapper/gradle-wrapper.properties`, `.gitignore`, `README.md` (architecture-
specific), launcher icon PNGs (generated as real binaries), and a
`.kiro/steering/` directory rendered for the chosen architecture
(`module-architecture.md`, `build-conventions.md`, `code-patterns.md`).

---

## 5. Why this stays in the script, not in prose

Reproducing this structure by hand — rather than running the scaffolder — loses
the guarantees the script enforces: the architecture branching, the exact package
map above, the conditional inclusion, config validation (valid package, no
reserved words, SDK ordering, the network-requires-database rule), token
rendering with same-package import elision, and the binary launcher icons. Use
this document to understand and review the output; use the script to produce it.
