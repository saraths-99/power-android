package {{PKG_DB}}

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.sqlite.db.SupportSQLiteDatabase
import {{PKG_DB}}.dao.ItemDao
import {{PKG_DB}}.model.ItemEntity

@Database(
    entities = [ItemEntity::class],
    version = 1,
    exportSchema = true,
)
abstract class {{APP_CLASS}}Database : RoomDatabase() {

    abstract fun itemDao(): ItemDao

    companion object {
        /**
         * Seeds a few rows on first creation so the app renders something before
         * any sync happens. Delete once you have real data.
         */
        val SeedCallback: Callback = object : Callback() {
            override fun onCreate(db: SupportSQLiteDatabase) {
                super.onCreate(db)
                db.execSQL(
                    "INSERT INTO items (id, title, description) VALUES " +
                        "('1', 'Welcome', 'This row was seeded by the Room callback.')," +
                        "('2', 'Offline-first', 'The local database is the source of truth.')," +
                        "('3', 'Unidirectional data flow', 'Events flow down, state flows up.')",
                )
            }
        }
    }
}
