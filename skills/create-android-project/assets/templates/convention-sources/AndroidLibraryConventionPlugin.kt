import com.android.build.api.dsl.LibraryExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies

class AndroidLibraryConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply("com.android.library")
                apply("org.jetbrains.kotlin.android")
            }

            extensions.configure<LibraryExtension> {
                compileSdk = {{COMPILE_SDK}}
                defaultConfig {
                    minSdk = {{MIN_SDK}}
                    testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
                }
                compileOptions {
                    sourceCompatibility = JAVA_LANGUAGE_VERSION
                    targetCompatibility = JAVA_LANGUAGE_VERSION
                }
                // targetSdk is an application-level concern; AGP warns if a
                // library module declares it.
            }

            configureKotlinJvm()

            dependencies {
                add("testImplementation", library("junit"))
                add("testImplementation", library("kotlinx-coroutines-test"))
            }
        }
    }
}
