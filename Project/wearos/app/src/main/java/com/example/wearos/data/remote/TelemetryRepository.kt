package com.example.wearos.data.remote

import android.util.Log
import com.example.wearos.data.local.OfflineQueue
import com.example.wearos.data.local.TokenStorage
import kotlin.math.round
import kotlin.random.Random
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

class TelemetryRepository(
    private val backendApi: BackendApi,
    private val offlineQueue: OfflineQueue,
    private val tokenStorage: TokenStorage,
    private val n8nApi: N8nApi
) {

    companion object {
        private const val TAG = "TelemetryWearOS"
    }

    suspend fun registerDevice(modelo: String, pacienteId: Int): Result<DeviceRegistrationResponse> {
        return try {
            tokenStorage.saveModel(modelo)
            tokenStorage.savePacienteId(pacienteId)

            val response = backendApi.registerDevice(
                DeviceRegistrationRequest(
                    tipo = "WearOS",
                    modelo = modelo,
                    sistemaOperativo = "Wear OS ${android.os.Build.VERSION.RELEASE}",
                    paciente_id = pacienteId
                )
            )

            if (response.isSuccessful) {
                val body = response.body()!!
                tokenStorage.saveToken(body.tokenAutenticacion)
                tokenStorage.saveDeviceId(body.id)
                Log.i(TAG, "Device registered: id=${body.id}")
                Result.success(body)
            } else {
                Log.w(TAG, "Registration failed: ${response.code()}")
                Result.failure(Exception("HTTP ${response.code()}"))
            }
        } catch (e: Exception) {
            Log.e(TAG, "Registration error", e)
            Result.failure(e)
        }
    }

    suspend fun submitTelemetry(
        frecuenciaCardiaca: Double,
        spo2: Double?,
        timestamp: String,
        dispositivoId: Int
    ): Boolean {
        val request = TelemetryRequest(
            frecuenciaCardiaca = frecuenciaCardiaca,
            spo2 = spo2,
            timestamp = timestamp,
            dispositivo_id = dispositivoId
        )

        return try {
            val response = backendApi.submitTelemetry(request)
            if (response.isSuccessful) {
                Log.i(TAG, "Telemetry sent: fc=$frecuenciaCardiaca")
                true
            } else {
                Log.w(TAG, "Telemetry failed: ${response.code()}")
                enqueueOffline(request, timestamp)
                false
            }
        } catch (e: Exception) {
            Log.e(TAG, "Telemetry network error", e)
            enqueueOffline(request, timestamp)
            false
        }
    }

    suspend fun sendToN8n(pacienteId: Int, frecuenciaCardiaca: Double, anomaliaEcg: String) {
        try {
            val spo2Raw = 90.0 + Random.nextDouble() * 10.0
            val spo2 = round(spo2Raw * 10.0) / 10.0
            val body = N8nBody(
                paciente_id = pacienteId,
                frecuenciaCardiaca = frecuenciaCardiaca,
                spo2 = spo2,
                anomaliaEcg = anomaliaEcg
            )
            val response = n8nApi.sendTelemetry(body)
            if (response.isSuccessful) {
                Log.i(TAG, "n8n telemetry sent: fc=$frecuenciaCardiaca")
            } else {
                Log.w(TAG, "n8n telemetry failed: ${response.code()}")
            }
        } catch (e: Exception) {
            Log.e(TAG, "n8n telemetry error", e)
        }
    }

    private suspend fun enqueueOffline(request: TelemetryRequest, timestamp: String) {
        val payload = Json.encodeToString(request)
        offlineQueue.enqueue(timestamp, payload)
    }

    suspend fun processOfflineQueue() {
        offlineQueue.retryPending { payload ->
            try {
                val request = Json.decodeFromString<TelemetryRequest>(payload)
                val response = backendApi.submitTelemetry(request)
                if (response.isSuccessful) {
                    Log.i(TAG, "Offline telemetry sent")
                    true
                } else {
                    Log.w(TAG, "Offline retry failed: ${response.code()}")
                    false
                }
            } catch (e: Exception) {
                Log.e(TAG, "Offline retry error", e)
                false
            }
        }
    }
}
