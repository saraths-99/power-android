package {{PKG_APP_UI}}

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.compose.rememberNavController
import {{PKG_NAV}}.{{APP_CLASS}}NavHost

/** App-level shell. Individual screens own their own top bars. */
@Composable
fun {{APP_ROOT}}(
    navController: NavHostController = rememberNavController(),
) {
    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background,
    ) {
        {{APP_CLASS}}NavHost(navController = navController)
    }
}
