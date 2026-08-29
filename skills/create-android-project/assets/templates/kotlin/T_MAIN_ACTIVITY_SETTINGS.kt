package {{PKG}}

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.getValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import {{PKG_APP_UI}}.{{APP_ROOT}}
import {{PKG_THEME}}.{{APP_CLASS}}Theme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    private val viewModel: MainActivityViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            val uiState by viewModel.uiState.collectAsStateWithLifecycle()
            {{APP_CLASS}}Theme(
                darkTheme = uiState.shouldUseDarkTheme(isSystemInDarkTheme()),
                dynamicColor = uiState.shouldUseDynamicColor(),
            ) {
                {{APP_ROOT}}()
            }
        }
    }
}
