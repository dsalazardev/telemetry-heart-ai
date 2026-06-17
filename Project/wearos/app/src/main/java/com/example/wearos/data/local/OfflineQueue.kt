package com.example.wearos.data.local

import android.content.Context
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.first
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonPrimitive
import java.time.Instant

class OfflineQueue(private val context: Context) {

    private val db = TelemetryDatabase.getInstance(context)
    private val dao = db.offlineQueueDao()
    private val json = Json { ignoreUnknownKeys = true }

    companion object {
        private const val MAX_QUEUE_SIZE = 1000
        private const val MAX_RETRIES = 10
    }

    suspend fun enqueue(timestamp: String, payload: String) {
        val count = dao.countPendiente()
        if (count >= MAX_QUEUE_SIZE) {
            dao.deleteOldest(count - MAX_QUEUE_SIZE + 1)
        }
        dao.insert(
            OfflineTelemetryEntity(
                timestamp = timestamp,
                payload = payload,
                estado = "pendiente",
                intentos = 0
            )
        )
    }

    suspend fun dequeue(): List<OfflineTelemetryEntity> {
        return dao.queryAllPendiente()
    }

    suspend fun markSent(id: Long) {
        dao.updateStatus(id, "enviado", 0, Instant.now().toString())
    }

    suspend fun markError(id: Long, intentos: Int) {
        val newIntentos = intentos + 1
        val estado = if (newIntentos >= MAX_RETRIES) "error" else "pendiente"
        dao.updateStatus(id, estado, newIntentos, Instant.now().toString())
    }

    suspend fun retryPending(onSend: suspend (String) -> Boolean) {
        val pending = dequeue()
        for (entry in pending) {
            val backoffSeconds = minOf(30L * (1L shl entry.intentos), 3600L)
            if (entry.ultimoIntento != null) {
                val lastAttempt = Instant.parse(entry.ultimoIntento)
                val elapsed = Instant.now().epochSecond - lastAttempt.epochSecond
                if (elapsed < backoffSeconds) continue
            }
            val success = onSend(entry.payload)
            if (success) {
                markSent(entry.id)
            } else {
                markError(entry.id, entry.intentos)
            }
        }
    }
}
