package {{PKG_DB}}.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Room representation of an item. Deliberately separate from the domain model so
 * schema changes never ripple into the rest of the app.
 */
@Entity(tableName = "items")
data class ItemEntity(
    @PrimaryKey
    val id: String,
    val title: String,
    val description: String,
)
