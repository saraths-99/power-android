package {{PKG_MODEL}}

/**
 * A domain model: plain Kotlin, no framework annotations. Database entities and
 * network DTOs are mapped to this type so the rest of the app never sees them.
 *
 * Rename this to something from your own domain.
 */
data class Item(
    val id: String,
    val title: String,
    val description: String,
)
