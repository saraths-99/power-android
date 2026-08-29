package {{PKG_NET}}

import {{PKG_NET}}.model.ItemDto

/** The remote contract. Swap the implementation without touching callers. */
interface ItemRemoteDataSource {
    suspend fun fetchItems(): List<ItemDto>
}
