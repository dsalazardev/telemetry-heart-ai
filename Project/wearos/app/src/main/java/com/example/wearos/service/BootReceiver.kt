package com.example.wearos.service

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

class BootReceiver : BroadcastReceiver() {

    companion object {
        private const val TAG = "TelemetryWearOS"
    }

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            Log.i(TAG, "BootReceiver: BOOT_COMPLETED received")
            val serviceIntent = Intent(context, TelemetryForegroundService::class.java)
            context.startForegroundService(serviceIntent)
        }
    }
}
