package {{PKG_FEATURE}}

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
{{R_IMPORT}}import {{PKG_COMPONENTS}}.EmptyState
import {{PKG_COMPONENTS}}.ErrorMessage
import {{PKG_COMPONENTS}}.ItemCard
import {{PKG_COMPONENTS}}.LoadingIndicator
import {{PKG_MODEL}}.Item
import {{PKG_THEME}}.{{APP_CLASS}}Theme

/**
 * Stateful entry point: owns the ViewModel and nothing else. Keeping it separate
 * from [{{FEATURE_CLASS}}Screen] is what lets the screen be previewed and tested
 * without Hilt.
 */
@Composable
internal fun {{FEATURE_CLASS}}Route(
    onItemClick: (String) -> Unit,
    modifier: Modifier = Modifier,
    viewModel: {{FEATURE_CLASS}}ViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    {{FEATURE_CLASS}}Screen(
        uiState = uiState,
        onAction = viewModel::onAction,
        onItemClick = onItemClick,
        modifier = modifier,
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun {{FEATURE_CLASS}}Screen(
    uiState: {{FEATURE_CLASS}}UiState,
    onAction: ({{FEATURE_CLASS}}Action) -> Unit,
    onItemClick: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    Scaffold(
        modifier = modifier.fillMaxSize(),
        topBar = {
            TopAppBar(
                title = { Text(text = stringResource(R.string.feature_{{FEATURE}}_title)) },
                actions = {
                    IconButton(onClick = { onAction({{FEATURE_CLASS}}Action.Refresh) }) {
                        Icon(
                            imageVector = Icons.Filled.Refresh,
                            contentDescription = stringResource(R.string.feature_{{FEATURE}}_refresh),
                        )
                    }
                },
            )
        },
    ) { innerPadding ->
        when (uiState) {
            {{FEATURE_CLASS}}UiState.Loading -> LoadingIndicator(
                modifier = Modifier.padding(innerPadding),
            )

            {{FEATURE_CLASS}}UiState.Empty -> EmptyState(
                message = stringResource(R.string.feature_{{FEATURE}}_empty),
                modifier = Modifier.padding(innerPadding),
            )

            is {{FEATURE_CLASS}}UiState.Error -> ErrorMessage(
                message = uiState.message,
                onRetry = { onAction({{FEATURE_CLASS}}Action.Refresh) },
                retryLabel = stringResource(R.string.feature_{{FEATURE}}_retry),
                modifier = Modifier.padding(innerPadding),
            )

            is {{FEATURE_CLASS}}UiState.Success -> LazyColumn(
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding),
            ) {
                items(items = uiState.items, key = { it.id }) { item ->
                    ItemCard(item = item, onClick = onItemClick)
                }
            }
        }
    }
}

@Preview
@Composable
private fun {{FEATURE_CLASS}}ScreenPreview() {
    {{APP_CLASS}}Theme {
        {{FEATURE_CLASS}}Screen(
            uiState = {{FEATURE_CLASS}}UiState.Success(
                items = listOf(
                    Item("1", "First item", "A short description"),
                    Item("2", "Second item", "Another description"),
                ),
            ),
            onAction = {},
            onItemClick = {},
        )
    }
}
