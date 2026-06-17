package com.example.wearos.data.remote

import kotlinx.serialization.Serializable
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

@Serializable
data class DeviceRegistrationRequest(
    val tipo: String,
    val modelo: String,
    val sistemaOperativo: String,
    val paciente_id: Int
)

@Serializable
data class DeviceRegistrationResponse(
    val id: Int,
    val tokenAutenticacion: String
)

@Serializable
data class TelemetryRequest(
    val frecuenciaCardiaca: Double,
    val spo2: Double? = null,
    val anomaliaEcg: String? = null,
    val timestamp: String,
    val dispositivo_id: Int
)

@Serializable
data class TelemetryResponse(
    val id: Int
)

interface BackendApi {

    @POST("dispositivos")
    suspend fun registerDevice(@Body request: DeviceRegistrationRequest): Response<DeviceRegistrationResponse>

    @POST("telemetria")
    suspend fun submitTelemetry(@Body request: TelemetryRequest): Response<TelemetryResponse>
}
