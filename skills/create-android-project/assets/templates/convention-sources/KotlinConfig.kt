import org.gradle.api.JavaVersion
import org.gradle.api.Project
import org.gradle.api.tasks.compile.JavaCompile
import org.gradle.kotlin.dsl.withType
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

internal const val JAVA_TARGET = "{{JAVA_VERSION}}"

internal val JAVA_LANGUAGE_VERSION: JavaVersion = JavaVersion.VERSION_{{JAVA_VERSION}}

/** Align the Kotlin and Java compilers on the same JVM target across all modules. */
internal fun Project.configureKotlinJvm() {
    tasks.withType<KotlinCompile>().configureEach {
        kotlinOptions {
            jvmTarget = JAVA_TARGET
            freeCompilerArgs = freeCompilerArgs + listOf(
                "-opt-in=kotlin.RequiresOptIn",
                "-opt-in=kotlinx.coroutines.ExperimentalCoroutinesApi",
            )
        }
    }
    tasks.withType<JavaCompile>().configureEach {
        sourceCompatibility = JAVA_TARGET
        targetCompatibility = JAVA_TARGET
    }
}
