package com.example.wearos.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(entities = [OfflineTelemetryEntity::class], version = 1, exportSchema = false)
abstract class TelemetryDatabase : RoomDatabase() {

    abstract fun offlineQueueDao(): OfflineQueueDao

    companion object {
        @Volatile
        private var INSTANCE: TelemetryDatabase? = null

        fun getInstance(context: Context): TelemetryDatabase {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: Room.databaseBuilder(
                    context.applicationContext,
                    TelemetryDatabase::class.java,
                    "telemetry_db"
                ).build().also { INSTANCE = it }
            }
        }
    }
}
