package {{PKG_DB_DI}}

import android.content.Context
import androidx.room.Room
import {{PKG_DB}}.{{APP_CLASS}}Database
import {{PKG_DB}}.dao.ItemDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
internal object DatabaseModule {

    @Provides
    @Singleton
    fun provides{{APP_CLASS}}Database(
        @ApplicationContext context: Context,
    ): {{APP_CLASS}}Database = Room.databaseBuilder(
        context,
        {{APP_CLASS}}Database::class.java,
        "{{DB_NAME}}",
    )
        .addCallback({{APP_CLASS}}Database.SeedCallback)
        .build()

    @Provides
    fun providesItemDao(database: {{APP_CLASS}}Database): ItemDao = database.itemDao()
}
