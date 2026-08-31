# {{PROJECT_NAME}} — Package Architecture

Owns the package layout, dependency direction, and layer responsibilities for this
project. Build tooling rules live in `build-conventions.md`; class-level patterns
live in `code-patterns.md`.

This project uses **MVVM in a single Gradle module**. That is a deliberate choice
for a project this size: there is no domain layer and no module graph, so there is
very little indirection between a screen and its data.

## 1. Package layout

```
app/src/main/kotlin/{{PACKAGE_PATH}}/
├── model/                 Domain models (plain Kotlin, no annotations)
├── data/
│   ├── local/             Room entities, DAO, database        (if present)
│   ├── remote/            Retrofit DTOs and data source       (if present)
│   ├── preferences/       DataStore-backed settings           (if present)
│   ├── mapper/            Entity/DTO <-> domain mapping
│   └── repository/        Repository interfaces + implementations
├── di/                    Hilt modules
├── common/                Injected dispatcher qualifiers
└── ui/
    ├── theme/             Colour scheme, typography, {{APP_CLASS}}Theme
    ├── components/        Reusable composables
    ├── <feature>/         Screen + ViewModel + UiState, one package per screen
    └── navigation/        Route constants and {{APP_CLASS}}NavHost
```

Root Kotlin package: `{{PACKAGE_NAME}}`. Source directory is
`src/main/kotlin/…` — not `src/main/java`.

## 2. Dependency direction

There is no compiler-enforced boundary in a single module, so these are rules you
have to keep by hand:

```
ui/<feature>  → data/repository, model, ui/components, ui/theme
ui/components → model, ui/theme
data/repository → data/local, data/remote, data/preferences, data/mapper, model
data/local    → model is used only via data/mapper
data/remote   → model is used only via data/mapper
model         → nothing
```

**Do not:**

- Call a DAO or a Retrofit service from a ViewModel. Go through a repository.
- Reference a `ViewModel` from a composable in `ui/components`. Reusable
  composables take data and callbacks.
- Expose `ItemEntity` or `ItemDto` above `data/`. Map to a `model/` type first.
- Put an Android import in `model/`. It should stay plain Kotlin so it can move into
  a `domain` module later without edits.
- Reach from one feature package into another feature package. If two screens need
  the same thing, it belongs in `data/`, `model/`, or `ui/components`.

## 3. Layer responsibilities

| Layer | Lives in | Owns | Must not |
|---|---|---|---|
| UI | `ui/<feature>`, `ui/components`, `ui/theme` | Composables, `@Preview`s | Hold business rules or call data sources |
| State holder | `ui/<feature>` | ViewModel, `UiState`, `Action` | Reference Android `View` or `Context` |
| Data | `data/repository` | Repositories, mapping, sync | Expose storage or wire types upward |
| Sources | `data/local`, `data/remote`, `data/preferences` | Room, Retrofit, DataStore | Know that repositories exist |
| Models | `model/` | Domain types | Carry Room or serialization annotations |

Each layer has its own model type. `ItemDto` (wire) maps to `ItemEntity` (storage)
maps to `Item` (domain), all in `data/mapper`.

## 4. Adding a screen

1. Create `ui/<name>/` with `<Name>UiState.kt`, `<Name>ViewModel.kt`,
   `<Name>Screen.kt`.
2. Add the route constant to `ui/navigation/Routes.kt`.
3. Add `NavGraphBuilder.<name>Screen()` in `ui/navigation/<Name>Navigation.kt`.
4. Call it from `{{APP_CLASS}}NavHost`.

No Gradle changes are needed. That is the main practical benefit of this layout.

The `{{FEATURE}}` screen that came with the scaffold is a placeholder showing the
full vertical slice end to end. Replace it with the first real screen rather than
building around it.

## 5. When to move to a multi-module Clean Architecture layout

The packages above intentionally mirror the boundaries a modular project would
enforce, so the move is mechanical rather than a rewrite. Consider it when:

- the app passes roughly 5 to 8 screens
- more than one or two developers are working in it
- build times become noticeable
- business rules need reuse across screens, or you want unit tests that never touch
  Android
- Kotlin Multiplatform appears on the roadmap

Migration order, most value first:

1. Extract a `domain` module (Kotlin JVM) and move `model/` into it.
2. Move the `ItemRepository` **interface** into `domain/repository`, leaving
   `ItemRepositoryImpl` behind.
3. Add use cases in `domain/usecase` and change each ViewModel to depend on them
   instead of the repository.
4. Split `data/local`, `data/remote`, `data/preferences` into `core:database`,
   `core:network`, `core:datastore`.
5. Move `ui/theme` into `core:designsystem` and `ui/components` into `core:ui`.
6. Move each `ui/<feature>` package into `feature/<name>/impl`, extracting the route
   constant into `feature/<name>/api`.

Steps 1 to 3 give most of the testability benefit and need no change to the module
graph. Stopping there is a reasonable outcome.

Do not create a `domain/` **package** inside this single module and call it clean
architecture: without a module boundary nothing enforces the dependency rule, so it
decays. Either keep the flat layout honestly, or extract real modules.