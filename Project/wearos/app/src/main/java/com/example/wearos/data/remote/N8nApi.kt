package com.example.wearos.data.remote

import kotlinx.serialization.Serializable
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

@Serializable
data class N8nBody(
    val paciente_id: Int,
    val frecuenciaCardiaca: Double,
    val spo2: Double,
    val anomaliaEcg: String
)

interface N8nApi {

    @POST("")
    suspend fun sendTelemetry(@Body body: N8nBody): Response<Unit>
}
