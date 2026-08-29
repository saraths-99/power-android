package {{PKG}}

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

/** Hilt entry point: triggers generation of the application-scoped graph. */
@HiltAndroidApp
class {{APP_CLASS}}Application : Application()
