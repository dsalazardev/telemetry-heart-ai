package com.example.wearos.service

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.health.services.client.PassiveListenerCallback
import androidx.health.services.client.data.DataPointContainer
import androidx.health.services.client.data.DataType
import com.example.wearos.R
import com.example.wearos.data.sensor.HealthDataHolder
import com.example.wearos.data.sensor.HealthDataHolder.getRiskLevel
import com.example.wearos.data.sensor.RiskLevel
import com.example.wearos.presentation.MainActivity
import androidx.wear.tiles.TileService
import com.example.wearos.tile.HrTileService
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.time.Instant

class TelemetryForegroundService : Service() {

    private val app get() = TelemetryApplication.instance
    private var telemetryJob: Job? = null
    private var currentHr: Double = 0.0
    private var registered: Boolean = false

    companion object {
        private const val TAG = "TelemetryWearOS"
        private const val NOTIFICATION_ID = 1
        private const val CHANNEL_ID = "telemetry_health"
        private const val TELEMETRY_INTERVAL_MS = 60_000L
        private const val DEFAULT_PACIENTE_ID = 1
    }

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "ForegroundService: onCreate")
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, buildNotification(0.0))
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.i(TAG, "ForegroundService: onStartCommand")
        registerHealthListener()
        registerDeviceIfNeeded()
        startTelemetryLoop()
        return START_STICKY
    }

    override fun onDestroy() {
        Log.i(TAG, "ForegroundService: onDestroy")
        telemetryJob?.cancel()
        serviceScope.cancel()
        app.healthSensor.unregisterPassiveCallback()
        super.onDestroy()
    }

    override fun onBind(intent: Intent): IBinder? = null

    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            CHANNEL_ID,
            getString(R.string.notification_channel_name),
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = getString(R.string.notification_channel_desc)
        }
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(channel)
    }

    private fun buildNotification(hr: Double): android.app.Notification {
        val openIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            this, 0, openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val riskLabel = when (getRiskLevel(hr)) {
            RiskLevel.ALTO -> getString(R.string.risk_alto)
            RiskLevel.MEDIO -> getString(R.string.risk_medio)
            RiskLevel.BAJO -> getString(R.string.risk_bajo)
        }

        val hrText = if (hr > 0) {
            getString(R.string.notification_hr_text, hr.toInt())
        } else {
            getString(R.string.no_data)
        }

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(hrText)
            .setContentText(getString(R.string.notification_risk_text, riskLabel))
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setForegroundServiceBehavior(NotificationCompat.FOREGROUND_SERVICE_IMMEDIATE)
            .build()
    }

    private fun updateNotification(hr: Double) {
        val manager = getSystemService(NotificationManager::class.java)
        manager.notify(NOTIFICATION_ID, buildNotification(hr))
    }

    private fun registerDeviceIfNeeded() {
        serviceScope.launch {
            val token = app.tokenStorage.getToken()
            if (token == null) {
                Log.i(TAG, "No token found, registering device...")
                val modelo = "${Build.MANUFACTURER} ${Build.MODEL}"
                val result = app.telemetryRepository.registerDevice(
                    modelo = modelo,
                    pacienteId = DEFAULT_PACIENTE_ID
                )
                if (result.isSuccess) {
                    val body = result.getOrNull()!!
                    Log.i(TAG, "Device registered: id=${body.id}")
                    registered = true
                } else {
                    Log.w(TAG, "Device registration failed, will retry on next loop")
                }
            } else {
                Log.i(TAG, "Token already exists, device already registered")
                registered = true
            }
        }
    }

    private fun registerHealthListener() {
        val callback = object : PassiveListenerCallback {
            override fun onNewDataPointsReceived(dataPoints: DataPointContainer) {
                val hrSamples = dataPoints.getData(DataType.HEART_RATE_BPM)
                if (hrSamples.isNotEmpty()) {
                    val hr = hrSamples.last().value
                    currentHr = hr
                    HealthDataHolder.updateHeartRate(hr)
                    Log.d(TAG, "HR received: $hr")
                    updateNotification(hr)
                    requestTileUpdate()
                }
            }

            override fun onPermissionLost() {
                Log.w(TAG, "Health permission lost")
                stopSelf()
            }
        }
        app.healthSensor.registerPassiveCallback(callback)
    }

    private fun requestTileUpdate() {
        try {
            TileService.getUpdater(this).requestUpdate(HrTileService::class.java)
        } catch (e: Exception) {
            Log.w(TAG, "Tile update failed", e)
        }
    }

    private val serviceScope = CoroutineScope(Dispatchers.Default + Job())

    private fun startTelemetryLoop() {
        telemetryJob?.cancel()
        telemetryJob = serviceScope.launch {
            while (isActive) {
                delay(TELEMETRY_INTERVAL_MS)
                val hr = currentHr
                if (hr > 0) {
                    val token = app.tokenStorage.getToken()
                    val deviceId = app.tokenStorage.getDeviceId()
                    if (token != null && deviceId != null) {
                        app.authInterceptor.token = token
                        val sent = app.telemetryRepository.submitTelemetry(
                            frecuenciaCardiaca = hr,
                            spo2 = null,
                            timestamp = Instant.now().toString(),
                            dispositivoId = deviceId
                        )
                        if (sent) {
                            Log.i(TAG, "Telemetry sent: fc=$hr")
                        }
                    }
                }
                app.telemetryRepository.processOfflineQueue()
            }
        }
    }
}
