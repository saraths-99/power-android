package {{PKG_NET}}.model

import kotlinx.serialization.Serializable

/** Wire format. Mapped into an entity in the data layer; never used by the UI. */
@Serializable
data class ItemDto(
    val id: String,
    val title: String,
    val description: String = "",
)
