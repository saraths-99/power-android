package {{PKG_NAV}}

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
{{NAVHOST_IMPORTS}}
/**
 * The single navigation graph. Each feature contributes its destinations through
 * an extension on NavGraphBuilder, so adding a feature does not mean editing a
 * growing when-block here.
 */
@Composable
fun {{APP_CLASS}}NavHost(
    navController: NavHostController,
    modifier: Modifier = Modifier,
) {
    NavHost(
        navController = navController,
        startDestination = {{FEATURE_UPPER}}_ROUTE,
        modifier = modifier,
    ) {
        {{FEATURE}}Screen(
            onItemClick = {
                // TODO: navigate to a detail destination once you add one.
            },
        )
    }
}
