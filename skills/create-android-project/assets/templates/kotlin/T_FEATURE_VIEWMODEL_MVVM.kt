package {{PKG_FEATURE}}

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import {{PKG_MODEL}}.Item
import {{PKG_REPO}}.ItemRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class {{FEATURE_CLASS}}ViewModel @Inject constructor(
    private val itemRepository: ItemRepository,
) : ViewModel() {

    val uiState: StateFlow<{{FEATURE_CLASS}}UiState> = itemRepository.observeItems()
        .map<List<Item>, {{FEATURE_CLASS}}UiState> { items ->
            if (items.isEmpty()) {
                {{FEATURE_CLASS}}UiState.Empty
            } else {
                {{FEATURE_CLASS}}UiState.Success(items)
            }
        }
        .catch { throwable ->
            emit({{FEATURE_CLASS}}UiState.Error(throwable.message ?: "Something went wrong"))
        }
        .stateIn(
            scope = viewModelScope,
            // Survive short-lived subscriber gaps such as a rotation.
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = {{FEATURE_CLASS}}UiState.Loading,
        )

    fun onAction(action: {{FEATURE_CLASS}}Action) {
        when (action) {
            {{FEATURE_CLASS}}Action.Refresh -> refresh()
        }
    }

    private fun refresh() {
        viewModelScope.launch { itemRepository.sync() }
    }
}
