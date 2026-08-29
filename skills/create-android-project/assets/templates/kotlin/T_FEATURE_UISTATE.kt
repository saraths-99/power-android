package {{PKG_FEATURE}}

import {{PKG_MODEL}}.Item

/** Every state the screen can be in. Exhaustive, so the UI cannot miss a case. */
sealed interface {{FEATURE_CLASS}}UiState {
    data object Loading : {{FEATURE_CLASS}}UiState
    data object Empty : {{FEATURE_CLASS}}UiState
    data class Success(val items: List<Item>) : {{FEATURE_CLASS}}UiState
    data class Error(val message: String) : {{FEATURE_CLASS}}UiState
}

/** User intents. The screen sends these up; it never mutates state itself. */
sealed interface {{FEATURE_CLASS}}Action {
    data object Refresh : {{FEATURE_CLASS}}Action
}
