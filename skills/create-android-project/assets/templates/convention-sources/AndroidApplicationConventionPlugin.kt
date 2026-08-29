import com.android.build.api.dsl.ApplicationExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.configure

class AndroidApplicationConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply("com.android.application")
                apply("org.jetbrains.kotlin.android")
            }

            extensions.configure<ApplicationExtension> {
                compileSdk = {{COMPILE_SDK}}
                defaultConfig {
                    minSdk = {{MIN_SDK}}
                    targetSdk = {{TARGET_SDK}}
                }
                compileOptions {
                    sourceCompatibility = JAVA_LANGUAGE_VERSION
                    targetCompatibility = JAVA_LANGUAGE_VERSION
                }
            }

            configureKotlinJvm()
        }
    }
}
