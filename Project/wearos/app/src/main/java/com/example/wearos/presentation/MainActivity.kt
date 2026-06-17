package com.example.wearos.presentation

import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.wear.compose.material3.Button
import androidx.wear.compose.material3.MaterialTheme
import androidx.wear.compose.material3.Text
import com.example.wearos.R
import com.example.wearos.presentation.theme.WearosTheme
import com.example.wearos.service.TelemetryForegroundService

class MainActivity : ComponentActivity() {

    private var hasPermission by mutableStateOf(false)
    private var connectionState by mutableStateOf(ConnectionState.DISCONNECTED)

    companion object {
        private const val TAG = "TelemetryWearOS"
    }

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        hasPermission = granted
        if (granted) {
            Log.i(TAG, "Health permission granted")
            connectionState = ConnectionState.CONNECTING
            startTelemetryService()
        } else {
            Log.w(TAG, "Health permission denied")
            connectionState = ConnectionState.DISCONNECTED
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        checkAndRequestPermission()
        setContent {
            WearosTheme {
                if (hasPermission) {
                    TelemetryScreen(
                        connectionState = connectionState,
                        onCheckHr = {
                            Log.d(TAG, "Check HR manually")
                        }
                    )
                } else {
                    PermissionRequestScreen(
                        onRequestPermission = { checkAndRequestPermission() }
                    )
                }
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        stopService(Intent(this, TelemetryForegroundService::class.java))
    }

    private fun checkAndRequestPermission() {
        val permission = if (Build.VERSION.SDK_INT >= 36) {
            "android.permission.health.READ_HEART_RATE"
        } else {
            "android.permission.BODY_SENSORS"
        }

        if (ContextCompat.checkSelfPermission(this, permission) == PackageManager.PERMISSION_GRANTED) {
            hasPermission = true
            connectionState = ConnectionState.CONNECTING
            startTelemetryService()
        } else {
            permissionLauncher.launch(permission)
        }
    }

    private fun startTelemetryService() {
        val intent = Intent(this, TelemetryForegroundService::class.java)
        if (Build.VERSION.SDK_INT >= 26) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }
        connectionState = ConnectionState.CONNECTED
    }
}

@Composable
fun PermissionRequestScreen(onRequestPermission: () -> Unit) {
    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = stringResource(R.string.permission_required),
            style = MaterialTheme.typography.titleMedium
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = stringResource(R.string.permission_rationale),
            style = MaterialTheme.typography.bodySmall
        )
        Spacer(modifier = Modifier.height(16.dp))
        Button(onClick = onRequestPermission) {
            Text(stringResource(R.string.grant_permission))
        }
    }
}
