# {{PROJECT_NAME}} — Testing

Describes the testing philosophy, tools, and patterns for this project.

## Testing philosophy

This project follows these testing principles:

1. **Hand-written test doubles**, not mocking frameworks — A test double that
   implements the real interface fails to compile when the interface changes; a mock
   silently drifts.

2. **Test behavior, not implementation** — Tests verify what code does, not how it
   does it. Refactoring should not break tests.

3. **Unit tests are the foundation** — Fast, focused tests for ViewModels,
   repositories, and business logic. Instrumented tests only for critical user flows.

4. **Test the stateless Screen, not the Route** — Screen composables receive data and
   emit events, so no ViewModel or Hilt graph is needed.

## 1. Test structure

Tests are organized by layer:

{{TEST_STRUCTURE}}

## 2. Testing tools

### JUnit 4
Standard testing framework.

```kotlin
class ExampleTest {
    @Test
    fun `test description in backticks`() {
        // Arrange
        val input = "test"
        
        // Act
        val result = doSomething(input)
        
        // Assert
        assertThat(result).isEqualTo("expected")
    }
}
```

### Truth (Google's assertion library)
More readable than JUnit assertions.

```kotlin
// ✓ Good - Truth
assertThat(result).isEqualTo(expected)
assertThat(list).hasSize(3)
assertThat(list).containsExactly("a", "b", "c")
assertThat(state).isInstanceOf(Success::class.java)

// ✗ Avoid - JUnit
assertEquals(expected, result)  // Order confusion
assertTrue(list.size == 3)  // Less descriptive
```

### Turbine (Flow testing)
Simplifies testing `Flow` emissions.

```kotlin
@Test
fun `uiState emits Success when items loaded`() = runTest {
    repository.emit(listOf(testItem))

    viewModel.uiState.test {
        assertThat(awaitItem()).isEqualTo(Loading)
        assertThat(awaitItem()).isEqualTo(Success(listOf(testItem)))
    }
}
```

### Coroutine Test Library
Provides `runTest` and `TestDispatchers`.

```kotlin
@Test
fun `repository fetches data on IO dispatcher`() = runTest {
    val result = repository.getData()
    assertThat(result).isNotEmpty()
}
```

{{TEST_UTILITIES_SECTION}}

## 3. Testing ViewModels

### Test setup

```kotlin
class HomeViewModelTest {
    private lateinit var repository: TestItemRepository
    private lateinit var viewModel: HomeViewModel

    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()

    @Before
    fun setup() {
        repository = TestItemRepository()
        viewModel = HomeViewModel(repository)
    }

    @Test
    fun `uiState is Loading initially`() = runTest {
        val state = viewModel.uiState.value
        assertThat(state).isEqualTo(HomeUiState.Loading)
    }

    @Test
    fun `uiState emits Success when items are loaded`() = runTest {
        repository.emit(listOf(testItem))

        viewModel.uiState.test {
            assertThat(awaitItem()).isEqualTo(HomeUiState.Loading)
            val successState = awaitItem()
            assertThat(successState).isInstanceOf(HomeUiState.Success::class.java)
            assertThat((successState as HomeUiState.Success).items).hasSize(1)
        }
    }

    @Test
    fun `when Refresh action then repository syncs`() = runTest {
        viewModel.onAction(HomeAction.Refresh)

        assertThat(repository.syncCallCount).isEqualTo(1)
    }
}
```

### MainDispatcherRule

Replaces `Dispatchers.Main` with a test dispatcher:

{{MAIN_DISPATCHER_RULE_LOCATION}}

```kotlin
class MainDispatcherRule(
    private val testDispatcher: TestDispatcher = UnconfinedTestDispatcher(),
) : TestWatcher() {
    override fun starting(description: Description) {
        Dispatchers.setMain(testDispatcher)
    }

    override fun finished(description: Description) {
        Dispatchers.resetMain()
    }
}
```

Use in every ViewModel test:

```kotlin
@get:Rule
val mainDispatcherRule = MainDispatcherRule()
```

## 4. Testing Repositories

### Test with hand-written doubles

```kotlin
class ItemRepositoryTest {
    private lateinit var dao: TestItemDao
    private lateinit var remoteDataSource: TestItemRemoteDataSource
    private lateinit var repository: DefaultItemRepository
    private val testDispatcher = StandardTestDispatcher()

    @Before
    fun setup() {
        dao = TestItemDao()
        remoteDataSource = TestItemRemoteDataSource()
        repository = DefaultItemRepository(dao, remoteDataSource, testDispatcher)
    }

    @Test
    fun `observeItems emits data from DAO`() = runTest(testDispatcher) {
        dao.insert(testEntity)

        repository.observeItems().test {
            val items = awaitItem()
            assertThat(items).hasSize(1)
            assertThat(items.first().id).isEqualTo("test-id")
        }
    }

    @Test
    fun `sync updates database with remote data`() = runTest(testDispatcher) {
        remoteDataSource.setItems(listOf(testDto))

        val success = repository.sync()

        assertThat(success).isTrue()
        assertThat(dao.getAll()).hasSize(1)
    }

    @Test
    fun `sync returns false when remote fails`() = runTest(testDispatcher) {
        remoteDataSource.setFailure(IOException("Network error"))

        val success = repository.sync()

        assertThat(success).isFalse()
    }
}
```

## 5. Testing Composables

### Test the Screen, not the Route

The stateless `Screen` composable is testable without Hilt:

```kotlin
class HomeScreenTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun `displays loading state`() {
        composeTestRule.setContent {
            AppTheme {
                HomeScreen(
                    uiState = HomeUiState.Loading,
                    onAction = {},
                )
            }
        }

        composeTestRule.onNodeWithTag("loading").assertIsDisplayed()
    }

    @Test
    fun `displays items in success state`() {
        val items = listOf(testItem.copy(title = "Test Item"))

        composeTestRule.setContent {
            AppTheme {
                HomeScreen(
                    uiState = HomeUiState.Success(items),
                    onAction = {},
                )
            }
        }

        composeTestRule.onNodeWithText("Test Item").assertIsDisplayed()
    }

    @Test
    fun `clicking item invokes callback`() {
        var clickedId: String? = null
        val items = listOf(testItem)

        composeTestRule.setContent {
            AppTheme {
                HomeScreen(
                    uiState = HomeUiState.Success(items),
                    onAction = {},
                    onItemClick = { clickedId = it }
                )
            }
        }

        composeTestRule.onNodeWithText(testItem.title).performClick()
        assertThat(clickedId).isEqualTo(testItem.id)
    }

    @Test
    fun `displays error message in error state`() {
        composeTestRule.setContent {
            AppTheme {
                HomeScreen(
                    uiState = HomeUiState.Error("Network error"),
                    onAction = {},
                )
            }
        }

        composeTestRule.onNodeWithText("Network error").assertIsDisplayed()
    }
}
```

### Semantic test tags

Use test tags for non-text elements:

```kotlin
CircularProgressIndicator(
    modifier = Modifier.testTag("loading")
)

// In test
composeTestRule.onNodeWithTag("loading").assertIsDisplayed()
```

### Accessibility testing

Verify semantic properties:

```kotlin
composeTestRule.onNodeWithContentDescription("Home icon").assertExists()
composeTestRule.onNodeWithText("Submit").assertHasClickAction()
```

## 6. Test Doubles

### Repository test double

{{TEST_DOUBLE_LOCATION}}

```kotlin
class TestItemRepository : ItemRepository {
    private val itemsFlow = MutableStateFlow<List<Item>>(emptyList())
    var syncCallCount = 0
        private set
    private var syncResult = true

    override fun observeItems(): Flow<List<Item>> = itemsFlow.asStateFlow()

    override fun observeItem(id: String): Flow<Item?> =
        itemsFlow.map { items -> items.find { it.id == id } }

    override suspend fun upsertItem(item: Item) {
        itemsFlow.value = itemsFlow.value + item
    }

    override suspend fun deleteItem(id: String) {
        itemsFlow.value = itemsFlow.value.filterNot { it.id == id }
    }

    override suspend fun sync(): Boolean {
        syncCallCount++
        return syncResult
    }

    // Test control methods
    fun emit(items: List<Item>) {
        itemsFlow.value = items
    }

    fun setSyncResult(success: Boolean) {
        syncResult = success
    }
}
```

### DAO test double

```kotlin
class TestItemDao : ItemDao {
    private val items = mutableListOf<ItemEntity>()
    private val itemsFlow = MutableStateFlow<List<ItemEntity>>(emptyList())

    override fun observeAll(): Flow<List<ItemEntity>> = itemsFlow.asStateFlow()

    override fun observeById(id: String): Flow<ItemEntity?> =
        itemsFlow.map { list -> list.find { it.id == id } }

    override suspend fun upsert(item: ItemEntity) {
        items.removeIf { it.id == item.id }
        items.add(item)
        itemsFlow.value = items.toList()
    }

    override suspend fun upsertAll(items: List<ItemEntity>) {
        this.items.clear()
        this.items.addAll(items)
        itemsFlow.value = this.items.toList()
    }

    override suspend fun delete(id: String) {
        items.removeIf { it.id == id }
        itemsFlow.value = items.toList()
    }

    // Test helper
    fun getAll(): List<ItemEntity> = items.toList()
}
```

### Remote data source test double

```kotlin
class TestItemRemoteDataSource : ItemRemoteDataSource {
    private var itemsResult: Result<List<ItemDto>> = Result.success(emptyList())

    override suspend fun getItems(): Result<List<ItemDto>> = itemsResult

    override suspend fun getItem(id: String): Result<ItemDto> =
        itemsResult.mapCatching { list ->
            list.find { it.id == id } ?: throw NoSuchElementException("Item not found")
        }

    // Test control
    fun setItems(items: List<ItemDto>) {
        itemsResult = Result.success(items)
    }

    fun setFailure(exception: Exception) {
        itemsResult = Result.failure(exception)
    }
}
```

## 7. Instrumented tests

Reserve instrumented tests (`androidTest/`) for critical flows that require Android
framework or device features.

### Database tests

Test actual Room implementation:

```kotlin
@RunWith(AndroidJUnit4::class)
class ItemDaoTest {
    private lateinit var database: AppDatabase
    private lateinit var dao: ItemDao

    @Before
    fun setup() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        database = Room.inMemoryDatabaseBuilder(context, AppDatabase::class.java).build()
        dao = database.itemDao()
    }

    @After
    fun teardown() {
        database.close()
    }

    @Test
    fun insertAndRetrieveItem() = runTest {
        val entity = ItemEntity("1", "Title", "Description")
        dao.upsert(entity)

        val retrieved = dao.getAll().first()
        assertThat(retrieved).hasSize(1)
        assertThat(retrieved.first().title).isEqualTo("Title")
    }
}
```

### UI tests for critical flows

```kotlin
@RunWith(AndroidJUnit4::class)
class LoginFlowTest {
    @get:Rule
    val composeTestRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun userCanLoginSuccessfully() {
        // Navigate to login
        composeTestRule.onNodeWithText("Login").performClick()

        // Enter credentials
        composeTestRule.onNodeWithTag("email").performTextInput("user@example.com")
        composeTestRule.onNodeWithTag("password").performTextInput("password")

        // Submit
        composeTestRule.onNodeWithText("Submit").performClick()

        // Verify navigation to home
        composeTestRule.waitUntil(timeoutMillis = 5000) {
            composeTestRule.onAllNodesWithText("Home").fetchSemanticsNodes().isNotEmpty()
        }
    }
}
```

## 8. Test data builders

Create reusable test data:

{{TEST_DATA_LOCATION}}

```kotlin
object TestData {
    val testItem = Item(
        id = "test-id",
        title = "Test Item",
        description = "Test description",
        createdAt = Instant.parse("2024-01-01T00:00:00Z"),
    )

    val testEntity = ItemEntity(
        id = "test-id",
        title = "Test Item",
        description = "Test description",
        createdAt = 1704067200000L,
    )

    val testDto = ItemDto(
        id = "test-id",
        title = "Test Item",
        description = "Test description",
        createdAt = "2024-01-01T00:00:00Z",
    )

    fun createItem(
        id: String = "test-id",
        title: String = "Test Item",
        description: String = "Test description",
    ) = Item(id, title, description, Instant.now())
}
```

## 9. Common testing patterns

### Testing loading state
```kotlin
@Test
fun `initial state is Loading`() {
    val state = viewModel.uiState.value
    assertThat(state).isEqualTo(Loading)
}
```

### Testing success state
```kotlin
@Test
fun `when data loaded then state is Success`() = runTest {
    repository.emit(listOf(testItem))

    viewModel.uiState.test {
        skipItems(1)  // Skip Loading
        val state = awaitItem()
        assertThat(state).isInstanceOf(Success::class.java)
    }
}
```

### Testing error handling
```kotlin
@Test
fun `when load fails then state is Error`() = runTest {
    repository.setFailure(IOException("Network error"))

    viewModel.uiState.test {
        skipItems(1)  // Skip Loading
        val state = awaitItem()
        assertThat(state).isInstanceOf(Error::class.java)
        assertThat((state as Error).message).contains("Network")
    }
}
```

### Testing user actions
```kotlin
@Test
fun `when Refresh action then repository syncs`() = runTest {
    viewModel.onAction(Refresh)
    
    advanceUntilIdle()  // Let coroutines complete
    assertThat(repository.syncCallCount).isEqualTo(1)
}
```

## 10. Coverage expectations

Aim for these coverage levels:
- **ViewModels:** 80%+ — Core business logic
- **Repositories:** 80%+ — Data coordination
- **Mappers:** 90%+ — Simple transformations
- **Composables:** 50%+ — Critical interactions only
- **DAOs:** Instrumented tests for complex queries

Don't chase 100% coverage. Focus on behavior that matters to users.

## Rules summary

- [ ] Use hand-written test doubles, not mocking frameworks
- [ ] Test doubles implement real interfaces
- [ ] ViewModels tested with `MainDispatcherRule` and `runTest`
- [ ] Flow tested with Turbine
- [ ] Test the stateless Screen, not the Route
- [ ] Use Truth for assertions
- [ ] Instrumented tests only for Room and critical flows
- [ ] Test data builders in {{TEST_DATA_LOCATION}}
- [ ] Shared test utilities in {{TEST_UTILITIES_LOCATION}}
- [ ] Test names use backticks for readability
