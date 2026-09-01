# Single-Module MVVM (feature reference)

Copy-adaptable reference templates for adding a feature to an Android app that
follows **MVVM** inside a **single Gradle module** (`:app`) — either a project
this skill scaffolded with `architecture: mvvm`, or any other single-module MVVM
app. It defines the layer boundaries, the package layout, the dependency
direction, and copy-adaptable templates for each layer.

For the module/Gradle wiring a new feature needs (route registration, package
creation), see `post-setup.md` §"Adding a second feature" › `mvvm`. This file
covers the per-layer code that goes inside that package.

## Core rules (do not violate)

1. **Dependency direction is one-way: `ui → presentation → data`.** A lower layer
   must never import an upper one.
2. **ViewModels must not import Android UI types** (`Context`, `View`, anything from
   `androidx.compose.*`). They expose state and receive events only.
3. **The ViewModel depends on a repository *interface*, never a concrete data source.**
4. **One immutable `UiState` per screen** is the single source of truth. The UI is a
   pure function of that state.
5. **Unidirectional data flow (UDF):** state flows down (`StateFlow`), events flow up
   (lambda callbacks like `onRetry`).
6. **Split each screen into a stateful route + a stateless content Composable.** Only
   the stateless one is used in `@Preview`.
7. **Run async work in `viewModelScope`**; expose state with `StateFlow`, collect it
   with `collectAsStateWithLifecycle()`.

## Package layout (single module `:app`)

Replace `com.example.app` with the project package and `<Feature>` with the feature
name (e.g. `UserList`).

```
com.example.app
├── MainActivity.kt                    # Entry point; sets Compose content only
├── data/                              # MODEL layer
│   ├── model/<Entity>.kt              # Immutable domain models
│   ├── source/<Entity>RemoteDataSource.kt   # Network/DB source(s)
│   └── repository/
│       ├── <Entity>Repository.kt      # Interface (abstraction)
│       └── <Entity>RepositoryImpl.kt  # Concrete implementation
├── presentation/                      # VIEWMODEL layer
│   ├── <Feature>UiState.kt            # Single immutable screen state
│   ├── <Feature>ViewModel.kt          # State holder + presentation logic
│   └── <Feature>ViewModelFactory.kt   # Injects dependencies (or use Hilt)
├── ui/                                # VIEW layer
│   ├── <Feature>Screen.kt             # Route (stateful) + Content (stateless) + previews
│   └── theme/Theme.kt
└── di/AppModule.kt                    # Manual DI container (or replace with Hilt/Koin)
```

## Request-flow contract

1. Route Composable obtains the ViewModel via a factory that injects the repository.
2. ViewModel sets `isLoading = true`, launches in `viewModelScope`.
3. Repository delegates to its data source(s), returns domain models (or throws).
4. ViewModel maps result → new `UiState`, emits on `StateFlow`.
5. Route collects with `collectAsStateWithLifecycle()`, passes state + event callbacks
   to the stateless Content, which renders the matching branch (loading / success / error).

---

## Templates

### 1. Domain model — `data/model/<Entity>.kt`

```kotlin
package com.example.app.data.model

data class User(
    val id: Int,
    val name: String,
    val email: String
)
```

### 2. Data source — `data/source/<Entity>RemoteDataSource.kt`

```kotlin
package com.example.app.data.source

import com.example.app.data.model.User

class UserRemoteDataSource {
    suspend fun fetchUsers(): List<User> {
        // Real impl: call Retrofit/Ktor here and map DTOs → domain models.
        TODO("Fetch from network")
    }
}
```

### 3. Repository interface — `data/repository/<Entity>Repository.kt`

```kotlin
package com.example.app.data.repository

import com.example.app.data.model.User

/** Abstraction the ViewModel depends on. Hides *where* data comes from. */
interface UserRepository {
    suspend fun getUsers(): List<User>
}
```

### 4. Repository impl — `data/repository/<Entity>RepositoryImpl.kt`

```kotlin
package com.example.app.data.repository

import com.example.app.data.model.User
import com.example.app.data.source.UserRemoteDataSource

class UserRepositoryImpl(
    private val remoteDataSource: UserRemoteDataSource
) : UserRepository {
    override suspend fun getUsers(): List<User> = remoteDataSource.fetchUsers()
}
```

### 5. UI state — `presentation/<Feature>UiState.kt`

```kotlin
package com.example.app.presentation

import com.example.app.data.model.User

/** Single source of truth for the screen. UI is a pure function of this. */
data class UserListUiState(
    val isLoading: Boolean = false,
    val users: List<User> = emptyList(),
    val errorMessage: String? = null
)
```

### 6. ViewModel — `presentation/<Feature>ViewModel.kt`

```kotlin
package com.example.app.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.app.data.repository.UserRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class UserListViewModel(
    private val userRepository: UserRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(UserListUiState())
    val uiState: StateFlow<UserListUiState> = _uiState.asStateFlow()

    init { loadUsers() }

    fun loadUsers() {
        _uiState.update { it.copy(isLoading = true, errorMessage = null) }
        viewModelScope.launch {
            try {
                val users = userRepository.getUsers()
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

### 7. ViewModel factory — `presentation/<Feature>ViewModelFactory.kt`

```kotlin
package com.example.app.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.example.app.data.repository.UserRepository

class UserListViewModelFactory(
    private val userRepository: UserRepository
) : ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(UserListViewModel::class.java)) {
            return UserListViewModel(userRepository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class: ${modelClass.name}")
    }
}
```

### 8. Screen (route + stateless content + previews) — `ui/<Feature>Screen.kt`

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
import com.example.app.data.model.User
import com.example.app.di.AppModule
import com.example.app.presentation.UserListUiState
import com.example.app.presentation.UserListViewModel
import com.example.app.presentation.UserListViewModelFactory

// Stateful route: wires ViewModel state down, events up. No UI logic.
@Composable
fun UserListRoute(
    viewModel: UserListViewModel = viewModel(
        factory = UserListViewModelFactory(AppModule.userRepository)
    )
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    UserListContent(uiState = uiState, onRetry = viewModel::loadUsers)
}

// Stateless content: pure function of state → fully previewable.
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

### 9. Manual DI — `di/AppModule.kt`

```kotlin
package com.example.app.di

import com.example.app.data.repository.UserRepository
import com.example.app.data.repository.UserRepositoryImpl
import com.example.app.data.source.UserRemoteDataSource

/** Minimal service locator. Swap for Hilt/Koin in production. */
object AppModule {
    private val remoteDataSource by lazy { UserRemoteDataSource() }
    val userRepository: UserRepository by lazy { UserRepositoryImpl(remoteDataSource) }
}
```

### 10. Entry point — `MainActivity.kt`

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

## Adapting the template for a new feature

1. Replace `com.example.app` with the real package and `User`/`UserList` with the entity/feature.
2. Add repository methods for the feature's data needs; keep the interface minimal.
3. Extend `UiState` with only the fields the screen renders.
4. Add event callbacks to the Content signature for every user action; route them to
   public ViewModel functions.
5. If dependencies grow, migrate `AppModule` → Hilt (`@HiltViewModel`, `@Module`).

## Checklist before considering a feature done

- [ ] Dependency direction respected (`ui → presentation → data`).
- [ ] ViewModel has zero `androidx.compose.*` / `Context` imports.
- [ ] ViewModel depends on the repository interface, not the impl or data source.
- [ ] Exactly one `UiState`; UI branches only on it.
- [ ] Stateful route + stateless content split; at least one `@Preview` on content.
- [ ] Async work runs in `viewModelScope`; state exposed as read-only `StateFlow`.
