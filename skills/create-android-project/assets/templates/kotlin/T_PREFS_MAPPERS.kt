package {{PKG_MAPPER}}

import {{PKG_MODEL}}.DarkThemeConfig
import {{PKG_MODEL}}.UserData
import {{PKG_PREFS}}.StoredPreferences

/** Turns stored primitives into domain types, tolerating unknown stored values. */
internal fun StoredPreferences.toDomain(): UserData = UserData(
    darkThemeConfig = darkThemeConfig
        ?.let { stored -> runCatching { DarkThemeConfig.valueOf(stored) }.getOrNull() }
        ?: DarkThemeConfig.FOLLOW_SYSTEM,
    useDynamicColor = useDynamicColor,
)
