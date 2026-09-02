# {{PROJECT_NAME}} — Navigation

Describes how screens and navigation work in this project using Jetpack Compose
Navigation.

## 1. Navigation structure

{{NAV_STRUCTURE}}

## 2. Navigation graph location

The navigation graph is defined in {{NAV_GRAPH_LOCATION}}:

```kotlin
@Composable
fun {{APP_CLASS}}NavHost(
    navController: NavHostController,
    modifier: Modifier = Modifier,
) {
    NavHost(
        navController = navController,
        startDestination = {{INITIAL_FEATURE_UPPER}}_ROUTE,
        modifier = modifier,
    ) {
        {{INITIAL_FEATURE}}Screen(
            onNavigateToDetail: { id ->
                navController.navigate("detail/$id")
            },
        )
        
        // Add more destinations here
    }
}
```

Called from `MainActivity`:

```kotlin
setContent {
    {{APP_CLASS}}Theme {
        val navController = rememberNavController()
        {{APP_CLASS}}NavHost(navController = navController)
    }
}
```

## 3. Route definitions

Each feature defines its own route constant in its navigation file:

{{FEATURE_NAV_LOCATION}}

```kotlin
const val {{INITIAL_FEATURE_UPPER}}_ROUTE = "{{INITIAL_FEATURE}}"

fun NavGraphBuilder.{{INITIAL_FEATURE}}Screen(
    onNavigateToDetail: (String) -> Unit,
) {
    composable(route = {{INITIAL_FEATURE_UPPER}}_ROUTE) {
        {{INITIAL_FEATURE_PASCAL}}Route(
            onItemClick = onNavigateToDetail,
        )
    }
}
```

**Rules:**
- Route constants are `const val` in SCREAMING_SNAKE_CASE
- Extension functions on `NavGraphBuilder` set up each destination
- Features receive navigation callbacks, never `NavController` directly

## 4. Navigation patterns

### Simple navigation (no arguments)
```kotlin
// Define route
const val PROFILE_ROUTE = "profile"

fun NavGraphBuilder.profileScreen(onBack: () -> Unit) {
    composable(route = PROFILE_ROUTE) {
        ProfileRoute(onBack = onBack)
    }
}

// Navigate
navController.navigate(PROFILE_ROUTE)
```

### Navigation with arguments
```kotlin
// Define route with placeholder
const val DETAIL_ROUTE = "detail/{itemId}"

fun NavGraphBuilder.detailScreen(onBack: () -> Unit) {
    composable(
        route = DETAIL_ROUTE,
        arguments = listOf(
            navArgument("itemId") { type = NavType.StringType }
        )
    ) { backStackEntry ->
        val itemId = backStackEntry.arguments?.getString("itemId") ?: return@composable
        DetailRoute(
            itemId = itemId,
            onBack = onBack,
        )
    }
}

// Navigate with argument
navController.navigate("detail/$itemId")
```

### Optional arguments
```kotlin
const val SEARCH_ROUTE = "search?query={query}"

fun NavGraphBuilder.searchScreen() {
    composable(
        route = SEARCH_ROUTE,
        arguments = listOf(
            navArgument("query") {
                type = NavType.StringType
                nullable = true
                defaultValue = null
            }
        )
    ) { backStackEntry ->
        val query = backStackEntry.arguments?.getString("query")
        SearchRoute(initialQuery = query)
    }
}

// Navigate with optional argument
navController.navigate("search?query=$query")  // With query
navController.navigate("search")  // Without query
```

### Type-safe navigation with custom types
For complex arguments, use custom NavType:

```kotlin
object ItemNavType : NavType<Item>(isNullableAllowed = false) {
    override fun put(bundle: Bundle, key: String, value: Item) {
        bundle.putString(key, Json.encodeToString(value))
    }

    override fun get(bundle: Bundle, key: String): Item {
        return Json.decodeFromString(bundle.getString(key)!!)
    }

    override fun parseValue(value: String): Item {
        return Json.decodeFromString(Uri.decode(value))
    }
}
```

**Prefer:** Passing IDs and loading data in ViewModel over passing complex objects.

## 5. Back navigation

### Pop back stack
```kotlin
// In NavHost callback
onBack = { navController.navigateUp() }

// In feature navigation extension
fun NavGraphBuilder.detailScreen(onBack: () -> Unit) {
    composable(route = DETAIL_ROUTE) {
        DetailRoute(onBack = onBack)  // Pass callback
    }
}

// In Route composable
@Composable
fun DetailRoute(
    onBack: () -> Unit,
    viewModel: DetailViewModel = hiltViewModel()
) {
    DetailScreen(
        uiState = uiState,
        onBackClick = onBack,  // Wire to UI
    )
}
```

### Pop with result
Use `SavedStateHandle` to pass results back:

```kotlin
// In source screen ViewModel
fun navigateToEdit() {
    navController.navigate("edit/$itemId")
}

// In destination screen ViewModel
@HiltViewModel
class EditViewModel @Inject constructor(
    private val savedStateHandle: SavedStateHandle,
) : ViewModel() {
    fun save(item: Item) {
        savedStateHandle["result"] = item
        // Signal to navigate back
    }
}

// In source screen, observe result
val result = navController.currentBackStackEntry
    ?.savedStateHandle
    ?.getStateFlow<Item?>("result", null)
    ?.collectAsStateWithLifecycle()
```

## 6. Deep links

Define deep links for external navigation:

```kotlin
fun NavGraphBuilder.detailScreen(onBack: () -> Unit) {
    composable(
        route = DETAIL_ROUTE,
        arguments = listOf(navArgument("itemId") { type = NavType.StringType }),
        deepLinks = listOf(
            navDeepLink {
                uriPattern = "{{PACKAGE_NAME}}://detail/{itemId}"
            },
            navDeepLink {
                uriPattern = "https://{{APP_NAME}}.example.com/detail/{itemId}"
            }
        )
    ) { backStackEntry ->
        val itemId = backStackEntry.arguments?.getString("itemId") ?: return@composable
        DetailRoute(itemId = itemId, onBack = onBack)
    }
}
```

Register deep link in `AndroidManifest.xml`:

```xml
<activity android:name=".MainActivity">
    <intent-filter>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data
            android:scheme="https"
            android:host="{{APP_NAME}}.example.com"
            android:pathPrefix="/detail" />
    </intent-filter>
</activity>
```

## 7. Nested navigation

For complex flows (e.g., multi-step onboarding), use nested graphs:

```kotlin
fun NavGraphBuilder.onboardingGraph(
    onComplete: () -> Unit,
) {
    navigation(
        route = "onboarding",
        startDestination = "onboarding/welcome"
    ) {
        composable("onboarding/welcome") {
            WelcomeRoute(onNext = { navController.navigate("onboarding/permissions") })
        }
        composable("onboarding/permissions") {
            PermissionsRoute(
                onNext = { navController.navigate("onboarding/profile") },
                onBack = { navController.navigateUp() }
            )
        }
        composable("onboarding/profile") {
            ProfileSetupRoute(
                onComplete = onComplete,
                onBack = { navController.navigateUp() }
            )
        }
    }
}

// In main NavHost
{{APP_CLASS}}NavHost(...) {
    onboardingGraph(
        onComplete = { navController.navigate(HOME_ROUTE) {
            popUpTo("onboarding") { inclusive = true }
        }}
    )
    homeScreen(...)
}
```

## 8. Bottom navigation

For apps with bottom navigation:

```kotlin
@Composable
fun {{APP_CLASS}}NavHost(
    navController: NavHostController,
    modifier: Modifier = Modifier,
) {
    Scaffold(
        bottomBar = {
            BottomNavigationBar(
                destinations = listOf(HOME_ROUTE, SEARCH_ROUTE, PROFILE_ROUTE),
                onNavigate = { route -> navController.navigate(route) },
                currentRoute = navController.currentBackStackEntryAsState().value?.destination?.route
            )
        }
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = HOME_ROUTE,
            modifier = modifier.padding(padding),
        ) {
            homeScreen()
            searchScreen()
            profileScreen()
        }
    }
}
```

**Critical:** Use `singleTop` and `popUpTo` to avoid stack buildup:

```kotlin
navController.navigate(route) {
    launchSingleTop = true
    restoreState = true
    popUpTo(navController.graph.findStartDestination().id) {
        saveState = true
    }
}
```

## 9. Testing navigation

### Test navigation extensions
```kotlin
class HomeNavigationTest {
    @Test
    fun `homeScreen adds composable to graph`() {
        val navController = TestNavHostController(ApplicationProvider.getApplicationContext())
        navController.navigatorProvider.addNavigator(ComposeNavigator())
        
        composeTestRule.setContent {
            NavHost(navController = navController, startDestination = HOME_ROUTE) {
                homeScreen(onNavigateToDetail = {})
            }
        }

        val route = navController.currentBackStackEntry?.destination?.route
        assertThat(route).isEqualTo(HOME_ROUTE)
    }
}
```

### Test ViewModel navigation effects
Use a test callback and verify it was invoked:

```kotlin
@Test
fun `when item clicked then navigation callback is invoked`() {
    var navigatedToId: String? = null
    val onNavigate: (String) -> Unit = { navigatedToId = it }

    composeTestRule.setContent {
        HomeScreen(
            uiState = HomeUiState.Success(listOf(testItem)),
            onItemClick = onNavigate,
        )
    }

    composeTestRule.onNodeWithText("Test Item").performClick()
    assertThat(navigatedToId).isEqualTo("test-id")
}
```

## 10. Common patterns

### Replace destination (no back)
```kotlin
navController.navigate(HOME_ROUTE) {
    popUpTo(navController.graph.findStartDestination().id) {
        inclusive = true
    }
}
```

### Clear back stack after login
```kotlin
navController.navigate(HOME_ROUTE) {
    popUpTo("login") { inclusive = true }
}
```

### Conditional navigation
```kotlin
LaunchedEffect(authState) {
    if (authState == AuthState.LoggedOut) {
        navController.navigate("login") {
            popUpTo(navController.graph.findStartDestination().id) { inclusive = true }
        }
    }
}
```

### Prevent duplicate navigation
```kotlin
fun NavController.navigateSingleTop(route: String) {
    if (currentDestination?.route != route) {
        navigate(route) { launchSingleTop = true }
    }
}
```

## 11. Accessibility

Navigation should respect TalkBack and keyboard navigation:

```kotlin
// Announce navigation to screen readers
LaunchedEffect(Unit) {
    // Announce screen title
}

// Back button
IconButton(
    onClick = onBack,
    contentDescription = stringResource(R.string.back_button_description)
) {
    Icon(Icons.Default.ArrowBack, contentDescription = null)
}
```

## Rules summary

- [ ] Route constants are top-level `const val` in feature's navigation file
- [ ] Features receive callbacks, never `NavController` directly
- [ ] Use `NavGraphBuilder` extensions to define destinations
- [ ] Arguments are declared explicitly with `navArgument`
- [ ] Prefer passing IDs over complex objects
- [ ] Use `navigateUp()` for back navigation
- [ ] Deep links are defined in `deepLinks` parameter
- [ ] Bottom nav uses `singleTop` and `popUpTo` to manage stack
- [ ] Test navigation with `TestNavHostController`
- [ ] Navigation actions are callbacks, not ViewModel dependencies
