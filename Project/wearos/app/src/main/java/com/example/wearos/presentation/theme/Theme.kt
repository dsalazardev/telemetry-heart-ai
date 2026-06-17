package com.example.wearos.presentation.theme

import androidx.compose.runtime.Composable
import androidx.wear.compose.material3.MaterialTheme

object RiskColors {
    val green = androidx.compose.ui.graphics.Color(0xFF4CAF50)
    val yellow = androidx.compose.ui.graphics.Color(0xFFFFC107)
    val red = androidx.compose.ui.graphics.Color(0xFFF44336)
}

@Composable
fun WearosTheme(
    content: @Composable () -> Unit
) {
    MaterialTheme(
        content = content
    )
}
