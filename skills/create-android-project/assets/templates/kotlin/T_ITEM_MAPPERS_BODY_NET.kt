
internal fun ItemDto.toEntity(): ItemEntity = ItemEntity(
    id = id,
    title = title,
    description = description,
)
