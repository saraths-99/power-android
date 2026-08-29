package {{PKG}}

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import {{PKG_MODEL}}.DarkThemeConfig
import {{PKG_MODEL}}.UserData
{{ACTIVITY_VM_IMPORT}}import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import javax.inject.Inject

sealed interface MainActivityUiState {
    data object Loading : MainActivityUiState
    data class Success(val userData: UserData) : MainActivityUiState
}

/** Supplies theme settings before the first frame so there is no colour flash. */
@HiltViewModel
class MainActivityViewModel @Inject constructor(
    {{ACTIVITY_VM_PARAM}}
) : ViewModel() {

    val uiState: StateFlow<MainActivityUiState> = {{ACTIVITY_VM_SOURCE}}
        .map<UserData, MainActivityUiState> { MainActivityUiState.Success(it) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = MainActivityUiState.Loading,
        )
}

internal fun MainActivityUiState.shouldUseDarkTheme(systemDark: Boolean): Boolean = when (this) {
    MainActivityUiState.Loading -> systemDark
    is MainActivityUiState.Success -> when (userData.darkThemeConfig) {
        DarkThemeConfig.FOLLOW_SYSTEM -> systemDark
        DarkThemeConfig.LIGHT -> false
        DarkThemeConfig.DARK -> true
    }
}

internal fun MainActivityUiState.shouldUseDynamicColor(): Boolean = when (this) {
    MainActivityUiState.Loading -> true
    is MainActivityUiState.Success -> userData.useDynamicColor
}
