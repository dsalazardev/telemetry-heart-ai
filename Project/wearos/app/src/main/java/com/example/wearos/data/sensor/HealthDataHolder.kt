package com.example.wearos.data.sensor

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

data class HealthData(
    val heartRate: Double = 0.0,
    val timestamp: String = "",
    val dataAvailable: Boolean = false
)

enum class RiskLevel {
    BAJO, MEDIO, ALTO
}

object HealthDataHolder {
    private val _healthData = MutableStateFlow(HealthData())

    val healthData: StateFlow<HealthData> = _healthData.asStateFlow()

    fun updateHeartRate(hr: Double) {
        _healthData.value = HealthData(
            heartRate = hr,
            timestamp = java.time.Instant.now().toString(),
            dataAvailable = true
        )
    }

    fun getCurrentHeartRate(): Double = _healthData.value.heartRate

    fun getCurrentTimestamp(): String = _healthData.value.timestamp

    fun isDataAvailable(): Boolean = _healthData.value.dataAvailable

    fun getRiskLevel(hr: Double): RiskLevel {
        return when {
            hr <= 0 -> RiskLevel.BAJO
            hr >= 120 || (hr in 1.0..40.0) -> RiskLevel.ALTO
            hr > 100 || (hr in 40.0..60.0) -> RiskLevel.MEDIO
            else -> RiskLevel.BAJO
        }
    }

    fun getFlatHR(): Int {
        val hr = _healthData.value.heartRate
        return if (hr > 0) hr.toInt() else 0
    }
}
