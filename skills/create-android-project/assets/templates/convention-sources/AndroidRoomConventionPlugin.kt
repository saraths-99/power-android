import androidx.room.gradle.RoomExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies

class AndroidRoomConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply("androidx.room")
                apply("com.google.devtools.ksp")
            }

            extensions.configure<RoomExtension> {
                // Exported schemas are checked in so migrations can be verified.
                schemaDirectory("$projectDir/schemas")
            }

            dependencies {
                add("implementation", library("room-runtime"))
                add("implementation", library("room-ktx"))
                add("ksp", library("room-compiler"))
            }
        }
    }
}
