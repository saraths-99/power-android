import org.gradle.api.Project
import org.gradle.kotlin.dsl.dependencies

/**
 * Compose dependencies shared by the application and library Compose conventions.
 * The BOM pins every Compose artifact to one tested combination, so the
 * individual libraries below carry no version.
 */
internal fun Project.addComposeDependencies() {
    dependencies {
        val bom = library("androidx-compose-bom")
        add("implementation", platform(bom))
        add("androidTestImplementation", platform(bom))
        add("implementation", library("androidx-compose-ui"))
        add("implementation", library("androidx-compose-ui-graphics"))
        add("implementation", library("androidx-compose-material3"))
        add("implementation", library("androidx-compose-ui-tooling-preview"))
        add("debugImplementation", library("androidx-compose-ui-tooling"))
        add("androidTestImplementation", library("androidx-compose-ui-test-junit4"))
        add("debugImplementation", library("androidx-compose-ui-test-manifest"))
    }
}
