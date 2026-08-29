import org.gradle.api.Project
import org.gradle.api.artifacts.VersionCatalog
import org.gradle.api.artifacts.VersionCatalogsExtension
import org.gradle.kotlin.dsl.getByType

/** Access the `libs` version catalog from a convention plugin. */
internal val Project.libs: VersionCatalog
    get() = extensions.getByType<VersionCatalogsExtension>().named("libs")

internal fun Project.library(alias: String) = libs.findLibrary(alias).orElseThrow {
    IllegalStateException("Version catalog is missing library alias '" + alias + "'")
}

internal fun Project.version(alias: String): String = libs.findVersion(alias).orElseThrow {
    IllegalStateException("Version catalog is missing version alias '" + alias + "'")
}.requiredVersion
