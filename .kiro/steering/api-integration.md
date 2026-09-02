---
inclusion: auto
name: api-integration
description: REST API integration patterns with Retrofit, kotlinx.serialization, and offline-first data sync. Use when implementing network calls, API endpoints, or data synchronization.
---

# API Integration

Generated projects use **Retrofit** with **kotlinx.serialization** for REST API integration, following an offline-first architecture where the local database is the source of truth.

## Core Principles

### Offline-First
- **Database is source of truth:** UI reads from Room, never directly from network
- **Network updates database:** API responses are written to database, then Flow emits updates
- **App works offline:** UI shows cached data while sync happens in background
- **Graceful degradation:** Network failures don't break UI; they're logged and retried

### Separation of Concerns
- **Remote data sources:** Encapsulate Retrofit services
- **DTOs (Data Transfer Objects):** Model API responses
- **Repositories:** Coordinate network and database
- **Mappers:** Convert between DTOs, entities, and domain models

## Project Setup

### Dependencies

#### Version Catalog (`gradle/libs.versions.toml`)
```toml
[versions]
retrofit = "2.9.0"
okhttp = "4.12.0"
kotlinx-serialization = "1.6.2"

[libraries]
retrofit = { module = "com.squareup.retrofit2:retrofit", version.ref = "retrofit" }
retrofit-kotlinx-serialization = { module = "com.jakewharton.retrofit:retrofit2-kotlinx-serialization-converter", version = "1.0.0" }
okhttp-logging = { module = "com.squareup.okhttp3:logging-interceptor", version.ref = "okhttp" }
kotlinx-serialization-json = { module = "org.jetbrains.kotlinx:kotlinx-serialization-json", version.ref = "kotlinx-serialization" }

[plugins]
kotlin-serialization = { id = "org.jetbrains.kotlin.plugin.serialization", version.ref = "kotlin" }
```

#### Module Build File
```kotlin
// MVVM: app/build.gradle.kts
// Clean: core/network/build.gradle.kts

plugins {
    alias(libs.plugins.kotlin.serialization)
}

dependencies {
    implementation(libs.retrofit)
    implementation(libs.retrofit.kotlinx.serialization)
    implementation(libs.okhttp.logging)
    implementation(libs.kotlinx.serialization.json)
}
```

## Network Module Structure

### MVVM Architecture
```
app/src/main/kotlin/com/example/app/
└── data/
    └── remote/
        ├── ItemDto.kt                    # API model
        ├── ItemRemoteDataSource.kt       # Retrofit service interface
        └── di/
            └── NetworkModule.kt          # Provides Retrofit, OkHttp
```

### Clean Architecture
```
core/network/src/main/kotlin/com/example/app/core/network/
├── model/
│   └── ItemDto.kt                        # API model
├── ItemRemoteDataSource.kt               # Retrofit service interface
└── di/
    └── NetworkModule.kt                  # Provides Retrofit, OkHttp, services
```

## DTOs (Data Transfer Objects)

### Basic DTO
```kotlin
import kotlinx.serialization.Serializable

@Serializable
data class ItemDto(
    val id: String,
    val title: String,
    val description: String,
    val timestamp: Long
)
```

### DTO with Custom JSON Keys
```kotlin
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class UserDto(
    @SerialName("user_id")
    val userId: String,
    
    @SerialName("full_name")
    val fullName: String,
    
    @SerialName("email_address")
    val email: String,
    
    @SerialName("created_at")
    val createdAt: Long
)
```

### Nested DTOs
```kotlin
@Serializable
data class ApiResponse<T>(
    val success: Boolean,
    val data: T? = null,
    val error: ErrorDto? = null
)

@Serializable
data class ErrorDto(
    val code: Int,
    val message: String
)

@Serializable
data class ItemListDto(
    val items: List<ItemDto>,
    val total: Int,
    val page: Int
)
```

### Nullable and Default Values
```kotlin
@Serializable
data class ItemDto(
    val id: String,
    val title: String,
    val description: String? = null,        // Nullable with default
    val timestamp: Long = 0L,               // Default value
    val tags: List<String> = emptyList()    // Default empty list
)
```

## Remote Data Sources

### Service Interface
```kotlin
interface ItemRemoteDataSource {
    suspend fun getItems(): List<ItemDto>
    suspend fun getItem(id: String): ItemDto
    suspend fun createItem(item: ItemDto): ItemDto
    suspend fun updateItem(id: String, item: ItemDto): ItemDto
    suspend fun deleteItem(id: String)
}
```

### Retrofit Implementation
```kotlin
import retrofit2.http.*

interface ItemRemoteDataSource {
    
    @GET("items")
    suspend fun getItems(): List<ItemDto>
    
    @GET("items/{id}")
    suspend fun getItem(@Path("id") id: String): ItemDto
    
    @POST("items")
    suspend fun createItem(@Body item: ItemDto): ItemDto
    
    @PUT("items/{id}")
    suspend fun updateItem(
        @Path("id") id: String,
        @Body item: ItemDto
    ): ItemDto
    
    @DELETE("items/{id}")
    suspend fun deleteItem(@Path("id") id: String)
}
```

### Query Parameters
```kotlin
interface ItemRemoteDataSource {
    
    @GET("items")
    suspend fun getItems(
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20,
        @Query("sort") sort: String = "created_at",
        @Query("order") order: String = "desc"
    ): ItemListDto
    
    @GET("search")
    suspend fun searchItems(
        @Query("q") query: String,
        @Query("category") category: String? = null
    ): List<ItemDto>
}
```

### Headers
```kotlin
interface ItemRemoteDataSource {
    
    @GET("items")
    suspend fun getItems(
        @Header("Authorization") token: String
    ): List<ItemDto>
    
    @POST("items")
    @Headers("Content-Type: application/json")
    suspend fun createItem(@Body item: ItemDto): ItemDto
}
```

## Network Module (Dependency Injection)

### Basic Setup
```kotlin
@Module
@InstallIn(SingletonComponent::class)
internal object NetworkModule {
    
    private const val BASE_URL = "https://api.example.com/v1/"
    
    @Provides
    @Singleton
    fun provideJson(): Json = Json {
        ignoreUnknownKeys = true          // Ignore unknown JSON fields
        coerceInputValues = true          // Coerce invalid values to defaults
        explicitNulls = false             // Omit null values in serialization
    }
    
    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient = OkHttpClient.Builder()
        .addInterceptor(
            HttpLoggingInterceptor().apply {
                level = if (BuildConfig.DEBUG) {
                    HttpLoggingInterceptor.Level.BODY
                } else {
                    HttpLoggingInterceptor.Level.NONE
                }
            }
        )
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
    
    @Provides
    @Singleton
    fun provideRetrofit(
        okHttpClient: OkHttpClient,
        json: Json
    ): Retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()
    
    @Provides
    @Singleton
    fun provideItemRemoteDataSource(retrofit: Retrofit): ItemRemoteDataSource =
        retrofit.create(ItemRemoteDataSource::class.java)
}
```

### With Authentication Interceptor
```kotlin
@Singleton
class AuthInterceptor @Inject constructor(
    private val tokenProvider: TokenProvider
) : Interceptor {
    
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        val authenticatedRequest = request.newBuilder()
            .header("Authorization", "Bearer ${tokenProvider.getToken()}")
            .build()
        return chain.proceed(authenticatedRequest)
    }
}

// In NetworkModule
@Provides
@Singleton
fun provideOkHttpClient(
    authInterceptor: AuthInterceptor
): OkHttpClient = OkHttpClient.Builder()
    .addInterceptor(authInterceptor)
    .addInterceptor(HttpLoggingInterceptor().apply { ... })
    .build()
```

## Repository Integration

### Offline-First Repository Pattern
```kotlin
internal class ItemRepositoryImpl @Inject constructor(
    private val dao: ItemDao,
    private val remoteDataSource: ItemRemoteDataSource,
    @Dispatcher(IO) private val ioDispatcher: CoroutineDispatcher
) : ItemRepository {
    
    // UI observes database, never network
    override fun observeItems(): Flow<List<Item>> =
        dao.observeAll().map { entities ->
            entities.map { it.toDomain() }
        }
    
    override fun observeItem(id: String): Flow<Item?> =
        dao.observeById(id).map { it?.toDomain() }
    
    // Sync updates database; UI updates automatically via Flow
    override suspend fun refreshItems(): Result<Unit> =
        withContext(ioDispatcher) {
            try {
                val dtos = remoteDataSource.getItems()
                val entities = dtos.map { it.toEntity() }
                dao.upsertAll(entities)
                Result.success(Unit)
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    
    override suspend fun createItem(item: Item): Result<Item> =
        withContext(ioDispatcher) {
            try {
                val dto = item.toDto()
                val createdDto = remoteDataSource.createItem(dto)
                val entity = createdDto.toEntity()
                dao.upsert(entity)
                Result.success(entity.toDomain())
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    
    override suspend fun deleteItem(id: String): Result<Unit> =
        withContext(ioDispatcher) {
            try {
                remoteDataSource.deleteItem(id)
                dao.deleteById(id)
                Result.success(Unit)
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
}
```

### Sync Strategy Patterns

#### Fetch on Refresh
```kotlin
override suspend fun refreshItems(): Result<Unit> = withContext(ioDispatcher) {
    try {
        val dtos = remoteDataSource.getItems()
        dao.deleteAll()                          // Clear old data
        dao.upsertAll(dtos.map { it.toEntity() })
        Result.success(Unit)
    } catch (e: Exception) {
        Result.failure(e)
    }
}
```

#### Incremental Sync
```kotlin
override suspend fun syncItems(): Result<Unit> = withContext(ioDispatcher) {
    try {
        val lastSyncTime = preferencesDataSource.getLastSyncTime()
        val dtos = remoteDataSource.getItemsSince(lastSyncTime)
        dao.upsertAll(dtos.map { it.toEntity() })
        preferencesDataSource.setLastSyncTime(System.currentTimeMillis())
        Result.success(Unit)
    } catch (e: Exception) {
        Result.failure(e)
    }
}
```

#### Merge Strategy
```kotlin
override suspend fun syncItem(id: String): Result<Unit> = withContext(ioDispatcher) {
    try {
        val localEntity = dao.getById(id)
        val remoteDto = remoteDataSource.getItem(id)
        
        val merged = if (localEntity != null && localEntity.modifiedAt > remoteDto.modifiedAt) {
            // Local is newer, push to server
            val updated = remoteDataSource.updateItem(id, localEntity.toDto())
            updated.toEntity()
        } else {
            // Remote is newer, use it
            remoteDto.toEntity()
        }
        
        dao.upsert(merged)
        Result.success(Unit)
    } catch (e: Exception) {
        Result.failure(e)
    }
}
```

## Mappers

### DTO to Entity
```kotlin
// In core/data or data/remote
internal fun ItemDto.toEntity() = ItemEntity(
    id = id,
    title = title,
    description = description,
    timestamp = timestamp
)

internal fun List<ItemDto>.toEntities() = map { it.toEntity() }
```

### DTO to Domain (Clean Architecture)
```kotlin
// In core/data
internal fun ItemDto.toDomain() = Item(
    id = id,
    title = title,
    description = description,
    timestamp = timestamp
)
```

### Domain/Entity to DTO
```kotlin
internal fun Item.toDto() = ItemDto(
    id = id,
    title = title,
    description = description,
    timestamp = timestamp
)
```

## Error Handling

### Network Error Types
```kotlin
sealed class NetworkError : Exception() {
    data class HttpError(val code: Int, val body: String?) : NetworkError()
    data class NetworkException(val cause: Throwable) : NetworkError()
    data object Timeout : NetworkError()
    data object NoInternet : NetworkError()
    data class Unknown(val cause: Throwable?) : NetworkError()
}
```

### Safe API Call Wrapper
```kotlin
suspend fun <T> safeApiCall(
    apiCall: suspend () -> T
): Result<T> = try {
    Result.success(apiCall())
} catch (e: HttpException) {
    Result.failure(NetworkError.HttpError(e.code(), e.message()))
} catch (e: IOException) {
    if (e is SocketTimeoutException) {
        Result.failure(NetworkError.Timeout)
    } else {
        Result.failure(NetworkError.NetworkException(e))
    }
} catch (e: Exception) {
    Result.failure(NetworkError.Unknown(e))
}

// Usage
override suspend fun refreshItems(): Result<Unit> =
    withContext(ioDispatcher) {
        safeApiCall { remoteDataSource.getItems() }
            .map { dtos ->
                dao.upsertAll(dtos.map { it.toEntity() })
            }
    }
```

### Repository Error Handling
```kotlin
override suspend fun refreshItems(): Result<Unit> = withContext(ioDispatcher) {
    try {
        val response = remoteDataSource.getItems()
        dao.deleteAll()
        dao.upsertAll(response.map { it.toEntity() })
        Result.success(Unit)
    } catch (e: IOException) {
        // Network error - keep cached data, log error
        Log.e("ItemRepository", "Network error during refresh", e)
        Result.failure(e)
    } catch (e: HttpException) {
        // HTTP error - handle based on code
        when (e.code()) {
            401 -> Result.failure(Exception("Unauthorized"))
            404 -> Result.failure(Exception("Not found"))
            else -> Result.failure(Exception("HTTP ${e.code()}: ${e.message()}"))
        }
    } catch (e: Exception) {
        // Unknown error
        Log.e("ItemRepository", "Unknown error during refresh", e)
        Result.failure(e)
    }
}
```

## ViewModel Integration

### Trigger Sync from ViewModel
```kotlin
@HiltViewModel
class HomeViewModel @Inject constructor(
    private val repository: ItemRepository
) : ViewModel() {
    
    private val _isRefreshing = MutableStateFlow(false)
    
    val uiState: StateFlow<HomeUiState> = combine(
        repository.observeItems(),
        _isRefreshing
    ) { items, isRefreshing ->
        HomeUiState.Success(items, isRefreshing)
    }
        .catch { emit(HomeUiState.Error(it.message ?: "Unknown error")) }
        .stateIn(viewModelScope, WhileSubscribed(5_000), HomeUiState.Loading)
    
    fun onAction(action: HomeAction) {
        when (action) {
            HomeAction.Refresh -> refresh()
        }
    }
    
    private fun refresh() {
        viewModelScope.launch {
            _isRefreshing.value = true
            repository.refreshItems()  // Result ignored; Flow updates UI
            _isRefreshing.value = false
        }
    }
}
```

### Show Sync Errors
```kotlin
sealed interface HomeUiState {
    data object Loading : HomeUiState
    data class Success(
        val items: List<Item>,
        val isRefreshing: Boolean = false,
        val syncError: String? = null
    ) : HomeUiState
    data class Error(val message: String) : HomeUiState
}

private fun refresh() {
    viewModelScope.launch {
        _isRefreshing.value = true
        val result = repository.refreshItems()
        _isRefreshing.value = false
        
        result.onFailure { error ->
            _syncError.value = error.message
        }
    }
}
```

## Testing Network Layer

### Test Remote Data Source
Use MockWebServer for integration tests.

```kotlin
@RunWith(AndroidJUnit4::class)
class ItemRemoteDataSourceTest {
    
    private lateinit var mockWebServer: MockWebServer
    private lateinit var remoteDataSource: ItemRemoteDataSource
    
    @Before
    fun setup() {
        mockWebServer = MockWebServer()
        mockWebServer.start()
        
        val retrofit = Retrofit.Builder()
            .baseUrl(mockWebServer.url("/"))
            .addConverterFactory(Json.asConverterFactory("application/json".toMediaType()))
            .build()
        
        remoteDataSource = retrofit.create(ItemRemoteDataSource::class.java)
    }
    
    @After
    fun teardown() {
        mockWebServer.shutdown()
    }
    
    @Test
    fun getItems_returnsItemList() = runTest {
        // Given
        val jsonResponse = """
            [
                {"id": "1", "title": "Item 1", "description": "Desc 1", "timestamp": 123},
                {"id": "2", "title": "Item 2", "description": "Desc 2", "timestamp": 456}
            ]
        """.trimIndent()
        
        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setBody(jsonResponse)
        )
        
        // When
        val items = remoteDataSource.getItems()
        
        // Then
        assertThat(items).hasSize(2)
        assertThat(items[0].id).isEqualTo("1")
    }
}
```

### Test Repository with Test Double
```kotlin
class TestItemRemoteDataSource : ItemRemoteDataSource {
    private var items: List<ItemDto> = emptyList()
    private var error: Throwable? = null
    
    override suspend fun getItems(): List<ItemDto> {
        error?.let { throw it }
        return items
    }
    
    fun setItems(items: List<ItemDto>) {
        this.items = items
        this.error = null
    }
    
    fun setError(error: Throwable) {
        this.error = error
    }
}

// In test
@Test
fun `refreshItems updates database with API data`() = runTest {
    // Given
    val dtos = listOf(testDto1, testDto2)
    remoteDataSource.setItems(dtos)
    
    // When
    val result = repository.refreshItems()
    
    // Then
    assertThat(result.isSuccess).isTrue()
    assertThat(dao.getAll()).hasSize(2)
}
```

## Best Practices Summary

### Do's
- ✅ Use kotlinx.serialization for JSON parsing
- ✅ Make database the source of truth (offline-first)
- ✅ Return `Result<T>` from repository operations
- ✅ Inject `CoroutineDispatcher` for testability
- ✅ Use DTOs for API models, separate from domain/entities
- ✅ Log network errors, don't crash
- ✅ Add timeout configuration to OkHttp
- ✅ Use interceptors for authentication
- ✅ Validate API responses before writing to database

### Don'ts
- ❌ Don't expose network calls to ViewModels
- ❌ Don't parse JSON manually
- ❌ Don't use Gson (prefer kotlinx.serialization)
- ❌ Don't return DTOs from repositories
- ❌ Don't ignore network errors silently
- ❌ Don't block the main thread with network calls
- ❌ Don't cache auth tokens in plain text
- ❌ Don't skip error handling in repositories
- ❌ Don't make UI wait for network responses

## Common Patterns Checklist

- [ ] DTOs annotated with `@Serializable`
- [ ] Retrofit service interface defined
- [ ] NetworkModule provides Retrofit and services
- [ ] Repository uses offline-first pattern
- [ ] Mappers convert DTOs to entities/domain models
- [ ] Error handling wraps all API calls
- [ ] OkHttp configured with timeouts and logging
- [ ] Authentication handled via interceptor
- [ ] ViewModel triggers sync, observes database
- [ ] Tests use test doubles or MockWebServer
