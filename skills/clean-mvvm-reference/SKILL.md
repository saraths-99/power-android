---
name: clean-mvvm-reference
description: Copy-adaptable reference templates for a Clean Architecture + MVVM feature in Jetpack Compose, with a domain layer of use cases and a repository interface owned by domain but implemented in the data layer. Use when adding a Clean-Architecture feature to an existing app, or when you need the per-layer templates (model, use case, repository interface, repository impl, data source, UiState, ViewModel, Compose route/content) following the View → ViewModel → UseCase → Repository → DataSource flow. For a simpler layout without a domain layer, use single-module-mvvm-reference; to bootstrap a whole new project, use create-android-project.
metadata:
  version: "1.0"
  stack: "Android · Kotlin · Jetpack Compose · Material 3 · Coroutines/Flow"
---

# Clean Architecture + MVVM (reference)

Use this skill to add a feature that follows **Clean Architecture with MVVM on
top**. It adds a **domain layer** between the ViewModel and the data layer:
ViewModels depend on **use cases**, and the **repository interface lives in
domain** while its **implementation lives in data**. That inversion is the whole
point — the domain layer stays pure Kotlin with no Android or data dependencies.

## Data flow (single direction, top to bottom)

```
View (UI)                          ← Composable renders UiState, emits events
        │  events ↓        state ↑
ViewModel                          ← holds UiState, calls use cases
        │
UseCase (Domain Layer)             ← one business operation per class
        │
Repository Interface (Domain Layer)← abstraction the domain owns
        │
Repository Implementation (Data Layer) ← concrete impl, maps + coordinates sources
        │
Data Source (Remote / Local)       ← Retrofit/Room/etc., returns DTOs/entities
```

Each arrow is a **compile-time dependency pointing downward only**. The
Repository *Interface* sits in domain; the *Implementation* in data depends
inward on that interface (Dependency Inversion), so data depends on domain, never
the reverse.

## Core rules (do not violate)

1. **Domain is pure Kotlin.** No `android.*`, `androidx.*`, no Retrofit/Room, no
   Compose. Its tests run on the plain JVM.
2. **Dependency direction:** `ui → presentation → domain ← data`. Both UI/
   presentation and data point *inward* at domain. Domain points at nothing.
3. **ViewModels depend on use cases, never on repositories or data sources.**
4. **Repository interface is declared in domain; implemented in data.**
5. **One use case per business operation**, exposed via `operator fun invoke`.
6. **Separate models per layer.** DTOs/entities (data) are mapped to domain
   models; neither DTOs nor entities ever reach the UI.
7. **One immutable `UiState` per screen**; UI is a pure function of it.
8. **Unidirectional data flow:** state down (`StateFlow`), events up (lambdas).
9. **Split each screen into a stateful route + a stateless (previewable) content.**
10. **Async work runs in `viewModelScope`**; expose reactive `Flow`/`StateFlow`.

## Package / module layout

Works as packages in a single module, or as Gradle modules (`domain/`, `data/`,
`app/`) for stricter enforcement. Replace `com.example.app` and `User`/`UserList`.

```
com.example.app
├── domain/                                  # DOMAIN LAYER (pure Kotlin)
│   ├── model/User.kt                        # Domain model
│   ├── repository/UserRepository.kt         # Interface (owned by domain)
│   └── usecase/GetUsersUseCase.kt           # One operation per class
├── data/                                    # DATA LAYER
│   ├── remote/UserRemoteDataSource.kt       # Network source (returns DTOs)
│   ├── remote/dto/UserDto.kt
│   ├── local/UserLocalDataSource.kt         # Optional cache/DB (entities)
│   ├── mapper/UserMappers.kt                # DTO/entity ↔ domain model
│   └── repository/UserRepositoryImpl.kt     # Implements domain interface
├── presentation/                            # VIEWMODEL LAYER
│   ├── UserListUiState.kt
│   └── UserListViewModel.kt
├── ui/                                      # VIEW LAYER
│   ├── UserListScreen.kt                    # Route + Content + previews
│   └── theme/Theme.kt
└── di/AppModule.kt                          # Manual DI (or Hilt)
```

## Request-flow contract

1. Route Composable obtains the ViewModel; the ViewModel is given its use case(s).
2. ViewModel sets `isLoading = true`, calls the use case in `viewModelScope`.
3. Use case invokes the repository *interface* and applies any business logic.
4. Repository *implementation* pulls from data source(s), maps DTOs/entities →
   domain models, returns them (or throws / emits an error).
5. ViewModel maps the domain result → new `UiState`, emits on `StateFlow`.
6. Route collects with `collectAsStateWithLifecycle()`, passes state + event
   callbacks to the stateless Content, which renders loading / success / error.

---

## Templates

### 1. Domain model — `domain/model/User.kt`

```kotlin
package com.example.app.domain.model

// Pure Kotlin. No framework imports ever.
data class User(
    val id: Int,
    val name: String,
    val email: String
)
```

### 2. Repository interface — `domain/repository/UserRepository.kt`

```kotlin
package com.example.app.domain.repository

import com.example.app.domain.model.User

/**
 * Declared in the DOMAIN layer. The data layer implements it, so the dependency
 * points inward (Dependency Inversion). Expose reactive streams where it makes
 * sense; a suspend getter is fine for one-shot reads.
 */
interface UserRepository {
    suspend fun getUsers(): List<User>
}
```

### 3. Use case — `domain/usecase/GetUsersUseCase.kt`

```kotlin
package com.example.app.domain.usecase

import com.example.app.domain.model.User
import com.example.app.domain.repository.UserRepository

/**
 * One business operation. The ViewModel calls this, never the repository
 * directly. Invoked like a function: getUsers().
 */
class GetUsersUseCase(
    private val userRepository: UserRepository
) {
    suspend operator fun invoke(): List<User> {
        // Business rules go here (filtering, sorting, combining sources, ...).
        return userRepository.getUsers().sortedBy { it.name }
    }
}
```

### 4. DTO — `data/remote/dto/UserDto.kt`

```kotlin
package com.example.app.data.remote.dto

// Wire model. Stays in the data layer; never reaches domain or UI.
data class UserDto(
    val id: Int,
    val fullName: String,
    val email: String
)
```

### 5. Mappers — `data/mapper/UserMappers.kt`

```kotlin
package com.example.app.data.mapper

import com.example.app.data.remote.dto.UserDto
import com.example.app.domain.model.User

fun UserDto.toDomain(): User = User(
    id = id,
    name = fullName,
    email = email
)
```

### 6. Remote data source — `data/remote/UserRemoteDataSource.kt`

```kotlin
package com.example.app.data.remote

import com.example.app.data.remote.dto.UserDto

class UserRemoteDataSource {
    suspend fun fetchUsers(): List<UserDto> {
        // Real impl: call Retrofit/Ktor here and return DTOs.
        TODO("Fetch from network")
    }
}
```

### 7. Repository implementation — `data/repository/UserRepositoryImpl.kt`

```kotlin
package com.example.app.data.repository

import com.example.app.data.mapper.toDomain
import com.example.app.data.remote.UserRemoteDataSource
import com.example.app.domain.model.User
import com.example.app.domain.repository.UserRepository

/**
 * Lives in the DATA layer, implements the DOMAIN interface. Coordinates data
 * sources and maps DTOs/entities → domain models. This is the only place that
 * knows about both DTOs and domain models.
 */
class UserRepositoryImpl(
    private val remoteDataSource: UserRemoteDataSource
) : UserRepository {
    override suspend fun getUsers(): List<User> =
        remoteDataSource.fetchUsers().map { it.toDomain() }
}
```

### 8. UI state — `presentation/UserListUiState.kt`

```kotlin
package com.example.app.presentation

import com.example.app.domain.model.User

data class UserListUiState(
    val isLoading: Boolean = false,
    val users: List<User> = emptyList(),
    val errorMessage: String? = null
)
```

### 9. ViewModel — `presentation/UserListViewModel.kt`

```kotlin
package com.example.app.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.app.domain.usecase.GetUsersUseCase
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * Depends on the USE CASE, not the repository. Contains no Android UI types.
 */
class UserListViewModel(
    private val getUsers: GetUsersUseCase
) : ViewModel() {

    private val _uiState = MutableStateFlow(UserListUiState())
    val uiState: StateFlow<UserListUiState> = _uiState.asStateFlow()

    init { loadUsers() }

    fun loadUsers() {
        _uiState.update { it.copy(isLoading = true, errorMessage = null) }
        viewModelScope.launch {
            try {
                val users = getUsers()
                _uiState.update { it.copy(isLoading = false, users = users) }
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(isLoading = false, errorMessage = e.message ?: "Something went wrong")
                }
            }
        }
    }
}
```

### 10. ViewModel factory — `presentation/UserListViewModelFactory.kt`

```kotlin
package com.example.app.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.example.app.domain.usecase.GetUsersUseCase

class UserListViewModelFactory(
    private val getUsers: GetUsersUseCase
) : ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(UserListViewModel::class.java)) {
            return UserListViewModel(getUsers) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class: ${modelClass.name}")
    }
}
```

### 11. Screen (route + stateless content + preview) — `ui/UserListScreen.kt`

```kotlin
package com.example.app.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.app.di.AppModule
import com.example.app.domain.model.User
import com.example.app.presentation.UserListUiState
import com.example.app.presentation.UserListViewModel
import com.example.app.presentation.UserListViewModelFactory

@Composable
fun UserListRoute(
    viewModel: UserListViewModel = viewModel(
        factory = UserListViewModelFactory(AppModule.getUsersUseCase)
    )
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    UserListContent(uiState = uiState, onRetry = viewModel::loadUsers)
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun UserListContent(uiState: UserListUiState, onRetry: () -> Unit) {
    Scaffold(topBar = { TopAppBar(title = { Text("Users") }) }) { padding ->
        Box(Modifier.fillMaxSize().padding(padding), contentAlignment = Alignment.Center) {
            when {
                uiState.isLoading -> CircularProgressIndicator()
                uiState.errorMessage != null -> Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    Text(uiState.errorMessage, color = MaterialTheme.colorScheme.error)
                    Button(onClick = onRetry) { Text("Retry") }
                }
                else -> LazyColumn(
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(uiState.users, key = { it.id }) { user ->
                        Card { Column(Modifier.padding(16.dp)) {
                            Text(user.name, style = MaterialTheme.typography.titleMedium)
                            Text(user.email, style = MaterialTheme.typography.bodyMedium)
                        } }
                    }
                }
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun SuccessPreview() = UserListContent(
    UserListUiState(users = listOf(User(1, "Ada Lovelace", "ada@example.com"))), onRetry = {}
)
```

### 12. Manual DI — `di/AppModule.kt`

```kotlin
package com.example.app.di

import com.example.app.data.remote.UserRemoteDataSource
import com.example.app.data.repository.UserRepositoryImpl
import com.example.app.domain.repository.UserRepository
import com.example.app.domain.usecase.GetUsersUseCase

/**
 * Wires data → domain. Note the type is the domain interface, the instance is
 * the data impl. Swap for Hilt in production (@Module providing the interface).
 */
object AppModule {
    private val remoteDataSource by lazy { UserRemoteDataSource() }
    private val userRepository: UserRepository by lazy { UserRepositoryImpl(remoteDataSource) }
    val getUsersUseCase by lazy { GetUsersUseCase(userRepository) }
}
```

### 13. Entry point — `MainActivity.kt`

```kotlin
package com.example.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.example.app.ui.UserListRoute
import com.example.app.ui.theme.AppTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AppTheme {
                Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                    UserListRoute()
                }
            }
        }
    }
}
```

---

## Recommended dependencies (`app/build.gradle.kts`)

- `androidx.activity:activity-compose`
- Compose BOM + `compose.ui`, `compose.material3`, `compose.ui.tooling-preview`
- `androidx.lifecycle:lifecycle-viewmodel-compose`
- `androidx.lifecycle:lifecycle-runtime-compose` (for `collectAsStateWithLifecycle`)
- `org.jetbrains.kotlinx:kotlinx-coroutines-android`
- `debugImplementation` `compose.ui.tooling`
- (multi-module) put `domain` as a pure `java-library`/`kotlin` module with no
  Android dependencies; `data` and `app` depend on `domain`.

## Adapting the template for a new feature

1. Replace `com.example.app` and `User`/`UserList` with the real package/entity.
2. Add one use case per operation the screen needs; keep business logic in use
   cases, not the ViewModel or repository impl.
3. Declare repository methods on the domain interface; implement in data.
4. Add a DTO/entity + mapper per data source; never leak them past the repository.
5. Extend `UiState` with only what the screen renders; add event callbacks for
   each user action, routed to public ViewModel functions.
6. If DI grows, migrate `AppModule` → Hilt (`@Module` binding the interface to the
   impl, `@HiltViewModel` injecting use cases).

## Checklist before considering a feature done

- [ ] Domain layer imports no `android.`/`androidx.`/Retrofit/Room/Compose.
- [ ] Dependency direction respected: `ui → presentation → domain ← data`.
- [ ] ViewModel depends on use case(s), not on the repository or data source.
- [ ] Repository interface in domain, implementation in data.
- [ ] Use cases hold the business logic; one operation per class.
- [ ] DTOs/entities mapped to domain models; neither reaches the UI.
- [ ] Exactly one `UiState`; stateful route + stateless previewable content.
- [ ] Async work runs in `viewModelScope`; state exposed as read-only `StateFlow`.
```
