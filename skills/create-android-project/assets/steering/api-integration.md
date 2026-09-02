# {{PROJECT_NAME}} — API Integration

Describes how this project handles remote data: Retrofit configuration, DTO mapping,
error handling, and the offline-first sync pattern.

{{NETWORK_GUARD}}

## 1. Network layer structure

{{NETWORK_STRUCTURE}}

All network types live in {{NETWORK_MODULE}}.

## 2. Retrofit configuration

The Retrofit instance is provided via Hilt:

```kotlin
@Module
@InstallIn(SingletonComponent::class)
internal object NetworkModule {
    @Provides
    @Singleton
    fun provideRetrofit(): Retrofit = Retrofit.Builder()
        .baseUrl("https://api.example.com/")  // Replace with actual API base URL
        .addConverterFactory(Json.asConverterFactory("application/json".toMediaType()))
        .build()

    @Provides
    @Singleton
    fun provideItemApi(retrofit: Retrofit): ItemApi =
        retrofit.create(ItemApi::class.java)
}
```

**Key points:**
- Use kotlinx.serialization for JSON, not Gson or Moshi
- Base URL goes in the module; environment-specific URLs can use BuildConfig
- API interfaces are provided as singletons

## 3. API interface pattern

Define API endpoints as suspend functions returning DTOs:

```kotlin
internal interface ItemApi {
    @GET("items")
    suspend fun getItems(): List<ItemDto>

    @GET("items/{id}")
    suspend fun getItem(@Path("id") id: String): ItemDto

    @POST("items")
    suspend fun createItem(@Body item: CreateItemDto): ItemDto

    @PUT("items/{id}")
    suspend fun updateItem(@Path("id") id: String, @Body item: UpdateItemDto): ItemDto

    @DELETE("items/{id}")
    suspend fun deleteItem(@Path("id") id: String)
}
```

**Rules:**
- Interfaces are `internal`
- Use suspend functions, not `Call<T>` or `Response<T>`
- DTOs are dedicated types, never reuse domain models
- Path parameters use `@Path`, query params use `@Query`, body uses `@Body`

## 4. Data Transfer Objects (DTOs)

DTOs are kotlinx.serialization data classes matching the API schema:

```kotlin
@Serializable
internal data class ItemDto(
    @SerialName("id") val id: String,
    @SerialName("title") val title: String,
    @SerialName("description") val description: String,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
internal data class CreateItemDto(
    @SerialName("title") val title: String,
    @SerialName("description") val description: String,
)
```

**Rules:**
- DTOs are `internal` and live in {{NETWORK_MODULE}}
- Use `@SerialName` for all properties (makes API contract explicit)
- Primitive types only (String, Int, Boolean, List); parse dates/enums in mapper
- Name pattern: `<Thing>Dto`, `Create<Thing>Dto`, `Update<Thing>Dto`

## 5. Remote data sources

Wrap API interfaces in a data source abstraction:

```kotlin
internal interface ItemRemoteDataSource {
    suspend fun getItems(): Result<List<ItemDto>>
    suspend fun getItem(id: String): Result<ItemDto>
    suspend fun createItem(item: CreateItemDto): Result<ItemDto>
}

internal class DefaultItemRemoteDataSource @Inject constructor(
    private val api: ItemApi,
) : ItemRemoteDataSource {

    override suspend fun getItems(): Result<List<ItemDto>> =
        try {
            Result.success(api.getItems())
        } catch (e: Exception) {
            Result.failure(e)
        }

    override suspend fun getItem(id: String): Result<ItemDto> =
        try {
            Result.success(api.getItem(id))
        } catch (e: Exception) {
            Result.failure(e)
        }

    override suspend fun createItem(item: CreateItemDto): Result<ItemDto> =
        try {
            Result.success(api.createItem(item))
        } catch (e: Exception) {
            Result.failure(e)
        }
}
```

**Why?** The data source layer catches exceptions and returns `Result<T>` so callers
don't need try/catch blocks. It also isolates Retrofit from the repository.

## 6. DTO to domain mapping

Mappers convert between DTOs and domain models:

```kotlin
internal fun ItemDto.toDomain(): Item = Item(
    id = id,
    title = title,
    description = description,
    createdAt = Instant.parse(createdAt),  // Parse API string to domain type
)

internal fun Item.toCreateDto(): CreateItemDto = CreateItemDto(
    title = title,
    description = description,
)

internal fun Item.toUpdateDto(): UpdateItemDto = UpdateItemDto(
    title = title,
    description = description,
)
```

**Rules:**
- Extension functions, `internal` visibility
- Live in {{MAPPER_LOCATION}}
- Named `toDomain()`, `toEntity()`, `toCreateDto()`, etc.
- Handle parsing (dates, enums) and validation here

## 7. Offline-first repository pattern

The repository coordinates local and remote data sources. **The database is the source
of truth:**

```kotlin
{{REPO_IMPL_INTERFACE}}class DefaultItemRepository @Inject constructor(
    private val localDataSource: ItemDao,
    private val remoteDataSource: ItemRemoteDataSource,
    @Dispatcher(IO) private val ioDispatcher: CoroutineDispatcher,
) : ItemRepository {

    // Reads come from the database
    override fun observeItems(): Flow<List<Item>> =
        localDataSource.observeAll()
            .map { entities -> entities.map { it.toDomain() } }

    override fun observeItem(id: String): Flow<Item?> =
        localDataSource.observeById(id)
            .map { it?.toDomain() }

    // Writes update the database, then sync to server
    override suspend fun upsertItem(item: Item) = withContext(ioDispatcher) {
        localDataSource.upsert(item.toEntity())
        syncItem(item.id)  // Background sync
    }

    // Sync fetches from server and updates database
    override suspend fun sync(): Boolean = withContext(ioDispatcher) {
        when (val result = remoteDataSource.getItems()) {
            is Result.Success -> {
                val entities = result.value.map { it.toDomain().toEntity() }
                localDataSource.upsertAll(entities)
                true
            }
            is Result.Failure -> {
                // Log error, but don't crash
                false
            }
        }
    }

    private suspend fun syncItem(id: String) {
        // Best-effort sync, failures are silent
        val item = localDataSource.getById(id)?.toDomain() ?: return
        remoteDataSource.createItem(item.toCreateDto())
    }
}
```

**Key principles:**
- UI reads from the database via `Flow`, never waits on network
- Sync operations update the database, not the return value
- Network failures don't crash the app; sync returns success/failure boolean
- ViewModel calls `repository.sync()` on user action (pull-to-refresh)

## 8. Error handling

### Network errors
Catch at the data source layer and return `Result.failure(exception)`.

### Repository layer
- Sync failures return `false`, not exceptions
- Don't propagate exceptions to ViewModel
- Log errors for debugging

### ViewModel layer
Present errors as UI state:

```kotlin
sealed interface HomeUiState {
    data object Loading : HomeUiState
    data class Success(val items: List<Item>, val isSyncing: Boolean = false) : HomeUiState
    data class Error(val message: String) : HomeUiState
}

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val repository: ItemRepository,
) : ViewModel() {

    val uiState: StateFlow<HomeUiState> = repository.observeItems()
        .map<List<Item>, HomeUiState> { items ->
            if (items.isEmpty()) HomeUiState.Loading
            else HomeUiState.Success(items)
        }
        .catch { emit(HomeUiState.Error(it.message ?: "Something went wrong")) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = HomeUiState.Loading,
        )

    fun onAction(action: HomeAction) {
        when (action) {
            HomeAction.Refresh -> refresh()
        }
    }

    private fun refresh() {
        viewModelScope.launch {
            val success = repository.sync()
            // Optionally show toast or update state
        }
    }
}
```

## 9. Authentication

If your API requires authentication:

### Add token to requests
Use an OkHttp interceptor:

```kotlin
internal class AuthInterceptor @Inject constructor(
    private val tokenProvider: TokenProvider,
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val token = tokenProvider.getToken()
        val request = chain.request().newBuilder()
            .addHeader("Authorization", "Bearer $token")
            .build()
        return chain.proceed(request)
    }
}

@Provides
@Singleton
fun provideOkHttpClient(authInterceptor: AuthInterceptor): OkHttpClient =
    OkHttpClient.Builder()
        .addInterceptor(authInterceptor)
        .build()

@Provides
@Singleton
fun provideRetrofit(okHttpClient: OkHttpClient): Retrofit =
    Retrofit.Builder()
        .client(okHttpClient)
        .baseUrl("https://api.example.com/")
        .addConverterFactory(Json.asConverterFactory("application/json".toMediaType()))
        .build()
```

### Store token securely
Use EncryptedSharedPreferences or DataStore with encryption.

## 10. Testing network code

### Mock the remote data source
```kotlin
class TestItemRemoteDataSource : ItemRemoteDataSource {
    private val responses = mutableMapOf<String, Result<ItemDto>>()

    fun setResponse(id: String, result: Result<ItemDto>) {
        responses[id] = result
    }

    override suspend fun getItem(id: String): Result<ItemDto> =
        responses[id] ?: Result.failure(Exception("Not found"))
}
```

### Test repository with fake data sources
```kotlin
class ItemRepositoryTest {
    private val dao = TestItemDao()
    private val remoteDataSource = TestItemRemoteDataSource()
    private val repository = DefaultItemRepository(dao, remoteDataSource, testDispatcher)

    @Test
    fun `sync updates local database from remote`() = runTest {
        val remoteItems = listOf(ItemDto("1", "Title", "Description", "2024-01-01"))
        remoteDataSource.setGetItemsResponse(Result.success(remoteItems))

        val success = repository.sync()

        assertThat(success).isTrue()
        assertThat(dao.getAll()).hasSize(1)
    }
}
```

## 11. Common patterns

### Pagination
Add pagination parameters to API and repository:

```kotlin
interface ItemApi {
    @GET("items")
    suspend fun getItems(
        @Query("page") page: Int,
        @Query("limit") limit: Int = 20,
    ): List<ItemDto>
}

interface ItemRepository {
    suspend fun loadPage(page: Int): Result<List<Item>>
}
```

Use Paging 3 for infinite scroll if needed.

### Request cancellation
Retrofit suspend functions respect coroutine cancellation automatically. When
`viewModelScope` cancels, in-flight requests are cancelled.

### Retry logic
Add retry with exponential backoff:

```kotlin
suspend fun <T> retryWithBackoff(
    times: Int = 3,
    initialDelay: Long = 100,
    maxDelay: Long = 1000,
    factor: Double = 2.0,
    block: suspend () -> T,
): T {
    var currentDelay = initialDelay
    repeat(times - 1) {
        try {
            return block()
        } catch (e: Exception) {
            delay(currentDelay)
            currentDelay = (currentDelay * factor).toLong().coerceAtMost(maxDelay)
        }
    }
    return block()  // Last attempt throws on failure
}
```

## Summary checklist

When integrating a new API:
- [ ] Define DTO data classes with `@Serializable` and `@SerialName`
- [ ] Create Retrofit interface with suspend functions
- [ ] Wrap in remote data source returning `Result<T>`
- [ ] Write mappers between DTO and domain models
- [ ] Implement repository with offline-first pattern
- [ ] Handle errors gracefully (no crashes on network failure)
- [ ] Test with hand-written test doubles
- [ ] Document base URL and authentication requirements
