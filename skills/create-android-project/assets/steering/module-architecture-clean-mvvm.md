# {{PROJECT_NAME}} — Module Architecture

Owns the module graph, dependency direction, and layer responsibilities for this
project. Build tooling rules live in `build-conventions.md`; class-level patterns
live in `code-patterns.md`.

This project uses **Clean Architecture with MVVM in the presentation layer**, as a
multi-module Gradle build. Keep it that way unless there is a deliberate decision
to collapse it.

## 1. Module graph

```
app/                        Single Activity, theme wiring, NavHost, DI entry point
build-logic/convention/     Convention plugins ({{PREFIX}}.*) applied by every module
domain/                     Models, repository interfaces, use cases (pure Kotlin)
data/                       Repository implementations, mappers, Hilt bindings
core/common                 Injected dispatcher qualifiers
core/designsystem           Material 3 theme, colours, typography
core/ui                     Reusable composables built on the design system
core/database               Room entities, DAOs, database            (if present)
core/network                Retrofit services, wire models (DTOs)    (if present)
core/datastore              Preferences DataStore, user settings     (if present)
core/testing                Test doubles, MainDispatcherRule         (if present)
feature/<name>/api          Navigation contract, public to other features
feature/<name>/impl         Screen, ViewModel, UiState, Hilt bindings
```

Root Kotlin package: `{{PACKAGE_NAME}}`. Source directories are
`src/main/kotlin/{{PACKAGE_PATH}}/…` — not `src/main/java`.

## 2. Dependency direction

```
app             → feature:*:impl, feature:*:api, data, domain, core:*
feature:*:impl  → own :api, other features' :api, domain, core:ui, core:designsystem
feature:*:api   → navigation only
data            → domain, core:database, core:network, core:datastore, core:common
core:ui         → domain, core:designsystem
core:database   → nothing from domain
core:network    → nothing from domain
core:designsystem → nothing in core
domain          → coroutines and javax.inject only
```

**Forbidden, no exceptions:**

- `domain → android.*`, `androidx.*`, `dagger.*`, or any other module. It is a JVM
  module so its tests run without an emulator. An Android import here is the single
  most damaging change you can make to this codebase.
- `feature:*:impl → data`. Features depend on use cases from `domain`. Only `app`
  wires `data` in, which is what lets you swap an implementation without touching a
  screen.
- `feature:A:impl → feature:B:impl`. Features talk through `api` modules. Shared
  behaviour belongs in `domain` or `core`.
- `core:* → feature:*` or `core:* → app`. Core never depends outward.
- `core:database → domain` or `core:network → domain`. Entities and DTOs are mapped
  to domain models in `data`, which keeps the two source modules independent of
  each other and of the domain.
- Skipping a layer. A ViewModel never touches a DAO, a Retrofit service, or a
  repository; it goes through a use case.

When adding a dependency, check it against this list first. If the edge is not
listed above, it is probably wrong.

## 3. Layer responsibilities

| Layer | Lives in | Owns | Must not |
|---|---|---|---|
| UI | `feature/*/impl`, `core/ui`, `core/designsystem` | Composables, `@Preview`s | Hold business rules or call a repository |
| State holder | `feature/*/impl` | ViewModel, `UiState`, `Action` | Reference Android `View` or `Context` |
| Domain | `domain` | Models, repository interfaces, use cases | Import any framework |
| Data | `data` | Repository implementations, mapping, sync | Expose entity or DTO types upward |
| Sources | `core/database`, `core/network`, `core/datastore` | Room, Retrofit, DataStore | Know that repositories or domain models exist |

Each layer has its own model type. `ItemDto` (wire) maps to `ItemEntity` (storage)
maps to `Item` (domain). All mapping lives in `data/mapper`.

## 4. Use cases

One class per business operation, in `domain/usecase`, invoked with
`operator fun invoke`:

```kotlin
class ObserveItemsUseCase @Inject constructor(
    private val repository: ItemRepository,
) {
    operator fun invoke(): Flow<List<Item>> = repository.observeItems()
}
```

- A use case wraps exactly one operation. If it needs three repositories and a
  branch, it is probably two use cases.
- A thin pass-through use case is fine and expected. Its value is the dependency
  direction, not the logic inside it.
- Business rules belong here, not in a ViewModel and not in a repository.
- Use cases are constructor-injected with `@Inject`; no Hilt module is needed
  because Hilt can construct them directly.

## 5. Adding a feature module

1. Create `feature/<name>/api` and `feature/<name>/impl`.
2. Register both in `settings.gradle.kts`:
   `include(":feature:<name>:api")` and `include(":feature:<name>:impl")`.
3. `api/build.gradle.kts` applies `alias(libs.plugins.{{PREFIX}}.android.library)`
   and holds only the route constant plus a `NavController` extension.
4. `impl/build.gradle.kts` applies `alias(libs.plugins.{{PREFIX}}.android.feature)`,
   which brings Compose, Hilt, `domain`, `core:ui` and `core:designsystem` with it.
   Add `api(projects.feature.<name>.api)` and nothing else unless the feature
   genuinely needs it.
5. Set `namespace = "{{PACKAGE_NAME}}.feature.<name>.impl"`.
6. Add whatever use cases the screen needs to `domain/usecase`.
7. Expose the destination as `NavGraphBuilder.<name>Screen(...)` and call it from
   `{{APP_CLASS}}NavHost`.
8. Add `implementation(projects.feature.<name>.impl)` to `app`.

The `{{FEATURE}}` feature that came with the scaffold is a placeholder showing the
full vertical slice end to end. Replace it with the first real feature rather than
building around it.

## 6. When the module graph should change

Add a `core` module when infrastructure is needed by two or more modules and does
not fit an existing one. Do not add a module for a single consumer — put it where
it is used and extract later. Do not split a module because it is large; split
because it has two distinct responsibilities.

Adding a second app-level target (a wear module, a catalog app) is the usual reason
to grow the graph sideways. Adding features is not: they slot into the existing
`feature/` pattern.

## 7. Verifying the rules still hold

These are cheap and worth running after any structural change:

```bash
grep -rE "^import (android|androidx|dagger)\." domain/src/   # must find nothing
grep -r "projects.data" feature/                             # must find nothing
./gradlew :domain:test                                       # must not need Android
```

The last command is the real test. If `:domain:test` starts needing an emulator or
Robolectric, something has leaked into the domain layer.