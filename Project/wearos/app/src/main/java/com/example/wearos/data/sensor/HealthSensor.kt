package com.example.wearos.data.sensor

import android.content.Context
import android.util.Log
import androidx.health.services.client.HealthServices
import androidx.health.services.client.MeasureCallback
import androidx.health.services.client.PassiveListenerCallback
import androidx.health.services.client.data.DataType
import androidx.health.services.client.data.PassiveListenerConfig
import kotlinx.coroutines.guava.await

class HealthSensor(private val context: Context) {

    private val healthClient = HealthServices.getClient(context)
    val passiveMonitoringClient = healthClient.passiveMonitoringClient
    val measureClient = healthClient.measureClient

    companion object {
        private const val TAG = "TelemetryWearOS"
    }

    suspend fun hasHeartRateCapability(): Boolean {
        return try {
            val capabilities = passiveMonitoringClient.getCapabilitiesAsync().await()
            DataType.HEART_RATE_BPM in capabilities.supportedDataTypesPassiveMonitoring
        } catch (e: Exception) {
            Log.e(TAG, "Error checking HR passive capability", e)
            false
        }
    }

    suspend fun hasHeartRateMeasureCapability(): Boolean {
        return try {
            val capabilities = measureClient.getCapabilitiesAsync().await()
            DataType.HEART_RATE_BPM in capabilities.supportedDataTypesMeasure
        } catch (e: Exception) {
            Log.e(TAG, "Error checking HR measure capability", e)
            false
        }
    }

    fun registerPassiveCallback(callback: PassiveListenerCallback) {
        val config = PassiveListenerConfig.builder()
            .setDataTypes(setOf(DataType.HEART_RATE_BPM))
            .build()
        passiveMonitoringClient.setPassiveListenerCallback(config, callback)
    }

    fun unregisterPassiveCallback() {
        passiveMonitoringClient.clearPassiveListenerCallbackAsync()
    }

    fun registerMeasureCallback(callback: MeasureCallback) {
        measureClient.registerMeasureCallback(DataType.HEART_RATE_BPM, callback)
    }

    fun unregisterMeasureCallback(callback: MeasureCallback) {
        measureClient.unregisterMeasureCallbackAsync(DataType.HEART_RATE_BPM, callback)
    }
}
