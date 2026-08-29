package {{PKG_REPO}}

import {{PKG_MODEL}}.DarkThemeConfig
import {{PKG_MODEL}}.UserData
import kotlinx.coroutines.flow.Flow

interface UserDataRepository {

    val userData: Flow<UserData>

    suspend fun setDarkThemeConfig(darkThemeConfig: DarkThemeConfig)

    suspend fun setDynamicColorPreference(useDynamicColor: Boolean)
}
