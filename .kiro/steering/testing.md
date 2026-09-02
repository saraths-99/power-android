---
inclusion: auto
name: testing
description: Testing philosophy, patterns, and tools for Android projects. Use when writing or discussing tests.
---

# Testing Strategy

Generated projects follow a pragmatic testing approach: comprehensive unit tests for business logic, minimal instrumented tests for critical flows, and hand-written test doubles for reliability.

## Testing Philosophy

### Test What Matters
- **Business logic:** Always test (ViewModels, repositories, use cases)
- **UI rendering:** Test selectively (complex screens, important flows)
- **Framework code:** Don't test (Room, Retrofit, Hilt handle their own)
- **Simple mappers:** Optional (low value, high maintenance)

### Hand-Written Test Doubles
Use hand-written implementations of interfaces, not mocking frameworks.

**Why?**
- **Compile-time safety:** Interface changes break test doubles immediately
- **No magic:** Behavior is explicit and debuggable
- **Reusable:** Share doubles across tests
- **Readable:** No mocking DSL to learn

**When?**
- Repositories in ViewModel tests
- Use cases in ViewModel tests (Clean Architecture)
- Data sources in repository tests

## Test Structure

### Location

#### Unit Tests (`src/test/`)
- **Fast:** Run on JVM, no Android runtime
- **For:** ViewModels, repositories, use cases, mappers, utilities
- **Dependencies:** JUnit 4, Truth, Turbine, Coroutines Test

#### Instrumented Tests (`src/androidTest/`)
- **Slow:** Run on device/emulator
- **For:** UI tests, database tests (Room), critical user flows
- **Dependencies:** AndroidX Test, Compose UI Test, Espresso (minimal)

### Module Organization

#### MVVM (Single Module)
```
app/
├── src/test/kotlin/          # Unit tests
│   ├── ui/
│   │   └── home/
│   │       └── HomeViewModelTest.kt
│   ├── data/
│   │   └── repository/
│   │       └── ItemRepositoryImplTest.kt
│   └── testdoubles/
│       └── TestItemRepository.kt
└── src/androidTest/kotlin/   # Instrumented tests
    ├── ui/
    │   └── home/
    │       └── HomeScreenTest.kt
    └── data/
        └── local/
            └── ItemDaoTest.kt
```

#### Clean Architecture (Multi-Module)
```
feature/home/
├── src/test/kotlin/
│   └── HomeViewModelTest.kt
└── src/androidTest/kotlin/
    └── HomeScreenTest.kt

core/domain/
└── src/test/kotlin/
    └── usecase/
        └── GetItemsUseCaseTest.kt

core/data/
└── src/test/kotlin/
    └── repository/
        └── ItemRepositoryImplTest.kt

core/testing/  # Shared test utilities
└── src/main/kotlin/
    ├── repository/
    │   └── TestItemRepository.kt
    ├── rules/
    │   └── MainDispatcherRule.kt
    └── data/
        └── TestData.kt
```

## Unit Testing Patterns

### ViewModel Tests

#### Setup Pattern
```kotlin
@OptIn(ExperimentalCoroutinesApi::class)
class HomeViewModelTest {
    
    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()
    
    private lateinit var viewModel: HomeViewModel
    private lateinit var repository: TestItemRepository
    
    @Before
    fun setup() {
        repository = TestItemRepository()
        viewModel = HomeViewModel(repository)
    }
    
    @Test
    fun `when items loaded then state is success`() = runTest {
        // Given
        val items = listOf(testItem1, testItem2)
        repository.emit(items)
        
        // When - ViewModel already observing
        
        // Then
        viewModel.uiState.test {
            assertThat(awaitItem()).isEqualTo(HomeUiState.Success(items))
        }
    }
    
    @Test
    fun `when loading fails then state is error`() = runTest {
        // Given
        repository.emitError(IOException("Network error"))
        
        // When
        viewModel.onAction(HomeAction.Refresh)
        
        // Then
        viewModel.uiState.test {
            assertThat(awaitItem()).isInstanceOf(HomeUiState.Error::class.java)
        }
    }
}
```

#### MainDispatcherRule
Replaces main dispatcher with test dispatcher for deterministic testing.

```kotlin
// core/testing/rules/MainDispatcherRule.kt
@ExperimentalCoroutinesApi
class MainDispatcherRule(
    private val testDispatcher: TestDispatcher = UnconfinedTestDispatcher()
) : TestWatcher() {
    
    override fun starting(description: Description) {
        Dispatchers.setMain(testDispatcher)
    }
    
    override fun finished(description: Description) {
        Dispatchers.resetMain()
    }
}
```

### Repository Tests

#### Test Repository Implementation
```kotlin
class ItemRepositoryImplTest {
    
    private lateinit var repository: ItemRepository
    private lateinit var dao: TestItemDao
    private lateinit var remoteDataSource: TestItemRemoteDataSource
    private val testDispatcher = UnconfinedTestDispatcher()
    
    @Before
    fun setup() {
        dao = TestItemDao()
        remoteDataSource = TestItemRemoteDataSource()
        repository = ItemRepositoryImpl(
            dao = dao,
            remoteDataSource = remoteDataSource,
            ioDispatcher = testDispatcher
        )
    }
    
    @Test
    fun `observeItems returns items from dao`() = runTest {
        // Given
        val entities = listOf(testEntity1, testEntity2)
        dao.emit(entities)
        
        // When
        val items = repository.observeItems().first()
        
        // Then
        assertThat(items).hasSize(2)
        assertThat(items[0].id).isEqualTo(testEntity1.id)
    }
    
    @Test
    fun `refreshItems fetches from remote and updates dao`() = runTest {
        // Given
        val dtos = listOf(testDto1, testDto2)
        remoteDataSource.setItems(dtos)
        
        // When
        val result = repository.refreshItems()
        
        // Then
        assertThat(result.isSuccess).isTrue()
        assertThat(dao.getInsertedItems()).hasSize(2)
    }
    
    @Test
    fun `refreshItems returns failure on network error`() = runTest {
        // Given
        remoteDataSource.setError(IOException("No network"))
        
        // When
        val result = repository.refreshItems()
        
        // Then
        assertThat(result.isFailure).isTrue()
    }
}
```

### Use Case Tests (Clean Architecture)

```kotlin
class GetItemsUseCaseTest {
    
    private lateinit var useCase: GetItemsUseCase
    private lateinit var repository: TestItemRepository
    
    @Before
    fun setup() {
        repository = TestItemRepository()
        useCase = GetItemsUseCase(repository)
    }
    
    @Test
    fun `invoke returns items from repository`() = runTest {
        // Given
        val items = listOf(testItem1, testItem2)
        repository.emit(items)
        
        // When
        val result = useCase().first()
        
        // Then
        assertThat(result).isEqualTo(items)
    }
}
```

## Test Doubles

### Repository Test Double
```kotlin
// core/testing/repository/TestItemRepository.kt
class TestItemRepository : ItemRepository {
    
    private val itemsFlow = MutableStateFlow<List<Item>>(emptyList())
    private var errorFlow = MutableStateFlow<Throwable?>(null)
    private var refreshResult: Result<Unit> = Result.success(Unit)
    
    override fun observeItems(): Flow<List<Item>> = itemsFlow
        .combine(errorFlow) { items, error ->
            error?.let { throw it } ?: items
        }
    
    override suspend fun refreshItems(): Result<Unit> = refreshResult
    
    // Test helpers
    fun emit(items: List<Item>) {
        itemsFlow.value = items
    }
    
    fun emitError(error: Throwable) {
        errorFlow.value = error
    }
    
    fun setRefreshResult(result: Result<Unit>) {
        refreshResult = result
    }
}
```

### DAO Test Double
```kotlin
class TestItemDao : ItemDao {
    
    private val items = MutableStateFlow<List<ItemEntity>>(emptyList())
    private val insertedItems = mutableListOf<ItemEntity>()
    
    override fun observeAll(): Flow<List<ItemEntity>> = items
    
    override suspend fun upsertAll(items: List<ItemEntity>) {
        insertedItems.addAll(items)
        this.items.value = items
    }
    
    override suspend fun deleteAll() {
        items.value = emptyList()
        insertedItems.clear()
    }
    
    // Test helpers
    fun emit(entities: List<ItemEntity>) {
        items.value = entities
    }
    
    fun getInsertedItems(): List<ItemEntity> = insertedItems
}
```

### Remote Data Source Test Double
```kotlin
class TestItemRemoteDataSource : ItemRemoteDataSource {
    
    private var items: List<ItemDto> = emptyList()
    private var error: Throwable? = null
    
    override suspend fun fetchItems(): List<ItemDto> {
        error?.let { throw it }
        return items
    }
    
    // Test helpers
    fun setItems(items: List<ItemDto>) {
        this.items = items
        this.error = null
    }
    
    fun setError(error: Throwable) {
        this.error = error
    }
}
```

## Testing Flows with Turbine

### Turbine Setup
Add to `build.gradle.kts`:
```kotlin
testImplementation("app.cash.turbine:turbine:1.0.0")
```

### Testing StateFlow Emissions
```kotlin
@Test
fun `state transitions correctly`() = runTest {
    viewModel.uiState.test {
        // Initial state
        assertThat(awaitItem()).isEqualTo(HomeUiState.Loading)
        
        // Emit data
        repository.emit(listOf(testItem))
        assertThat(awaitItem()).isEqualTo(HomeUiState.Success(listOf(testItem)))
        
        // Emit error
        repository.emitError(IOException("Error"))
        assertThat(awaitItem()).isInstanceOf(HomeUiState.Error::class.java)
    }
}
```

### Testing Flow Operators
```kotlin
@Test
fun `repository flow is mapped to ui state`() = runTest {
    // Given
    val items = listOf(testItem1, testItem2)
    
    // When
    repository.emit(items)
    
    // Then
    viewModel.uiState.test {
        val state = awaitItem()
        assertThat(state).isInstanceOf(HomeUiState.Success::class.java)
        assertThat((state as HomeUiState.Success).items).hasSize(2)
    }
}
```

## Compose UI Testing

### Test Stateless Screen Composable
Test the `Screen` composable, not the `Route`. This avoids needing ViewModels and Hilt in tests.

```kotlin
@RunWith(AndroidJUnit4::class)
class HomeScreenTest {
    
    @get:Rule
    val composeTestRule = createComposeRule()
    
    @Test
    fun whenSuccessState_displaysItems() {
        // Given
        val items = listOf(
            Item("1", "Item 1", "Description 1"),
            Item("2", "Item 2", "Description 2")
        )
        val uiState = HomeUiState.Success(items)
        
        // When
        composeTestRule.setContent {
            AppTheme {
                HomeScreen(
                    uiState = uiState,
                    onItemClick = {},
                    onAction = {}
                )
            }
        }
        
        // Then
        composeTestRule.onNodeWithText("Item 1").assertIsDisplayed()
        composeTestRule.onNodeWithText("Item 2").assertIsDisplayed()
    }
    
    @Test
    fun whenEmptyState_displaysEmptyMessage() {
        // Given
        val uiState = HomeUiState.Empty
        
        // When
        composeTestRule.setContent {
            AppTheme {
                HomeScreen(
                    uiState = uiState,
                    onItemClick = {},
                    onAction = {}
                )
            }
        }
        
        // Then
        composeTestRule.onNodeWithText("No items").assertIsDisplayed()
    }
    
    @Test
    fun whenItemClicked_invokesCallback() {
        // Given
        val items = listOf(Item("1", "Item 1", "Description 1"))
        var clickedItemId: String? = null
        
        // When
        composeTestRule.setContent {
            AppTheme {
                HomeScreen(
                    uiState = HomeUiState.Success(items),
                    onItemClick = { clickedItemId = it },
                    onAction = {}
                )
            }
        }
        
        composeTestRule.onNodeWithText("Item 1").performClick()
        
        // Then
        assertThat(clickedItemId).isEqualTo("1")
    }
}
```

### Common Compose Test Patterns

#### Find by Text
```kotlin
composeTestRule.onNodeWithText("Hello").assertIsDisplayed()
```

#### Find by Content Description
```kotlin
composeTestRule.onNodeWithContentDescription("Profile icon").assertIsDisplayed()
```

#### Find by Test Tag
```kotlin
// In composable
Box(modifier = Modifier.testTag("home_content"))

// In test
composeTestRule.onNodeWithTag("home_content").assertIsDisplayed()
```

#### Perform Actions
```kotlin
composeTestRule.onNodeWithText("Submit").performClick()
composeTestRule.onNodeWithTag("text_field").performTextInput("Hello")
composeTestRule.onNodeWithTag("scrollable").performScrollToIndex(5)
```

#### Wait for Condition
```kotlin
composeTestRule.waitUntil(timeoutMillis = 5000) {
    composeTestRule
        .onAllNodesWithText("Loaded")
        .fetchSemanticsNodes()
        .isNotEmpty()
}
```

## Database Testing

### Room DAO Tests
Test DAOs with real Room database (in-memory).

```kotlin
@RunWith(AndroidJUnit4::class)
class ItemDaoTest {
    
    private lateinit var database: AppDatabase
    private lateinit var dao: ItemDao
    
    @Before
    fun setup() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        database = Room.inMemoryDatabaseBuilder(context, AppDatabase::class.java)
            .allowMainThreadQueries()
            .build()
        dao = database.itemDao()
    }
    
    @After
    fun teardown() {
        database.close()
    }
    
    @Test
    fun insertAndRetrieveItems() = runTest {
        // Given
        val entity = ItemEntity("1", "Title", "Description", 123L)
        
        // When
        dao.upsert(entity)
        val items = dao.observeAll().first()
        
        // Then
        assertThat(items).hasSize(1)
        assertThat(items[0].id).isEqualTo("1")
    }
    
    @Test
    fun deleteAll_removesAllItems() = runTest {
        // Given
        dao.upsert(ItemEntity("1", "Title 1", "Desc 1", 123L))
        dao.upsert(ItemEntity("2", "Title 2", "Desc 2", 456L))
        
        // When
        dao.deleteAll()
        val items = dao.observeAll().first()
        
        // Then
        assertThat(items).isEmpty()
    }
}
```

## Test Data Builders

### Shared Test Data
Create test data in `core/testing` module for reuse.

```kotlin
// core/testing/data/TestData.kt
object TestItemData {
    
    val item1 = Item(
        id = "test-id-1",
        title = "Test Item 1",
        description = "Test Description 1",
        timestamp = 1234567890L
    )
    
    val item2 = Item(
        id = "test-id-2",
        title = "Test Item 2",
        description = "Test Description 2",
        timestamp = 1234567891L
    )
    
    fun item(
        id: String = "test-id",
        title: String = "Test Title",
        description: String = "Test Description",
        timestamp: Long = System.currentTimeMillis()
    ) = Item(id, title, description, timestamp)
}

object TestItemEntityData {
    
    fun entity(
        id: String = "test-id",
        title: String = "Test Title",
        description: String = "Test Description",
        timestamp: Long = System.currentTimeMillis()
    ) = ItemEntity(id, title, description, timestamp)
}
```

## Testing Best Practices

### Do's
- ✅ Test business logic (ViewModels, repositories, use cases)
- ✅ Use hand-written test doubles
- ✅ Test stateless Screen composables, not Routes
- ✅ Use descriptive test names with backticks
- ✅ Follow Given-When-Then structure
- ✅ Share test data and utilities in `core/testing`
- ✅ Use `runTest` for coroutine tests
- ✅ Use Turbine for Flow testing
- ✅ Test error cases and edge cases

### Don'ts
- ❌ Don't use mocking frameworks (MockK, Mockito)
- ❌ Don't test framework code (Room, Retrofit)
- ❌ Don't test simple data classes or mappers
- ❌ Don't make tests depend on each other
- ❌ Don't use real network calls in tests
- ❌ Don't test private functions directly
- ❌ Don't skip error case testing

## Test Coverage Guidelines

### High Priority (Must Test)
- ViewModels (all state transitions)
- Repositories (data coordination logic)
- Use cases (business logic)
- Complex UI logic (conditional rendering)

### Medium Priority (Should Test)
- Composable screens (important flows)
- Navigation logic
- Data transformations (mappers with logic)
- Error handling paths

### Low Priority (Optional)
- Simple data classes
- Trivial mappers (`entity.toModel()`)
- Framework wrappers
- Hilt modules

## Running Tests

### Command Line
```bash
# All unit tests
./gradlew test

# Specific module unit tests
./gradlew :feature:home:test

# All instrumented tests
./gradlew connectedAndroidTest

# Specific module instrumented tests
./gradlew :app:connectedAndroidTest

# With coverage
./gradlew test jacocoTestReport
```

### Android Studio
- Right-click package/file → Run Tests
- Run Configuration → Create JUnit or Android Instrumented Tests config
- View coverage: Run → Run with Coverage

## Dependencies Reference

### Unit Test Dependencies
```kotlin
// build.gradle.kts (in testImplementation)
testImplementation("junit:junit:4.13.2")
testImplementation("com.google.truth:truth:1.1.5")
testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")
testImplementation("app.cash.turbine:turbine:1.0.0")
```

### Instrumented Test Dependencies
```kotlin
// build.gradle.kts (in androidTestImplementation)
androidTestImplementation("androidx.test.ext:junit:1.1.5")
androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
androidTestImplementation("androidx.compose.ui:ui-test-junit4")
debugImplementation("androidx.compose.ui:ui-test-manifest")
```

### Test Utilities Module (Clean Architecture)
```kotlin
// core/testing/build.gradle.kts
dependencies {
    implementation(project(":core:domain"))
    implementation(project(":core:data"))
    implementation(libs.kotlinx.coroutines.test)
    implementation(libs.junit)
}
```

## Summary Checklist

When writing tests:
- [ ] Test class named `<ClassUnderTest>Test`
- [ ] Test functions use backticks for readable names
- [ ] Given-When-Then structure followed
- [ ] Hand-written test doubles used (no mocking)
- [ ] `MainDispatcherRule` added for ViewModel tests
- [ ] Turbine used for Flow testing
- [ ] Stateless Screen tested, not Route
- [ ] Test data shared from `core/testing`
- [ ] Error cases covered
- [ ] Tests are independent (no shared state)
