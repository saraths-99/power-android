# {{PROJECT_NAME}} — Code Patterns

Owns the class-level patterns every new file in this project should follow. Module
boundaries live in `module-architecture.md`; Gradle rules in `build-conventions.md`.

Match these patterns when adding code. They are the shapes already present in the
scaffold, so consistency costs nothing.

## 1. Unidirectional data flow

State flows down, events flow up. Only the ViewModel mutates state.

```
{{DATA_FLOW_DIAGRAM}}
```

A composable never reaches past its ViewModel, and a ViewModel never holds a
`Context`, a `View`, or a navigation decision.

## 2. Screen split: Route and Screen

Every screen is two composables. The stateful one reads the ViewModel; the
stateless one renders and carries the `@Preview`.

```kotlin
@Composable
internal fun ExampleRoute(
    onItemClick: (String) -> Unit,
    modifier: Modifier = Modifier,
    viewModel: ExampleViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    ExampleScreen(
        uiState = uiState,
        onAction = viewModel::onAction,
        onItemClick = onItemClick,
        modifier = modifier,
    )
}

@Composable
internal fun ExampleScreen(
    uiState: ExampleUiState,
    onAction: (ExampleAction) -> Unit,
    onItemClick: (String) -> Unit,
    modifier: Modifier = Modifier,
) { /* rendering only */ }
```

Rules:
- `Modifier` is the first optional parameter and is applied to the root layout.
- `Route` and `Screen` composables are `internal`.
- Reusable composables belong in {{COMPONENT_HOME}}, wrap in `{{APP_CLASS}}Theme`,
  and take data plus callbacks, never a ViewModel.
- Collect with `collectAsStateWithLifecycle()`, not `collectAsState()`.

## 3. UiState is a sealed interface

Model every state the screen can be in, so `when` is exhaustive and no case is
missed. Do not use a single data class with `isLoading` and `error` fields that can
contradict each other.

```kotlin
sealed interface ExampleUiState {
    data object Loading : ExampleUiState
    data object Empty : ExampleUiState
    data class Success(val items: List<Item>) : ExampleUiState
    data class Error(val message: String) : ExampleUiState
}

sealed interface ExampleAction {
    data object Refresh : ExampleAction
}
```

User intents go through one `onAction(action)` entry point rather than a separate
lambda per interaction.

## 4. ViewModel shape

```kotlin
@HiltViewModel
class ExampleViewModel @Inject constructor(
{{VM_CONSTRUCTOR}}) : ViewModel() {

    val uiState: StateFlow<ExampleUiState> = {{VM_SOURCE}}
        .map<List<Item>, ExampleUiState> { items ->
            if (items.isEmpty()) ExampleUiState.Empty else ExampleUiState.Success(items)
        }
        .catch { emit(ExampleUiState.Error(it.message ?: "Something went wrong")) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = ExampleUiState.Loading,
        )

    fun onAction(action: ExampleAction) {
        when (action) {
            ExampleAction.Refresh -> refresh()
        }
    }
}
```

Use `SharingStarted.WhileSubscribed(5_000)` so the stream survives a configuration
change without leaking. Derive state from the incoming flow rather than holding a
mutable copy alongside it.

{{VM_DEPENDENCY_RULE}}
{{USE_CASE_SECTION}}## 5. Repositories expose Flow

```kotlin
interface ItemRepository {
    fun observeItems(): Flow<List<Item>>
    suspend fun upsertItem(item: Item)
    suspend fun sync(): Boolean
}
```

Reads return `Flow`, never a suspend getter that returns a snapshot. Writes are
`suspend`. The interface is public and lives in {{REPO_INTERFACE_HOME}}; the
implementation is `internal` and bound with `@Binds` in {{REPO_BINDING_HOME}}.

Where a local database is present, it is the source of truth: reads come from Room
and `sync()` refreshes it from the network. The UI never waits on the network to
render.

## 6. Inject dispatchers

Never reference `Dispatchers.IO` directly. Inject it so tests can substitute a test
dispatcher.

```kotlin
internal class DefaultRepository @Inject constructor(
    private val dao: ItemDao,
    @Dispatcher(AppDispatchers.IO) private val ioDispatcher: CoroutineDispatcher,
) : ItemRepository {

    override suspend fun upsertItem(item: Item) {
        withContext(ioDispatcher) { dao.upsert(item.asEntity()) }
    }
}
```

## 7. Hilt

- Application-scoped bindings go in `@InstallIn(SingletonComponent::class)` modules.
- Use `@Binds` in an `internal interface` module for interface-to-implementation.
- Use `@Provides` in an `internal object` module for types you construct.
- Keep DI modules in a `di` package inside the module that owns the types.
- ViewModels are `@HiltViewModel` with constructor injection, obtained via
  `hiltViewModel()`.

## 8. Naming

| Thing | Pattern |
|---|---|
| Screen composables | `<Feature>Route`, `<Feature>Screen` |
| State and intents | `<Feature>UiState`, `<Feature>Action` |
| Repository | `<Thing>Repository` interface, `<Thing>RepositoryImpl` implementation |
{{USE_CASE_NAMING_ROW}}| Room entity / DAO | `<Thing>Entity`, `<Thing>Dao` |
| Wire model | `<Thing>Dto` |
| Remote data source | `<Thing>RemoteDataSource` |
| Mapper | `toDomain()`, `toEntity()` |
| Route constant | `<FEATURE>_ROUTE` |
| Hilt module | `<Area>Module` |

When two mappers with the same name would be imported into one file, give one a
distinct name (`toItemEntity()`) rather than fully qualifying it.

## 9. Tests

- Hand-written test doubles, no mocking library. A double that implements the real
  interface fails to compile when the interface changes; a mock silently drifts.
- Put shared doubles in {{TEST_DOUBLE_HOME}}.
- Use `MainDispatcherRule` for ViewModel tests and Turbine to assert on `Flow`
  emissions.
- Test the stateless `Screen` composable, not the `Route`, so no ViewModel or Hilt
  graph is needed.
- Unit tests in `src/test`, instrumented tests in `src/androidTest`, reserved for
  critical flows.

## 10. Resources and strings

User-visible text goes in the owning module's `res/values/strings.xml`, referenced
with `stringResource(R.string.…)`. Prefix feature strings with the feature name
(`feature_{{FEATURE}}_title`) so merged resources never collide. Every `Icon` and
image needs a `contentDescription`, or an explicit `null` when it is decorative.

Colours and typography come from `{{APP_CLASS}}Theme` and
`MaterialTheme.colorScheme` / `MaterialTheme.typography`. Do not hardcode a `Color`
in a feature module.