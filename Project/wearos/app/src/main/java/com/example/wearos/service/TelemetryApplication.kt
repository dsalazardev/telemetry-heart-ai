package com.example.wearos.service

import android.app.Application
import com.example.wearos.data.local.OfflineQueue
import com.example.wearos.data.local.TokenStorage
import com.example.wearos.data.remote.AuthAuthenticator
import com.example.wearos.data.remote.AuthInterceptor
import com.example.wearos.data.remote.HttpClient
import com.example.wearos.data.remote.TelemetryRepository
import com.example.wearos.data.sensor.HealthSensor

class TelemetryApplication : Application() {

    lateinit var tokenStorage: TokenStorage
        private set
    lateinit var healthSensor: HealthSensor
        private set
    lateinit var offlineQueue: OfflineQueue
        private set
    lateinit var authInterceptor: AuthInterceptor
        private set
    lateinit var telemetryRepository: TelemetryRepository
        private set

    override fun onCreate() {
        super.onCreate()
        instance = this

        tokenStorage = TokenStorage(this)
        healthSensor = HealthSensor(this)
        offlineQueue = OfflineQueue(this)

        authInterceptor = AuthInterceptor()
        val authAuthenticator = AuthAuthenticator(tokenStorage, authInterceptor)
        val okHttpClient = HttpClient.createOkHttpClient(authInterceptor, authAuthenticator)
        val retrofit = HttpClient.createRetrofit(okHttpClient)
        val backendApi = HttpClient.createBackendApi(retrofit)

        telemetryRepository = TelemetryRepository(backendApi, offlineQueue, tokenStorage)
    }

    companion object {
        lateinit var instance: TelemetryApplication
            private set
    }
}
