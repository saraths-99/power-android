---
inclusion: auto
name: architecture
description: Android architecture patterns, layer responsibilities, and data flow. Use when discussing or implementing architectural decisions, layer boundaries, or data flow patterns.
---

# Architecture Patterns

This power generates projects following two architectural approaches: **MVVM** for simplicity and **Clean Architecture + MVVM** for scalability. Both share core principles but differ in module organization and layer separation.

## Core Principles (Both Architectures)

### Unidirectional Data Flow
State flows down from ViewModels to UI. Events flow up from UI to ViewModels. Only ViewModels mutate state.

```
User Action → UI Event → ViewModel → State Update → UI Renders New State
```

**Benefits:**
- Predictable state changes
- Easy to test (no circular dependencies)
- Clear ownership (ViewModel owns state)
- No race conditions from multiple mutation sources

### Offline-First
The local database is the single source of truth. Network operations update the database; UI reads from database.

```
UI → ViewModel → Repository → Room Database (source of truth)
                              ↑
                         Network sync updates database
```

**Benefits:**
- App works offline immediately
- Consistent data access pattern
- UI never waits on network
- Network failures don't break UI

### Separation of Concerns
Each layer has a single responsibility and depends only on layers below it.

**Dependency Rule:** Outer layers depend on inner layers, never the reverse.
- UI depends on ViewModels
- ViewModels depend on repositories (MVVM) or use cases (Clean)
- Repositories depend on data sources
- Domain layer has no dependencies (Clean Architecture only)

## MVVM Architecture (Single Module)

### Layer Diagram
```
┌─────────────────────────────────────┐
│           UI Layer                  │
│  (Compose Screens + ViewModels)     │
└──────────────┬──────────────────────┘
               │ depends on
┌──────────────▼──────────────────────┐
│         Repository Layer            │
│    (Interface + Implementation)     │
└──────────────┬──────────────────────┘
               │ depends on
┌──────────────▼──────────────────────┐
│        Data Sources Layer           │
│   (Room DAO, Retrofit, DataStore)   │
└─────────────────────────────────────┘
```

### Layer Responsibilities

#### UI Layer (`ui/`)
**What it contains:**
- Composable functions (Screens and reusable components)
- ViewModels (state management)
- UI State models (sealed interfaces)
- Navigation graphs
- Material 3 theme

**Responsibilities:**
- Render state as UI
- Capture user interactions
- Navigate between screens
- Collect state from ViewModels with Lifecycle awareness

**Rules:**
- Never access repositories or data sources directly
- Never hold Android framework types (`Context`, `Activity`) in ViewModels
- Composables receive data via parameters, not ViewModels (except Route composables)
- All state is immutable from UI's perspective

**Example:**
```kotlin
@Composable
internal fun HomeRoute(
    viewModel: HomeViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    HomeScreen(
        uiState = uiState,
        onAction = viewModel::onAction
    )
}
```

#### Repository Layer (`data/repository/`)
**What it contains:**
- Repository interfaces (public contracts)
- Repository implementations (`internal`)
- Coordination logic between data sources

**Responsibilities:**
- Abstract data source details from ViewModels
- Coordinate multiple data sources (database + network)
- Implement business logic for data operations
- Transform entities/DTOs to domain models
- Handle sync strategies (offline-first)

**Rules:**
- Interfaces are public; implementations are `internal`
- Return `Flow` for observed data, `suspend` functions for operations
- Database is always source of truth
- Network calls update database, not return directly to UI

**Example:**
```kotlin
interface ItemRepository {
    fun observeItems(): Flow<List<Item>>
    suspend fun refreshItems(): Result<Unit>
}

internal class ItemRepositoryImpl @Inject constructor(
    private val dao: ItemDao,
    private val remoteDataSource: ItemRemoteDataSource,
    @Dispatcher(IO) private val ioDispatcher: CoroutineDispatcher
) : ItemRepository {
    override fun observeItems(): Flow<List<Item>> =
        dao.observeAll().map { entities -> entities.map { it.toDomain() } }
    
    override suspend fun refreshItems(): Result<Unit> =
        withContext(ioDispatcher) {
            try {
                val dtos = remoteDataSource.fetchItems()
                dao.upsertAll(dtos.map { it.toEntity() })
                Result.success(Unit)
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
}
```

#### Data Sources Layer (`data/local/`, `data/remote/`, `data/preferences/`)
**What it contains:**
- Room DAOs and entities
- Retrofit services and DTOs
- DataStore accessors
- Hilt modules for providing instances

**Responsibilities:**
- Execute specific storage/network operations
- Define data schemas (entities, DTOs)
- Provide type-safe access to data stores
- No business logic (pure CRUD operations)

**Rules:**
- DAOs return `Flow` for observable queries, `suspend` for mutations
- Entities and DTOs are internal to data layer
- Remote data sources are interfaces, bound via Hilt
- Each data source lives in its own package with DI module

### Data Flow Example (MVVM)

**User refreshes a list:**
```
1. User swipes to refresh
2. Screen calls viewModel.onAction(Refresh)
3. ViewModel calls repository.refreshItems()
4. Repository fetches from network (RemoteDataSource)
5. Repository writes to database (DAO)
6. DAO emits new data through Flow
7. Repository transforms entities to domain models
8. ViewModel transforms to UI state
9. Screen recomposes with new state
```

## Clean Architecture + MVVM (Multi-Module)

### Layer Diagram
```
┌─────────────────────────────────────┐
│      Presentation Layer             │
│  (Feature Modules: Screen + VM)     │
└──────────────┬──────────────────────┘
               │ depends on
┌──────────────▼──────────────────────┐
│        Domain Layer                 │
│  (Use Cases + Models + Interfaces)  │  ← Pure Kotlin, No Android
└──────────────┬──────────────────────┘
               │ depends on (interfaces only)
┌──────────────▼──────────────────────┐
│         Data Layer                  │
│  (Repository Impl + Mappers)        │
└──────────────┬──────────────────────┘
               │ depends on
┌──────────────▼──────────────────────┐
│       Data Sources Layer            │
│  (Database, Network, DataStore)     │
└─────────────────────────────────────┘
```

### Layer Responsibilities

#### Presentation Layer (`feature/*` modules)
**What it contains:**
- Screens and Route composables
- ViewModels
- UI State and Action models
- Feature-specific navigation

**Responsibilities:**
- Same as MVVM UI layer
- Depends on domain layer for models and use cases
- Each feature is its own module

**Rules:**
- Same as MVVM UI layer
- ViewModels call use cases, not repositories directly
- No direct access to data or database modules

**Example:**
```kotlin
@HiltViewModel
class HomeViewModel @Inject constructor(
    private val getItemsUseCase: GetItemsUseCase,
    private val refreshItemsUseCase: RefreshItemsUseCase
) : ViewModel() {
    val uiState: StateFlow<HomeUiState> = getItemsUseCase()
        .map { items -> 
            if (items.isEmpty()) HomeUiState.Empty 
            else HomeUiState.Success(items) 
        }
        .stateIn(viewModelScope, WhileSubscribed(5_000), HomeUiState.Loading)
    
    fun onAction(action: HomeAction) {
        when (action) {
            HomeAction.Refresh -> viewModelScope.launch {
                refreshItemsUseCase()
            }
        }
    }
}
```

#### Domain Layer (`core/domain` module)
**What it contains:**
- Domain models (business entities)
- Repository interfaces (contracts)
- Use cases (business logic)

**Responsibilities:**
- Define business rules
- Encapsulate single business operations
- Depend on nothing (pure Kotlin)
- Define contracts for data layer

**Rules:**
- **Pure Kotlin module** — No Android framework dependencies
- Uses `kotlin("jvm")` plugin, not Android Library
- One use case = one business operation
- Use cases call repository interfaces
- All types are public (consumed by presentation and data)

**Example:**
```kotlin
// Domain Model
data class Item(
    val id: String,
    val title: String,
    val description: String,
    val timestamp: Long
)

// Repository Interface
interface ItemRepository {
    fun observeItems(): Flow<List<Item>>
    suspend fun refreshItems(): Result<Unit>
}

// Use Case
class GetItemsUseCase @Inject constructor(
    private val repository: ItemRepository
) {
    operator fun invoke(): Flow<List<Item>> = repository.observeItems()
}

class RefreshItemsUseCase @Inject constructor(
    private val repository: ItemRepository
) {
    suspend operator fun invoke(): Result<Unit> = repository.refreshItems()
}
```

#### Data Layer (`core/data` module)
**What it contains:**
- Repository implementations
- Mappers between entities/DTOs and domain models
- Coordination logic
- Hilt bindings for repositories

**Responsibilities:**
- Implement repository interfaces from domain
- Transform data layer models to domain models
- Coordinate multiple data sources
- Same offline-first strategy as MVVM

**Rules:**
- Implementations are `internal`
- Depends on domain (interfaces), database, network, datastore modules
- All mappers live here
- Bound to domain interfaces via `@Binds`

**Example:**
```kotlin
internal class ItemRepositoryImpl @Inject constructor(
    private val dao: ItemDao,
    private val remoteDataSource: ItemRemoteDataSource,
    @Dispatcher(IO) private val ioDispatcher: CoroutineDispatcher
) : ItemRepository {
    override fun observeItems(): Flow<List<Item>> =
        dao.observeAll().map { entities -> entities.map { it.toDomain() } }
    
    override suspend fun refreshItems(): Result<Unit> =
        withContext(ioDispatcher) {
            // Same implementation as MVVM
        }
}

// Mapper extensions
internal fun ItemEntity.toDomain() = Item(
    id = id,
    title = title,
    description = description,
    timestamp = timestamp
)
```

#### Data Sources Layer (`core/database`, `core/network`, `core/datastore`)
**Same as MVVM** but in separate modules for:
- Parallel compilation
- Clear dependency boundaries
- Independent versioning
- Easier testing

### Data Flow Example (Clean Architecture)

**User refreshes a list:**
```
1. User swipes to refresh
2. Screen calls viewModel.onAction(Refresh)
3. ViewModel calls refreshItemsUseCase()
4. Use case calls repository.refreshItems()
5. Repository (impl in core/data) fetches from network
6. Repository writes to database
7. DAO emits to repository
8. Repository maps entities to domain models
9. Use case returns domain models
10. ViewModel transforms to UI state
11. Screen recomposes
```

## Dependency Injection with Hilt

### Module Organization

#### MVVM (Single Module)
All DI modules in `di/` subpackages:
```
data/local/di/DatabaseModule.kt
data/remote/di/NetworkModule.kt
data/preferences/di/DataStoreModule.kt
data/repository/di/RepositoryModule.kt
core/common/di/DispatchersModule.kt
```

#### Clean Architecture
One DI module per core module:
```
core/database/di/DatabaseModule.kt
core/network/di/NetworkModule.kt
core/datastore/di/DataStoreModule.kt
core/data/di/RepositoryModule.kt
core/common/di/DispatchersModule.kt
```

### Binding Patterns

**Interface to Implementation:**
```kotlin
@Module
@InstallIn(SingletonComponent::class)
internal interface RepositoryModule {
    @Binds
    fun bindItemRepository(impl: ItemRepositoryImpl): ItemRepository
}
```

**Constructed Types:**
```kotlin
@Module
@InstallIn(SingletonComponent::class)
internal object DatabaseModule {
    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase =
        Room.databaseBuilder(context, AppDatabase::class.java, "app-database")
            .build()
    
    @Provides
    fun provideItemDao(database: AppDatabase): ItemDao =
        database.itemDao()
}
```

## Testing Strategy

### Unit Tests (Both Architectures)
- **ViewModels:** Test state transformations with fake repositories/use cases
- **Repositories:** Test coordination logic with fake DAOs and data sources
- **Use Cases (Clean):** Test business logic with fake repositories

### Test Doubles
Hand-written test implementations that implement real interfaces:
```kotlin
class TestItemRepository : ItemRepository {
    private val items = MutableStateFlow<List<Item>>(emptyList())
    
    override fun observeItems(): Flow<List<Item>> = items.asStateFlow()
    
    override suspend fun refreshItems(): Result<Unit> {
        // Test implementation
        return Result.success(Unit)
    }
    
    fun setItems(newItems: List<Item>) {
        items.value = newItems
    }
}
```

**Why hand-written?**
- Compile-time safety (changes to interface break the test double)
- No mocking library magic
- Easy to understand and debug
- Shared across tests in `core/testing` module

## Common Anti-Patterns to Avoid

### Don't: ViewModels Calling ViewModels
❌ `HomeViewModel` calls `ProfileViewModel.loadData()`
✅ Shared logic goes in repositories or use cases

### Don't: Repositories Returning UI State
❌ `repository.getItems(): Flow<ItemUiState>`
✅ `repository.getItems(): Flow<List<Item>>` (domain models)

### Don't: UI Directly Accessing Data Sources
❌ `Screen` calls `dao.getItems()`
✅ `Screen` → `ViewModel` → `Repository` → `DAO`

### Don't: Domain Layer with Android Dependencies (Clean)
❌ `UseCase` depends on `Context`, `ViewModel`, `LiveData`
✅ `UseCase` is pure Kotlin, depends only on domain interfaces

### Don't: Multiple Sources of Truth
❌ Network returns data directly to UI, separate from database
✅ Network updates database, UI observes database only

### Don't: Mutable State in UI
❌ `Screen` modifies `List<Item>` and passes it back
✅ `Screen` emits events, ViewModel produces new immutable state

## When to Choose Which Architecture

### Choose MVVM When:
- Building a prototype or MVP
- Solo developer or small team
- Short-lived project (< 6 months active development)
- Simple feature set (< 5 major features)
- Learning Android development

### Choose Clean Architecture When:
- Large, long-lived application
- Team of 3+ developers
- Complex business logic
- Multiple feature teams working in parallel
- Planning for 1+ years of development
- Need high testability and strict boundaries

## Migration Path

It's difficult to migrate between architectures. If you start with MVVM and outgrow it:

**Option 1:** Scaffold a new Clean Architecture project and migrate features incrementally
**Option 2:** Add domain layer to MVVM project manually (requires significant refactoring)

**Recommendation:** If uncertain, start with Clean Architecture. The upfront complexity pays off in maintainability.
