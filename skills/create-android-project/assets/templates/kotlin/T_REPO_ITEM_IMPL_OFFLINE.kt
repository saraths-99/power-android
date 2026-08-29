package {{PKG_REPO_IMPL}}

{{OFFLINE_IMPORTS}}
/**
 * Offline-first: the Room database is the source of truth and [sync] refreshes it
 * from the network. Reads never hit the network, so the UI works offline.
 */
internal class ItemRepositoryImpl @Inject constructor(
    private val itemDao: ItemDao,
{{REMOTE_PARAM}}    @Dispatcher(AppDispatchers.IO) private val ioDispatcher: CoroutineDispatcher,
) : ItemRepository {

    override fun observeItems(): Flow<List<Item>> =
        itemDao.observeAll().map { entities -> entities.map { it.toDomain() } }

    override fun observeItem(id: String): Flow<Item?> =
        itemDao.observeById(id).map { entity -> entity?.toDomain() }

    override suspend fun upsertItem(item: Item) {
        withContext(ioDispatcher) { itemDao.upsert(item.toEntity()) }
    }

    override suspend fun deleteItem(id: String) {
        withContext(ioDispatcher) { itemDao.deleteById(id) }
    }

    override suspend fun sync(): Boolean = withContext(ioDispatcher) {
{{SYNC_BODY}}
    }
}
