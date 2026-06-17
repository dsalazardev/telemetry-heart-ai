package com.example.wearos.presentation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.wear.compose.material3.Button
import androidx.wear.compose.material3.ButtonDefaults
import androidx.wear.compose.material3.MaterialTheme
import androidx.wear.compose.material3.Text
import com.example.wearos.R
import com.example.wearos.data.sensor.HealthDataHolder
import com.example.wearos.data.sensor.HealthDataHolder.getRiskLevel
import com.example.wearos.data.sensor.RiskLevel
import com.example.wearos.presentation.theme.RiskColors

@Composable
fun TelemetryScreen(
    connectionState: ConnectionState,
    onCheckHr: () -> Unit
) {
    val healthData by HealthDataHolder.healthData.collectAsState()
    val hr = healthData.heartRate
    val riskLevel = getRiskLevel(hr)
    val riskColor = when (riskLevel) {
        RiskLevel.ALTO -> RiskColors.red
        RiskLevel.MEDIO -> RiskColors.yellow
        RiskLevel.BAJO -> RiskColors.green
    }

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = stringResource(R.string.hr_label),
                style = MaterialTheme.typography.labelMedium
            )
            Spacer(modifier = Modifier.padding(start = 8.dp))
            ConnectionIndicator(state = connectionState)
        }

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = if (hr > 0) {
                stringResource(R.string.hr_value_template, hr.toInt())
            } else {
                stringResource(R.string.no_data)
            },
            fontSize = 48.sp,
            fontWeight = FontWeight.Bold,
            color = riskColor,
            textAlign = TextAlign.Center
        )

        Spacer(modifier = Modifier.height(4.dp))

        Text(
            text = stringResource(R.string.risk_level),
            style = MaterialTheme.typography.labelSmall
        )
        Text(
            text = when (riskLevel) {
                RiskLevel.ALTO -> stringResource(R.string.risk_alto)
                RiskLevel.MEDIO -> stringResource(R.string.risk_medio)
                RiskLevel.BAJO -> stringResource(R.string.risk_bajo)
            },
            color = riskColor,
            fontWeight = FontWeight.Medium
        )

        if (healthData.timestamp.isNotEmpty()) {
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "${stringResource(R.string.last_update)}: ${healthData.timestamp.take(19).replace("T", " ")}",
                style = MaterialTheme.typography.labelSmall,
                textAlign = TextAlign.Center
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        Button(
            onClick = onCheckHr,
            colors = ButtonDefaults.buttonColors(
                containerColor = MaterialTheme.colorScheme.primaryContainer
            )
        ) {
            Text(stringResource(R.string.check_hr_now))
        }
    }
}
