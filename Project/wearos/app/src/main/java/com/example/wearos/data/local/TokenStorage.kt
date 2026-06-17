package com.example.wearos.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.tokenStore: DataStore<Preferences> by preferencesDataStore(name = "token_prefs")

class TokenStorage(private val context: Context) {

    companion object {
        private val TOKEN_KEY = stringPreferencesKey("jwt_token")
        private val DEVICE_ID_KEY = stringPreferencesKey("device_id")
        private val MODEL_KEY = stringPreferencesKey("device_model")
        private val PACIENTE_ID_KEY = stringPreferencesKey("paciente_id")
    }

    val tokenFlow: Flow<String?> = context.tokenStore.data.map { prefs ->
        prefs[TOKEN_KEY]
    }

    val deviceIdFlow: Flow<Int?> = context.tokenStore.data.map { prefs ->
        prefs[DEVICE_ID_KEY]?.toIntOrNull()
    }

    suspend fun saveToken(token: String) {
        context.tokenStore.edit { prefs ->
            prefs[TOKEN_KEY] = token
        }
    }

    suspend fun getToken(): String? {
        return context.tokenStore.data.first()[TOKEN_KEY]
    }

    suspend fun saveDeviceId(deviceId: Int) {
        context.tokenStore.edit { prefs ->
            prefs[DEVICE_ID_KEY] = deviceId.toString()
        }
    }

    suspend fun getDeviceId(): Int? {
        return context.tokenStore.data.first()[DEVICE_ID_KEY]?.toIntOrNull()
    }

    suspend fun saveModel(model: String) {
        context.tokenStore.edit { prefs ->
            prefs[MODEL_KEY] = model
        }
    }

    suspend fun getModel(): String? {
        return context.tokenStore.data.first()[MODEL_KEY]
    }

    suspend fun savePacienteId(pacienteId: Int) {
        context.tokenStore.edit { prefs ->
            prefs[PACIENTE_ID_KEY] = pacienteId.toString()
        }
    }

    suspend fun getPacienteId(): Int? {
        return context.tokenStore.data.first()[PACIENTE_ID_KEY]?.toIntOrNull()
    }

    suspend fun clear() {
        context.tokenStore.edit { prefs ->
            prefs.remove(TOKEN_KEY)
            prefs.remove(DEVICE_ID_KEY)
            prefs.remove(MODEL_KEY)
            prefs.remove(PACIENTE_ID_KEY)
        }
    }
}
