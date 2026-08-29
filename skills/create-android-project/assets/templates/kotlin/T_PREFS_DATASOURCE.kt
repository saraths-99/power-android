package {{PKG_PREFS}}

import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

private val DARK_THEME_CONFIG = stringPreferencesKey("dark_theme_config")
private val USE_DYNAMIC_COLOR = booleanPreferencesKey("use_dynamic_color")

/**
 * What is physically stored. Primitives only: converting to domain types is the
 * data layer's job, which keeps this class free of domain knowledge.
 */
data class StoredPreferences(
    val darkThemeConfig: String?,
    val useDynamicColor: Boolean,
)

/** The only class that knows the Preferences keys. */
@Singleton
class UserPreferencesDataSource @Inject constructor(
    private val dataStore: DataStore<Preferences>,
) {

    val preferences: Flow<StoredPreferences> = dataStore.data.map { stored ->
        StoredPreferences(
            darkThemeConfig = stored[DARK_THEME_CONFIG],
            useDynamicColor = stored[USE_DYNAMIC_COLOR] ?: true,
        )
    }

    suspend fun setDarkThemeConfig(value: String) {
        dataStore.edit { it[DARK_THEME_CONFIG] = value }
    }

    suspend fun setDynamicColorPreference(value: Boolean) {
        dataStore.edit { it[USE_DYNAMIC_COLOR] = value }
    }
}
