package com.example.wearos.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query

@Dao
interface OfflineQueueDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(entry: OfflineTelemetryEntity)

    @Query("SELECT * FROM offline_queue WHERE estado = 'pendiente' ORDER BY timestamp ASC")
    suspend fun queryAllPendiente(): List<OfflineTelemetryEntity>

    @Query("UPDATE offline_queue SET estado = :estado, intentos = :intentos, ultimoIntento = :ultimoIntento WHERE id = :id")
    suspend fun updateStatus(id: Long, estado: String, intentos: Int, ultimoIntento: String?)

    @Query("SELECT COUNT(*) FROM offline_queue WHERE estado = 'pendiente'")
    suspend fun countPendiente(): Int

    @Query("DELETE FROM offline_queue WHERE id IN (SELECT id FROM offline_queue WHERE estado = 'pendiente' ORDER BY timestamp ASC LIMIT :limit)")
    suspend fun deleteOldest(limit: Int)
}
