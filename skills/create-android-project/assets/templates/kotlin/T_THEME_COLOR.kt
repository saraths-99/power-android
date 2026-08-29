package {{PKG_THEME}}

import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.ui.graphics.Color

// Replace with your brand palette. Material Theme Builder generates a full set
// of tokens: https://material-foundation.github.io/material-theme-builder/
internal val Primary = Color(0xFF3B5BA9)
internal val PrimaryDark = Color(0xFFB2C5FF)
internal val Secondary = Color(0xFF565E71)
internal val SecondaryDark = Color(0xFFBEC6DC)
internal val ErrorLight = Color(0xFFBA1A1A)
internal val ErrorDark = Color(0xFFFFB4AB)

internal val LightColorScheme = lightColorScheme(
    primary = Primary,
    secondary = Secondary,
    error = ErrorLight,
)

internal val DarkColorScheme = darkColorScheme(
    primary = PrimaryDark,
    secondary = SecondaryDark,
    error = ErrorDark,
)
