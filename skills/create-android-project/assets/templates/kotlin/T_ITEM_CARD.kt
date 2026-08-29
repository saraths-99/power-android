package {{PKG_COMPONENTS}}

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import {{PKG_MODEL}}.Item
import {{PKG_THEME}}.{{APP_CLASS}}Theme

/** Stateless presentation of an [Item]. All data and callbacks are passed in. */
@Composable
fun ItemCard(
    item: Item,
    onClick: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .clickable { onClick(item.id) },
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(text = item.title, style = MaterialTheme.typography.titleMedium)
            Text(
                text = item.description,
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.padding(top = 4.dp),
            )
        }
    }
}

@Preview
@Composable
private fun ItemCardPreview() {
    {{APP_CLASS}}Theme {
        ItemCard(
            item = Item(id = "1", title = "Item title", description = "Item description"),
            onClick = {},
        )
    }
}
