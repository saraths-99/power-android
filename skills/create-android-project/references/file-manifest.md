# File manifest — which template goes where

Copy each template from `assets/templates/` to the destination path, substituting
all tokens (see `references/token-map.md`). Kotlin destinations live under
`<module>/src/main/kotlin/<package-as-path>/<FileName>.kt`, where the package is
the resolved value of the listed `PKG_*` token and `<package-as-path>` is that
package with dots replaced by slashes.

Filenames marked with a token (e.g. `{FEATURE_CLASS}Screen.kt`) use the resolved
identifier. Rows tagged `[flag]` are created only when that config flag is true.

## Kotlin source (`assets/templates/kotlin/`)

| Template | Destination filename | Package token | Condition |
|---|---|---|---|
| `T_MODEL_ITEM.kt` | `Item.kt` | `PKG_MODEL` | always |
| `T_MODEL_USER_DATA.kt` | `UserData.kt` | `PKG_MODEL` | `[datastore]` |
| `T_MODEL_DARK_THEME.kt` | `DarkThemeConfig.kt` | `PKG_MODEL` | `[datastore]` |
| `T_DISPATCHERS.kt` | `AppDispatchers.kt` | `PKG_DISPATCHERS` | always |
| `T_DISPATCHERS_MODULE.kt` | `DispatchersModule.kt` | `PKG_DISPATCHERS_DI` | always |
| `T_DB_ENTITY.kt` | `ItemEntity.kt` | `PKG_DB` (+`.model`) | `[database]` |
| `T_DB_DAO.kt` | `ItemDao.kt` | `PKG_DB` (+`.dao`) | `[database]` |
| `T_DB_DATABASE.kt` | `{APP_CLASS}Database.kt` | `PKG_DB` | `[database]` |
| `T_DB_MODULE.kt` | `DatabaseModule.kt` | `PKG_DB_DI` | `[database]` |
| `T_NET_DTO.kt` | `ItemDto.kt` | `PKG_NET` (+`.model`) | `[network]` |
| `T_NET_DATASOURCE.kt` | `ItemRemoteDataSource.kt` | `PKG_NET` | `[network]` |
| `T_NET_RETROFIT.kt` | `RetrofitItemRemoteDataSource.kt` | `PKG_NET` (+`.retrofit`) | `[network]` |
| `T_NET_MODULE.kt` | `NetworkModule.kt` | `PKG_NET_DI` | `[network]` |
| `T_PREFS_DATASOURCE.kt` | `UserPreferencesDataSource.kt` | `PKG_PREFS` | `[datastore]` |
| `T_PREFS_MODULE.kt` | `DataStoreModule.kt` | `PKG_PREFS_DI` | `[datastore]` |
| `T_ITEM_MAPPERS_*` (head+body) | `ItemMappers.kt` | `PKG_MAPPER` | `[database]` |
| `T_PREFS_MAPPERS.kt` | `PreferencesMappers.kt` | `PKG_MAPPER` | `[datastore]` |
| `T_REPO_ITEM.kt` | `ItemRepository.kt` | `PKG_REPO` | always |
| `T_REPO_ITEM_IMPL_OFFLINE.kt` | `ItemRepositoryImpl.kt` | `PKG_REPO_IMPL` | `[database]` |
| `T_REPO_ITEM_IMPL_MEMORY.kt` | `ItemRepositoryImpl.kt` | `PKG_REPO_IMPL` | when **not** `[database]` |
| `T_REPO_USER.kt` | `UserDataRepository.kt` | `PKG_REPO` | `[datastore]` |
| `T_REPO_USER_IMPL.kt` | `UserDataRepositoryImpl.kt` | `PKG_REPO_IMPL` | `[datastore]` |
| `T_REPO_MODULE.kt` | `RepositoryModule.kt` | `PKG_DATA_DI` | always |
| `T_USE_CASE.kt` | one file per use case (see below) | `PKG_USECASE` | `clean-mvvm` only |
| `T_THEME_COLOR.kt` | `Color.kt` | `PKG_THEME` | always |
| `T_THEME_TYPE.kt` | `Type.kt` | `PKG_THEME` | always |
| `T_THEME.kt` | `Theme.kt` | `PKG_THEME` | always |
| `T_ITEM_CARD.kt` | `ItemCard.kt` | `PKG_COMPONENTS` | always |
| `T_STATE_VIEWS.kt` | `StateViews.kt` | `PKG_COMPONENTS` | always |
| `T_FEATURE_UISTATE.kt` | `{FEATURE_CLASS}UiState.kt` | `PKG_FEATURE` | always |
| `T_FEATURE_VIEWMODEL_MVVM.kt` | `{FEATURE_CLASS}ViewModel.kt` | `PKG_FEATURE` | `mvvm` |
| `T_FEATURE_VIEWMODEL_CLEAN.kt` | `{FEATURE_CLASS}ViewModel.kt` | `PKG_FEATURE` | `clean-mvvm` |
| `T_FEATURE_SCREEN.kt` | `{FEATURE_CLASS}Screen.kt` | `PKG_FEATURE` | always |
| `T_FEATURE_NAV.kt` | `{FEATURE_CLASS}Navigation.kt` | `PKG_FEATURE_NAV` | always |
| `T_FEATURE_ROUTE.kt` | `Routes.kt` (mvvm) / `{FEATURE_CLASS}Navigation.kt` (clean, in `api`) | `PKG_FEATURE_API` | always |
| `T_NAV_HOST.kt` | `{APP_CLASS}NavHost.kt` | `PKG_NAV` | always |
| `T_APP_ROOT.kt` | `{APP_ROOT}.kt` | `PKG_APP_UI` | always |
| `T_APPLICATION.kt` | `{APP_CLASS}Application.kt` | `PKG` | always |
| `T_MAIN_ACTIVITY_SETTINGS.kt` + `T_MAIN_ACTIVITY_VM.kt` | `MainActivity.kt` + `MainActivityViewModel.kt` | `PKG` | `[datastore]` |
| `T_MAIN_ACTIVITY_PLAIN.kt` | `MainActivity.kt` | `PKG` | when **not** `[datastore]` |
| `T_TEST_DISPATCHER_RULE.kt` | `MainDispatcherRule.kt` (test source, +`.util`) | `PKG_TESTING` | `[testUtilities]` |
| `T_TEST_FAKE_REPO.kt` | `FakeItemRepository.kt` (test source, +`.repository`) | `PKG_TESTING` | `[testUtilities]` |

For `mvvm`, module = `app`. For `clean-mvvm`, module is the one named in
`references/project-structure.md` §2 for that role (e.g. `domain`, `data`,
`core/database`, `feature/<f>/impl`).

### Use cases (`clean-mvvm` only, `T_USE_CASE.kt` → `PKG_USECASE`)

One file per operation. Always: `ObserveItemsUseCase`, `ObserveItemUseCase`,
`UpsertItemUseCase`, `DeleteItemUseCase`, `SyncItemsUseCase`. With `[datastore]`
also: `ObserveUserDataUseCase`, `SetDarkThemeConfigUseCase`,
`SetDynamicColorPreferenceUseCase`. Each wraps the matching repository call with
`operator fun invoke`.

## Resources and manifest (app module)

| File | Source | Notes |
|---|---|---|
| `app/src/main/AndroidManifest.xml` | `T_MANIFEST.xml` | add the INTERNET `<uses-permission>` only if `[network]` |
| `app/src/main/res/values/strings.xml` | build inline | `app_name` = `{APP_NAME_XML}`; append `T_FEATURE_STRINGS.xml.fragment` when the feature strings live in the app module (mvvm) |
| `app/src/main/res/values/themes.xml` | `T_THEMES_XML.xml` | |
| `app/proguard-rules.pro` | `T_PROGUARD_HEAD.pro` (+ `T_PROGUARD_OKHTTP.pro` if `[network]`) | |
| launcher icons | see SKILL.md Step 5 | vector adaptive icon, not PNG |

For `clean-mvvm`, the feature strings go in
`feature/<f>/impl/src/main/res/values/strings.xml` instead.

## Root / build files

| File | Source | Notes |
|---|---|---|
| `settings.gradle.kts` | `root/SETTINGS_GRADLE.gradle.kts` | mvvm: only `include(":app")`. clean: `include` `:app :domain :data`, each present `:core:*`, `:feature:<f>:api` + `:impl`, and `includeBuild("build-logic")` |
| `build.gradle.kts` (root) | `root/ROOT_BUILD_GRADLE.gradle.kts` | |
| `gradle.properties` | `root/GRADLE_PROPERTIES.properties` | |
| `gradle/libs.versions.toml` | `root/VERSION_CATALOG_BASE.toml` (+ `VERSION_CATALOG_CONVENTION.toml` appended for clean) | |
| `gradle/wrapper/gradle-wrapper.properties` | `root/GRADLE_WRAPPER_PROPERTIES.properties` | |
| `.gitignore` | `root/GITIGNORE.gitignore` | |
| `app/build.gradle.kts` | `app-build/T_APP_BUILD_MVVM.gradle.kts` or `T_APP_BUILD_CLEAN.gradle.kts` | assemble the plugin + dependency lists per the flags (see project-structure.md §3) |
| `README.md` | `readme/README_MVVM.md` or `README_CLEAN.md` | |

## build-logic (clean-mvvm only)

Copy `build-logic/BUILD_LOGIC_SETTINGS.gradle.kts` and
`build-logic/BUILD_LOGIC_CONVENTION_BUILD.gradle.kts`, and every file in
`convention-sources/` into
`build-logic/convention/src/main/kotlin/`.

## Emitted steering (both architectures)

Render into the new project's `.kiro/steering/`:

| Destination | Source |
|---|---|
| `.kiro/steering/module-architecture.md` | `assets/steering/module-architecture-<arch>.md` |
| `.kiro/steering/build-conventions.md` | `assets/steering/build-conventions-<arch>.md` |
| `.kiro/steering/code-patterns.md` | `assets/steering/code-patterns.md` |

These carry the project's conventions forward for later sessions. They contain
their own `{{TOKEN}}` set (e.g. `PROJECT_NAME`, `PACKAGE_NAME`, `PACKAGE_PATH`,
`DATA_FLOW_DIAGRAM`, and clean-only use-case sections) — substitute those too.
