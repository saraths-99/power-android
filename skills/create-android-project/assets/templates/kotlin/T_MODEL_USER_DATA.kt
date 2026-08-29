package {{PKG_MODEL}}

/** User-controlled settings as a single immutable snapshot. */
data class UserData(
    val darkThemeConfig: DarkThemeConfig = DarkThemeConfig.FOLLOW_SYSTEM,
    val useDynamicColor: Boolean = true,
)
