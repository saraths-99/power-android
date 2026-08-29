package {{PKG_REPO_IMPL}}

import {{PKG_MODEL}}.Item
{{REPO_IFACE_IMPORT}}import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.update
import javax.inject.Inject
import javax.inject.Singleton

private val SeedItems = listOf(
    Item("1", "Welcome to {{APP_NAME_KT}}", "Swap this for a persistent repository."),
    Item("2", "Unidirectional data flow", "Events flow down, state flows up."),
    Item("3", "Reactive streams", "The UI observes Flow instead of polling."),
)

/**
 * In-memory source of truth: state is lost when the process dies. Replace with a
 * database-backed implementation when you add persistence. The [ItemRepository]
 * contract does not change, so nothing above this layer has to.
 */
@Singleton
internal class ItemRepositoryImpl @Inject constructor() : ItemRepository {

    private val items = MutableStateFlow(SeedItems)

    override fun observeItems(): Flow<List<Item>> = items.asStateFlow()

    override fun observeItem(id: String): Flow<Item?> =
        items.map { list -> list.firstOrNull { it.id == id } }

    override suspend fun upsertItem(item: Item) {
        items.update { list -> list.filterNot { it.id == item.id } + item }
    }

    override suspend fun deleteItem(id: String) {
        items.update { list -> list.filterNot { it.id == id } }
    }

    override suspend fun sync(): Boolean = true
}
