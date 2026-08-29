# {{APP_NAME}}

Scaffolded by the **Android Project - Initial Setup** Kiro power.
Architecture: **Clean Architecture + MVVM, multi module**.

## Structure

```
app/                        Entry point, DI wiring, NavHost, theme selection
domain/                     Pure Kotlin: models, repository interfaces, use cases
data/                       Repository implementations and mappers
core/common/                Injected dispatcher qualifiers
core/designsystem/          Theme, colour scheme, typography
core/ui/                    Reusable composables
{{OPTIONAL_MODULES}}{{FEATURE_TREE_LINE}}build-logic/convention/     Convention plugins ({{PREFIX}}.*) shared by all modules
gradle/libs.versions.toml   Single source of truth for dependency versions
```

## Dependency rules

```
app             -> feature:*:impl, feature:*:api, data, domain, core:*
feature:*:impl  -> feature:*:api, domain, core:ui, core:designsystem
feature:*:api   -> navigation only
data            -> domain, core:common{{DATA_RULE_MODULES}}
{{DATA_SOURCE_RULES}}domain          -> coroutines and javax.inject only
```

Three rules make this work, and breaking any of them undoes the benefit:

1. **`domain` never depends on Android.** It is a JVM module, so its tests run
   without an emulator or Robolectric.
2. **Feature modules never depend on `data`.** They see use cases from `domain`.
   `data` is wired in by `app` alone.
3. **Features never depend on another feature's `impl`.** They talk through
   `api` modules, which only carry navigation contracts.

## How data flows

```
{{FEATURE_CLASS}}Screen -> {{FEATURE_CLASS}}ViewModel -> ObserveItemsUseCase -> ItemRepository
                                                          (interface, :domain)
                                                                 |
                                                     ItemRepositoryImpl (:data)
                                                                 |
                                                        DAO / remote source
```

The ViewModel depends on use cases, so it has no idea whether data comes from
Room, the network, or a fake in a test.

## Build

```bash
./gradlew :app:assembleDebug     # debug APK
./gradlew test                   # unit tests across all modules
./gradlew :domain:test           # domain tests, no Android required
./gradlew build                  # everything, including lint and release
```

If `./gradlew` is missing, generate the wrapper first:

```bash
gradle wrapper --gradle-version {{GRADLE_VERSION}}
```

Opening the project in Android Studio also creates the wrapper.

## Adding a feature

1. Create `feature/<name>/api` and `feature/<name>/impl`.
2. Register both in `settings.gradle.kts`.
3. In `impl`, apply `alias(libs.plugins.{{PREFIX}}.android.feature)`; the
   convention plugin supplies `domain`, `core:ui` and `core:designsystem`.
4. Add use cases to `domain` for anything the screen needs.
5. Contribute the destination from `NavGraphBuilder.<name>Screen()` and call it
   from `{{APP_CLASS}}NavHost`.

## Before you ship

- Replace the placeholder launcher icons in `app/src/main/res/mipmap-*`
  (Android Studio: right-click `res` > New > Image Asset).
- Set your brand colours in `core/designsystem`.
{{SHIP_NETWORK_LINE}}- Add a release signing config in `app/build.gradle.kts`.
- Rename the sample `Item` model to something from your own domain.
