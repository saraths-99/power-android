package {{PKG}}

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import {{PKG_APP_UI}}.{{APP_ROOT}}
import {{PKG_THEME}}.{{APP_CLASS}}Theme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            {{APP_CLASS}}Theme {
                {{APP_ROOT}}()
            }
        }
    }
}
