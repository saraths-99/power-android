---
inclusion: auto
name: navigation
description: Navigation patterns for Jetpack Compose Navigation. Use when implementing navigation, routes, or screen transitions.
---

# Navigation Patterns

Generated projects use **Jetpack Compose Navigation** with a type-safe, extension-based approach. Navigation logic lives outside ViewModels and screens, following unidirectional data flow principles.

## Core Concepts

### Navigation is Event-Driven
Navigation happens in response to UI events, not as side effects from ViewModels. Screens emit navigation events upward; the NavHost handles routing.

```
User Action → Screen Event → NavHost → Navigate to Destination
```

**ViewModels never navigate.** They manage business logic and state; navigation is UI concern.

## Route Definitions

### Route Constants
Each feature defines its route as a top-level constant in its navigation file.

```kotlin
// feature/home/navigation/HomeNavigation.kt
const val HOME_ROUTE = "home"

// feature/profile/navigation/ProfileNavigation.kt
const val PROFILE_ROUTE = "profile"

// feature/details/navigation/DetailsNavigation.kt
private const val DETAILS_ROUTE_BASE = "details"
private const val DETAILS_ARG_ID = "itemId"
const val DETAILS_ROUTE = "$DETAILS_ROUTE_BASE/{$DETAILS_ARG_ID}"
```

### Route Patterns

#### Simple Routes (No Arguments)
```kotlin
const val HOME_ROUTE = "home"
```

#### Routes with Required Arguments
```kotlin
private const val DETAILS_ROUTE_BASE = "details"
private const val DETAILS_ARG_ID = "itemId"
const val DETAILS_ROUTE = "$DETAILS_ROUTE_BASE/{$DETAILS_ARG_ID}"

// Usage in NavHost
composable(route = DETAILS_ROUTE) { backStackEntry ->
    val itemId = backStackEntry.arguments?.getString(DETAILS_ARG_ID)
    DetailsRoute(itemId = itemId ?: "")
}
```

#### Routes with Optional Arguments
```kotlin
private const val SEARCH_ROUTE_BASE = "search"
private const val SEARCH_ARG_QUERY = "query"
const val SEARCH_ROUTE = "$SEARCH_ROUTE_BASE?$SEARCH_ARG_QUERY={$SEARCH_ARG_QUERY}"

// Usage
composable(
    route = SEARCH_ROUTE,
    arguments = listOf(
        navArgument(SEARCH_ARG_QUERY) {
            type = NavType.StringType
            defaultValue = ""
        }
    )
) { backStackEntry ->
    val query = backStackEntry.arguments?.getString(SEARCH_ARG_QUERY) ?: ""
    SearchRoute(initialQuery = query)
}
```

## Navigation Extensions

### Extension Functions on NavController
Each feature provides extension functions to navigate to it. This keeps navigation logic DRY and type-safe.

```kotlin
// feature/home/navigation/HomeNavigation.kt
fun NavController.navigateToHome(navOptions: NavOptions? = null) {
    navigate(HOME_ROUTE, navOptions)
}

// feature/details/navigation/DetailsNavigation.kt
fun NavController.navigateToDetails(itemId: String, navOptions: NavOptions? = null) {
    navigate("$DETAILS_ROUTE_BASE/$itemId", navOptions)
}

// feature/profile/navigation/ProfileNavigation.kt
fun NavController.navigateToProfile(
    navOptions: NavOptions? = null
) {
    navigate(PROFILE_ROUTE, navOptions)
}
```

### Benefits
- **Type-safe:** Arguments are function parameters, not string manipulation
- **Encapsulated:** Route construction logic in one place
- **Discoverable:** IDE autocomplete shows all navigation options
- **Refactorable:** Renaming a function updates all callers

## NavHost Setup

### MVVM Architecture (Single Module)
NavHost lives in `MainActivity.kt` or a separate `navigation/AppNavHost.kt` file.

```kotlin
// MainActivity.kt or navigation/AppNavHost.kt
@Composable
fun AppNavHost(
    navController: NavHostController,
    modifier: Modifier = Modifier
) {
    NavHost(
        navController = navController,
        startDestination = HOME_ROUTE,
        modifier = modifier
    ) {
        composable(route = HOME_ROUTE) {
            HomeRoute(
                onItemClick = { itemId ->
                    navController.navigateToDetails(itemId)
                }
            )
        }
        
        composable(route = DETAILS_ROUTE) { backStackEntry ->
            val itemId = backStackEntry.arguments?.getString(DETAILS_ARG_ID) ?: ""
            DetailsRoute(
                onBackClick = { navController.popBackStack() }
            )
        }
        
        composable(route = PROFILE_ROUTE) {
            ProfileRoute(
                onBackClick = { navController.popBackStack() }
            )
        }
    }
}
```

### Clean Architecture (Multi-Module)
NavHost lives in `app` module at `navigation/<AppName>NavHost.kt`.

```kotlin
// app/src/main/kotlin/com/example/app/navigation/AppNavHost.kt
@Composable
fun AppNavHost(
    navController: NavHostController,
    modifier: Modifier = Modifier
) {
    NavHost(
        navController = navController,
        startDestination = HOME_ROUTE,
        modifier = modifier
    ) {
        homeScreen(
            onItemClick = navController::navigateToDetails
        )
        
        detailsScreen(
            onBackClick = navController::popBackStack
        )
        
        profileScreen(
            onBackClick = navController::popBackStack
        )
    }
}
```

Each feature provides a `NavGraphBuilder` extension to add itself to the graph:

```kotlin
// feature/home/navigation/HomeNavigation.kt
fun NavGraphBuilder.homeScreen(
    onItemClick: (String) -> Unit
) {
    composable(route = HOME_ROUTE) {
        HomeRoute(onItemClick = onItemClick)
    }
}

// feature/details/navigation/DetailsNavigation.kt
fun NavGraphBuilder.detailsScreen(
    onBackClick: () -> Unit
) {
    composable(route = DETAILS_ROUTE) { backStackEntry ->
        val itemId = backStackEntry.arguments?.getString(DETAILS_ARG_ID) ?: ""
        DetailsRoute(
            itemId = itemId,
            onBackClick = onBackClick
        )
    }
}
```

**Benefits:**
- Feature modules don't depend on each other
- `app` module wires navigation together
- Each feature is self-contained

## Passing Navigation Callbacks

### From Screen to Caller
Screens receive navigation callbacks as parameters. They emit events; they don't navigate.

```kotlin
@Composable
internal fun HomeRoute(
    onItemClick: (String) -> Unit,
    onProfileClick: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: HomeViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    
    HomeScreen(
        uiState = uiState,
        onItemClick = onItemClick,
        onProfileClick = onProfileClick,
        onAction = viewModel::onAction,
        modifier = modifier
    )
}

@Composable
internal fun HomeScreen(
    uiState: HomeUiState,
    onItemClick: (String) -> Unit,
    onProfileClick: () -> Unit,
    onAction: (HomeAction) -> Unit,
    modifier: Modifier = Modifier
) {
    // UI calls onItemClick("123") or onProfileClick()
    // NavHost handles actual navigation
}
```

### In NavHost
NavHost receives `NavController` and passes navigation lambdas to screens.

```kotlin
NavHost(navController = navController, ...) {
    composable(HOME_ROUTE) {
        HomeRoute(
            onItemClick = { itemId -> navController.navigateToDetails(itemId) },
            onProfileClick = { navController.navigateToProfile() }
        )
    }
}
```

## Navigation Options

### Pop Behavior
Use `NavOptions` for custom back stack behavior.

```kotlin
// Pop up to home and clear back stack
navController.navigateToHome(
    navOptions = navOptions {
        popUpTo(HOME_ROUTE) { inclusive = true }
    }
)

// Replace current screen (like "login -> home" after auth)
navController.navigateToHome(
    navOptions = navOptions {
        popUpTo(LOGIN_ROUTE) { inclusive = true }
        launchSingleTop = true
    }
)

// Single instance of a screen
navController.navigateToDetails(
    itemId = itemId,
    navOptions = navOptions {
        launchSingleTop = true
    }
)
```

### Common Patterns

#### Bottom Navigation
Keep only one instance of each tab in back stack.

```kotlin
BottomNavigationItem(
    selected = currentRoute == HOME_ROUTE,
    onClick = {
        navController.navigateToHome(
            navOptions = navOptions {
                popUpTo(navController.graph.findStartDestination().id) {
                    saveState = true
                }
                launchSingleTop = true
                restoreState = true
            }
        )
    }
)
```

#### Single Top
Avoid duplicate screens when navigating to the same destination.

```kotlin
fun NavController.navigateToSearch(
    query: String = "",
    navOptions: NavOptions? = navOptions {
        launchSingleTop = true
    }
) {
    val route = if (query.isBlank()) {
        SEARCH_ROUTE_BASE
    } else {
        "$SEARCH_ROUTE_BASE?$SEARCH_ARG_QUERY=$query"
    }
    navigate(route, navOptions)
}
```

## Deep Linking

### Define Deep Links
Add deep links in `NavGraphBuilder` extensions.

```kotlin
fun NavGraphBuilder.detailsScreen(
    onBackClick: () -> Unit
) {
    composable(
        route = DETAILS_ROUTE,
        deepLinks = listOf(
            navDeepLink { uriPattern = "myapp://details/{$DETAILS_ARG_ID}" }
        )
    ) { backStackEntry ->
        val itemId = backStackEntry.arguments?.getString(DETAILS_ARG_ID) ?: ""
        DetailsRoute(itemId = itemId, onBackClick = onBackClick)
    }
}
```

### Manifest Declaration
Add intent filter in `AndroidManifest.xml`.

```xml
<activity android:name=".MainActivity">
    <intent-filter>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="myapp" android:host="details" />
    </intent-filter>
</activity>
```

## Nested Navigation

### Nested Graphs
Group related screens into nested graphs.

```kotlin
fun NavGraphBuilder.authGraph(
    navController: NavController,
    onAuthComplete: () -> Unit
) {
    navigation(
        startDestination = LOGIN_ROUTE,
        route = "auth"
    ) {
        composable(LOGIN_ROUTE) {
            LoginRoute(
                onLoginSuccess = onAuthComplete,
                onSignUpClick = { navController.navigateToSignUp() }
            )
        }
        
        composable(SIGNUP_ROUTE) {
            SignUpRoute(
                onSignUpSuccess = onAuthComplete,
                onBackClick = { navController.popBackStack() }
            )
        }
    }
}

// In NavHost
NavHost(...) {
    authGraph(
        navController = navController,
        onAuthComplete = { navController.navigateToHome() }
    )
    
    homeScreen(...)
}
```

## ViewModel and Navigation

### ViewModels Do Not Navigate
ViewModels emit state, not navigation events.

```kotlin
// ✗ Avoid - ViewModel shouldn't know about navigation
@HiltViewModel
class HomeViewModel @Inject constructor(...) : ViewModel() {
    fun onItemClick(itemId: String) {
        // Don't do: navController.navigate(...)
    }
}

// ✓ Good - Screen handles navigation
@Composable
fun HomeRoute(
    onItemClick: (String) -> Unit,
    viewModel: HomeViewModel = hiltViewModel()
) {
    HomeScreen(
        uiState = viewModel.uiState,
        onItemClick = onItemClick  // Passed through
    )
}
```

### One-Time Events
For scenarios where ViewModel must trigger navigation (e.g., after async operation), use a single-event pattern.

```kotlin
// UiState includes navigation event
sealed interface LoginUiState {
    data object Idle : LoginUiState
    data object Loading : LoginUiState
    data object Success : LoginUiState  // Triggers navigation
    data class Error(val message: String) : LoginUiState
}

// Screen observes and consumes
@Composable
fun LoginRoute(
    onLoginSuccess: () -> Unit,
    viewModel: LoginViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    
    LaunchedEffect(uiState) {
        if (uiState is LoginUiState.Success) {
            onLoginSuccess()
        }
    }
    
    LoginScreen(...)
}
```

## Back Stack Management

### Handle System Back
`NavController` automatically handles system back. No extra code needed.

### Programmatic Back
```kotlin
// Go back one screen
navController.popBackStack()

// Go back to specific destination
navController.popBackStack(route = HOME_ROUTE, inclusive = false)

// Check if can go back
if (navController.previousBackStackEntry != null) {
    navController.popBackStack()
} else {
    // At root, maybe finish activity
}
```

### Prevent Back
Use `BackHandler` to intercept back press.

```kotlin
@Composable
fun EditScreen(
    hasUnsavedChanges: Boolean,
    onBackClick: () -> Unit
) {
    var showDialog by remember { mutableStateOf(false) }
    
    BackHandler(enabled = hasUnsavedChanges) {
        showDialog = true
    }
    
    if (showDialog) {
        AlertDialog(
            onDismissRequest = { showDialog = false },
            title = { Text("Unsaved changes") },
            text = { Text("Discard changes?") },
            confirmButton = {
                TextButton(onClick = { onBackClick() }) {
                    Text("Discard")
                }
            },
            dismissButton = {
                TextButton(onClick = { showDialog = false }) {
                    Text("Cancel")
                }
            }
        )
    }
}
```

## Testing Navigation

### Test Navigation Logic
Use `TestNavHostController` in tests.

```kotlin
@Test
fun `when item clicked then navigates to details`() {
    val navController = TestNavHostController(ApplicationProvider.getApplicationContext())
    
    composeTestRule.setContent {
        navController.navigatorProvider.addNavigator(ComposeNavigator())
        NavHost(navController = navController, startDestination = HOME_ROUTE) {
            composable(HOME_ROUTE) {
                HomeScreen(
                    uiState = HomeUiState.Success(listOf(item)),
                    onItemClick = { navController.navigateToDetails(it) }
                )
            }
        }
    }
    
    composeTestRule.onNodeWithText("Item Title").performClick()
    
    assertThat(navController.currentDestination?.route).isEqualTo(DETAILS_ROUTE)
}
```

### Test Screens Without Navigation
Pass lambdas that record calls.

```kotlin
@Test
fun `when item clicked then callback invoked`() {
    var clickedItemId: String? = null
    
    composeTestRule.setContent {
        HomeScreen(
            uiState = HomeUiState.Success(listOf(testItem)),
            onItemClick = { clickedItemId = it },
            onAction = {}
        )
    }
    
    composeTestRule.onNodeWithText("Test Item").performClick()
    
    assertThat(clickedItemId).isEqualTo("test-id")
}
```

## Common Pitfalls

### Don't: Pass NavController to Screens
❌ Screens shouldn't depend on `NavController`.

```kotlin
// ✗ Avoid
@Composable
fun HomeScreen(navController: NavController) {
    Button(onClick = { navController.navigateToDetails("123") })
}
```

✅ Pass callbacks instead.

```kotlin
// ✓ Good
@Composable
fun HomeScreen(onItemClick: (String) -> Unit) {
    Button(onClick = { onItemClick("123") })
}
```

### Don't: Navigate in ViewModel Directly
❌ ViewModels shouldn't hold `NavController` or navigate.

```kotlin
// ✗ Avoid
@HiltViewModel
class HomeViewModel @Inject constructor(
    private val navController: NavController  // Wrong!
) : ViewModel()
```

✅ Use state or one-time events.

### Don't: Forget to Handle Configuration Changes
✅ `NavHost` and `rememberNavController()` handle this automatically. No extra code needed.

## Summary

### Navigation Checklist
- [ ] Route constants defined at top level
- [ ] Extension functions for type-safe navigation
- [ ] Screens receive callbacks, not `NavController`
- [ ] ViewModels don't navigate directly
- [ ] Arguments extracted from `BackStackEntry`
- [ ] `NavGraphBuilder` extensions for features (Clean Architecture)
- [ ] Deep links configured with intent filters
- [ ] Back stack managed with `NavOptions`
- [ ] Navigation tested with `TestNavHostController`

### File Organization

**MVVM:**
```
app/src/main/kotlin/com/example/app/
├── ui/
│   ├── home/
│   │   ├── HomeScreen.kt
│   │   ├── HomeViewModel.kt
│   │   └── navigation/
│   │       └── HomeNavigation.kt
│   └── details/
│       └── ...
└── MainActivity.kt  (or navigation/AppNavHost.kt)
```

**Clean Architecture:**
```
feature/home/src/main/kotlin/com/example/app/feature/home/
├── HomeScreen.kt
├── HomeViewModel.kt
└── navigation/
    └── HomeNavigation.kt

app/src/main/kotlin/com/example/app/
└── navigation/
    └── AppNavHost.kt
```
