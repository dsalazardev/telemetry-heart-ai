package com.example.wearos.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "offline_queue")
data class OfflineTelemetryEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val timestamp: String,
    val payload: String,
    val estado: String = "pendiente",
    val intentos: Int = 0,
    val ultimoIntento: String? = null
)
