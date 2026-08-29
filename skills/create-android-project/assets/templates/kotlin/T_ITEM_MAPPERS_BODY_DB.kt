
/**
 * Mapping lives in the data layer, so the database and network modules never
 * need to know about domain types, or about each other.
 */
internal fun ItemEntity.toDomain(): Item = Item(
    id = id,
    title = title,
    description = description,
)

internal fun Item.toEntity(): ItemEntity = ItemEntity(
    id = id,
    title = title,
    description = description,
)
