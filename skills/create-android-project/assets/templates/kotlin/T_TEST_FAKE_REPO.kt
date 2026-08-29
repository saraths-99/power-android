package {{PKG_TESTING}}.repository

import {{PKG_MODEL}}.Item
import {{PKG_REPO}}.ItemRepository
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.map

/**
 * Hand-written test double. Preferred over a mocking library: it is faster and it
 * fails to compile when [ItemRepository] changes, instead of failing at runtime.
 */
class FakeItemRepository : ItemRepository {

    private val itemsFlow = MutableSharedFlow<List<Item>>(
        replay = 1,
        onBufferOverflow = BufferOverflow.DROP_OLDEST,
    )

    var syncResult: Boolean = true

    override fun observeItems(): Flow<List<Item>> = itemsFlow

    override fun observeItem(id: String): Flow<Item?> =
        itemsFlow.map { items -> items.firstOrNull { it.id == id } }

    override suspend fun upsertItem(item: Item) {
        val current = itemsFlow.replayCache.firstOrNull().orEmpty()
        itemsFlow.emit(current.filterNot { it.id == item.id } + item)
    }

    override suspend fun deleteItem(id: String) {
        val current = itemsFlow.replayCache.firstOrNull().orEmpty()
        itemsFlow.emit(current.filterNot { it.id == id })
    }

    override suspend fun sync(): Boolean = syncResult

    /** Test hook: push a new list to every collector. */
    suspend fun emitItems(items: List<Item>) {
        itemsFlow.emit(items)
    }
}
