package com.example.wearos.complication

import androidx.wear.watchface.complications.data.ComplicationData
import androidx.wear.watchface.complications.data.ComplicationType
import androidx.wear.watchface.complications.data.PlainComplicationText
import androidx.wear.watchface.complications.data.ShortTextComplicationData
import androidx.wear.watchface.complications.datasource.ComplicationRequest
import androidx.wear.watchface.complications.datasource.SuspendingComplicationDataSourceService
import com.example.wearos.R
import com.example.wearos.data.sensor.HealthDataHolder
import com.example.wearos.data.sensor.HealthDataHolder.getRiskLevel
import com.example.wearos.data.sensor.RiskLevel

class HrComplicationService : SuspendingComplicationDataSourceService() {

    override fun getPreviewData(type: ComplicationType): ComplicationData? {
        if (type != ComplicationType.SHORT_TEXT) return null
        return createComplicationData("72 bpm", "72 bpm — Bajo")
    }

    override suspend fun onComplicationRequest(request: ComplicationRequest): ComplicationData {
        val hr = HealthDataHolder.getFlatHR()
        val riskLevel = getRiskLevel(hr.toDouble())
        val riskLabel = when (riskLevel) {
            RiskLevel.ALTO -> getString(R.string.risk_alto)
            RiskLevel.MEDIO -> getString(R.string.risk_medio)
            RiskLevel.BAJO -> getString(R.string.risk_bajo)
        }

        val text = if (hr > 0) {
            getString(R.string.hr_value_template, hr)
        } else {
            getString(R.string.no_data)
        }
        val contentDescription = if (hr > 0) {
            "$text — $riskLabel"
        } else {
            text
        }

        return createComplicationData(text, contentDescription)
    }

    private fun createComplicationData(text: String, contentDescription: String) =
        ShortTextComplicationData.Builder(
            text = PlainComplicationText.Builder(text).build(),
            contentDescription = PlainComplicationText.Builder(contentDescription).build()
        ).build()
}
