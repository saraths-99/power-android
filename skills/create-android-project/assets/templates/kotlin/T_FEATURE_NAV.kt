package {{PKG_FEATURE_NAV}}

import androidx.navigation.NavGraphBuilder
import androidx.navigation.compose.composable
{{ROUTE_IMPORT}}import {{PKG_FEATURE}}.{{FEATURE_CLASS}}Route

/** Registers this feature's destination. The app module owns the NavHost. */
fun NavGraphBuilder.{{FEATURE}}Screen(
    onItemClick: (String) -> Unit,
) {
    composable(route = {{FEATURE_UPPER}}_ROUTE) {
        {{FEATURE_CLASS}}Route(onItemClick = onItemClick)
    }
}
