package {{PKG_REPO_IMPL}}

import {{PKG_MAPPER}}.toDomain
import {{PKG_MODEL}}.DarkThemeConfig
import {{PKG_MODEL}}.UserData
import {{PKG_PREFS}}.UserPreferencesDataSource
{{USER_REPO_IFACE_IMPORT}}import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject

internal class UserDataRepositoryImpl @Inject constructor(
    private val dataSource: UserPreferencesDataSource,
) : UserDataRepository {

    override val userData: Flow<UserData> = dataSource.preferences.map { it.toDomain() }

    override suspend fun setDarkThemeConfig(darkThemeConfig: DarkThemeConfig) {
        dataSource.setDarkThemeConfig(darkThemeConfig.name)
    }

    override suspend fun setDynamicColorPreference(useDynamicColor: Boolean) {
        dataSource.setDynamicColorPreference(useDynamicColor)
    }
}
