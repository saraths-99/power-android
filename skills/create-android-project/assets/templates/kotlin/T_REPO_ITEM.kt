package {{PKG_REPO}}

import {{PKG_MODEL}}.Item
import kotlinx.coroutines.flow.Flow

/**
 * Reads and writes items. Exposes streams rather than snapshots so the UI reacts
 * to changes instead of polling.
 */
interface ItemRepository {

    fun observeItems(): Flow<List<Item>>

    fun observeItem(id: String): Flow<Item?>

    suspend fun upsertItem(item: Item)

    suspend fun deleteItem(id: String)

    /** Pulls remote data into the local store. Returns false if the pull failed. */
    suspend fun sync(): Boolean
}
