package com.example.wearos.data.remote

import android.util.Log
import com.example.wearos.BuildConfig
import com.example.wearos.data.local.TokenStorage
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import java.util.concurrent.TimeUnit

class AuthInterceptor : Interceptor {

    @Volatile
    var token: String? = null

    override fun intercept(chain: Interceptor.Chain): Response {
        val currentToken = token
        val request = if (currentToken != null) {
            chain.request().newBuilder()
                .addHeader("Authorization", "Bearer $currentToken")
                .build()
        } else {
            chain.request()
        }
        return chain.proceed(request)
    }
}

class AuthAuthenticator(
    private val tokenStorage: TokenStorage,
    private val authInterceptor: AuthInterceptor
) : okhttp3.Authenticator {

    private val json = Json { ignoreUnknownKeys = true }
    private val jsonMediaType = "application/json".toMediaType()
    private val tempClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .build()

    companion object {
        private const val TAG = "TelemetryWearOS"
    }

    override fun authenticate(route: okhttp3.Route?, response: Response): Request? {
        if (response.request.header("Authorization") == null) return null
        if (response.priorResponse?.code == 401) return null

        return try {
            val pacienteId = runBlocking { tokenStorage.getPacienteId() } ?: return null
            val model = runBlocking { tokenStorage.getModel() } ?: "Unknown"

            val requestBody = json.encodeToString(
                DeviceRegistrationRequest(
                    tipo = "WearOS",
                    modelo = model,
                    sistemaOperativo = "Wear OS ${android.os.Build.VERSION.RELEASE}",
                    paciente_id = pacienteId
                )
            )

            val registerRequest = Request.Builder()
                .url("${BuildConfig.BACKEND_URL}/dispositivos")
                .post(requestBody.toRequestBody(jsonMediaType))
                .build()

            val registerResponse = tempClient.newCall(registerRequest).execute()
            if (!registerResponse.isSuccessful) {
                Log.w(TAG, "Auth refresh failed: ${registerResponse.code}")
                return null
            }

            val body = registerResponse.body?.string() ?: return null
            val registration = json.decodeFromString<DeviceRegistrationResponse>(body)
            val newToken = registration.tokenAutenticacion

            runBlocking {
                tokenStorage.saveToken(newToken)
                tokenStorage.saveDeviceId(registration.id)
            }
            authInterceptor.token = newToken

            response.request.newBuilder()
                .header("Authorization", "Bearer $newToken")
                .build()
        } catch (e: Exception) {
            Log.e(TAG, "Auth refresh error", e)
            null
        }
    }
}
