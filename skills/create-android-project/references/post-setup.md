# After scaffolding

What to hand the user, and what to offer to do next.

## Placeholders that must be replaced

Say these out loud rather than leaving them to be discovered.

| What | Where | Why it matters |
|---|---|---|
| Launcher icons | `app/src/main/res/mipmap-*/ic_launcher*.png` | Flat blue squares. Real PNGs so the build resolves, but not shippable. Android Studio: right-click `res` > New > Image Asset. |
| Brand colours | `core/designsystem/…/theme/Color.kt` or `ui/theme/Color.kt` | Placeholder palette. [Material Theme Builder](https://material-foundation.github.io/material-theme-builder/) generates a full token set. |
| `BASE_URL` | `core/network/…/retrofit/` or `data/remote/retrofit/` | Points at `https://example.com/api/`. Sync fails until this is real. |
| `Item` model | `domain/model/` or `model/` | A stand-in. Rename to something from the user's domain. |
| Release signing | `app/build.gradle.kts` | No signing config is generated. `assembleRelease` produces an unsigned APK. |

## Not generated on purpose

- **Gradle wrapper JAR** — a binary. Run `gradle wrapper --gradle-version <version>`
  or open the project in Android Studio (see SKILL.md Step 6).
- **Test cases** — only test *helpers*. Tests belong to the behaviour the user is
  about to write, not to a template.
- **CI config** — depends on their provider.
- **`local.properties`** — machine-specific, and gitignored.

## Renaming the sample model

This is usually the first real task, and it is worth offering. For `Item` →
`Trail` the touch points are:

**`mvvm`:** `model/Item.kt`, `data/local/model/ItemEntity.kt`,
`data/local/dao/ItemDao.kt`, `data/remote/model/ItemDto.kt`,
`data/mapper/ItemMappers.kt`, `data/repository/ItemRepository*.kt`,
`ui/components/ItemCard.kt`, the feature's `UiState`, plus the seeded rows in the
database callback.

**`clean-mvvm`:** the same list spread across `domain/`, `data/`,
`core/database/`, `core/network/`, `core/ui/`, and every use case in
`domain/usecase/`.

Two things a rename must not miss:

- `@Entity(tableName = "items")` and every `@Query` string that names the table.
  These are strings, so the compiler will not catch them, but Room's annotation
  processor will.
- The `INSERT INTO items …` statement in the seed callback.

Room's KSP processor fails the build on a table-name mismatch, so a full rename
is verifiable with `./gradlew :app:assembleDebug`.

## Adding a second feature

The steps below cover the module/Gradle wiring a new feature needs — they do not
cover the per-layer code itself. For the UiState, ViewModel, Route/Content,
Repository (and for `clean-mvvm`, UseCase and repository interface) templates,
follow `single-module-mvvm-reference.md` (mvvm) or `clean-mvvm-reference.md`
(clean-mvvm), in this same `references/` directory, once the module/package below
exists — they give copy-adaptable templates for exactly that layer split.

### `clean-mvvm`

1. `feature/<name>/api/build.gradle.kts` with the `android.library` convention,
   namespace `<pkg>.feature.<name>.api`, and `api(libs.androidx.navigation.compose)`.
2. `feature/<name>/impl/build.gradle.kts` with the `android.feature` convention
   and `api(projects.feature.<name>.api)`. The convention plugin supplies
   `domain`, `core:ui` and `core:designsystem`.
3. Register both in `settings.gradle.kts`.
4. Route constant and `navigateTo<Name>()` in the api module.
5. `<Name>UiState.kt`, `<Name>ViewModel.kt`, `<Name>Screen.kt`, and
   `navigation/<Name>Navigation.kt` in impl.
6. Any new business operation gets a use case in `domain/usecase/`.
7. Add `implementation(projects.feature.<name>.impl)` to `app` and call the new
   `NavGraphBuilder.<name>Screen()` from the NavHost.

### `mvvm`

1. New package `ui/<name>/` with `<Name>UiState.kt`, `<Name>ViewModel.kt`,
   `<Name>Screen.kt`.
2. Route constant in `ui/navigation/Routes.kt`.
3. `NavGraphBuilder.<name>Screen()` in `ui/navigation/<Name>Navigation.kt`.
4. Call it from the NavHost.

No Gradle changes either way for `mvvm`.

## Wiring up navigation between screens

The generated NavHost passes an `onItemClick` that does nothing:

```kotlin
{{feature}}Screen(
    onItemClick = {
        // TODO: navigate to a detail destination once you add one.
    },
)
```

Once a detail screen exists, this becomes `navController.navigateToDetail(it)`.
In `clean-mvvm`, `navigateToDetail` comes from the detail feature's `api` module,
which is exactly why the api/impl split exists.

## Adding error typing

The generated code maps a `Throwable` message straight into
`<Feature>UiState.Error`. That is fine to start and deliberately minimal. When
error handling gets real, introduce a domain error type:

```kotlin
// domain
sealed interface AppError {
    data class Network(val message: String) : AppError
    data class Database(val message: String) : AppError
    data object Unauthorized : AppError
}
```

Have repositories return `Result<T>` or a `Try<T>` carrying `AppError`, and map to
user-facing strings in the ViewModel. Keep the mapping in the ViewModel: domain
errors should not know about string resources.

## Bumping versions

Everything lives in `gradle/libs.versions.toml`. One constraint that bites:

```toml
kotlin = "1.9.22"
androidxComposeCompiler = "1.5.10"
```

These are a matched pair. Bumping Kotlin without the Compose compiler fails the
build with a version-mismatch error. The mapping is at
https://developer.android.com/jetpack/androidx/releases/compose-kotlin

Moving to Kotlin 2.x is a larger change: the Compose compiler ships as a Gradle
plugin (`org.jetbrains.kotlin.plugin.compose`) and `composeOptions
.kotlinCompilerExtensionVersion` goes away. Worth doing, but as its own task.

## Verifying the dependency rules hold

For `clean-mvvm`, these are the checks worth running after any structural change:

```bash
# domain must be framework-free
grep -rE "^import (android|androidx|dagger)\." domain/src/ && echo "RULE BROKEN"

# features must not reach into the data layer
grep -r "projects.data" feature/ && echo "RULE BROKEN"

# domain tests must run without Android
./gradlew :domain:test
```

The last one is the real test: if `:domain:test` needs an emulator, something has
leaked into the domain layer.
