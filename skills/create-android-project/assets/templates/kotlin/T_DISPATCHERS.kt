package {{PKG_DISPATCHERS}}

import javax.inject.Qualifier

/**
 * Qualifier for injecting a specific dispatcher. Injecting dispatchers rather
 * than referencing `Dispatchers.IO` directly is what makes suspend functions
 * testable with a test dispatcher.
 */
@Qualifier
@Retention(AnnotationRetention.RUNTIME)
annotation class Dispatcher(val dispatcher: AppDispatchers)

enum class AppDispatchers {
    Default,
    IO,
}
