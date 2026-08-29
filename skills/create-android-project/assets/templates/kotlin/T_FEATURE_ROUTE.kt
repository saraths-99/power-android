package {{PKG_FEATURE_API}}

import androidx.navigation.NavController
import androidx.navigation.NavOptions

const val {{FEATURE_UPPER}}_ROUTE = "{{FEATURE}}"

fun NavController.navigateTo{{FEATURE_CLASS}}(navOptions: NavOptions? = null) {
    navigate({{FEATURE_UPPER}}_ROUTE, navOptions)
}
