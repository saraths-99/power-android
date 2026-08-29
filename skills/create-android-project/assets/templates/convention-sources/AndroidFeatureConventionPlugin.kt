import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.dependencies
import org.gradle.kotlin.dsl.project

/**
 * Feature modules are presentation-layer only: they see `domain` (use cases and
 * models) and the shared UI modules, never `data`.
 */
class AndroidFeatureConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply("{{PREFIX}}.android.library")
                apply("{{PREFIX}}.android.library.compose")
                apply("{{PREFIX}}.hilt")
            }

            dependencies {
                add("implementation", project(":domain"))
                add("implementation", project(":core:ui"))
                add("implementation", project(":core:designsystem"))
                add("implementation", library("androidx-hilt-navigation-compose"))
                add("implementation", library("androidx-navigation-compose"))
                add("implementation", library("androidx-lifecycle-runtime-compose"))
                add("implementation", library("androidx-lifecycle-viewmodel-compose"))
                add("testImplementation", library("turbine"))
            }
        }
    }
}
