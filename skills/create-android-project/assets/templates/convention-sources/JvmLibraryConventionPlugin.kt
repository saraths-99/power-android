import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.plugins.JavaPluginExtension
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies

/** For pure-Kotlin modules such as `domain`, which must not see the Android SDK. */
class JvmLibraryConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            pluginManager.apply("org.jetbrains.kotlin.jvm")

            extensions.configure<JavaPluginExtension> {
                sourceCompatibility = JAVA_LANGUAGE_VERSION
                targetCompatibility = JAVA_LANGUAGE_VERSION
            }

            configureKotlinJvm()

            dependencies {
                add("testImplementation", library("junit"))
                add("testImplementation", library("kotlinx-coroutines-test"))
            }
        }
    }
}
