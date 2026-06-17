## ADDED Requirements

### Requirement: Collect heart rate via PassiveMonitoringClient
The system SHALL collect heart rate data in the background using Health Services `PassiveMonitoringClient` with `PassiveListenerService`.

#### Scenario: Background HR collection starts with foreground service
- **WHEN** the TelemetryForegroundService starts
- **THEN** the system SHALL register a PassiveListenerConfig with `PassiveMonitoringClient` to receive HR data points
- **AND** the system SHALL forward received HR values to the shared `HealthDataHolder` singleton

#### Scenario: Background HR data points are received
- **WHEN** Health Services delivers new HR data points via `PassiveListenerService.onNewDataPointsReceived`
- **THEN** the system SHALL extract the latest HR value (beats per minute)
- **AND** the system SHALL update `HealthDataHolder` with the new HR, timestamp, and status

### Requirement: Provide on-demand HR reading via MeasureClient
The system SHALL provide a mechanism to obtain a single real-time HR reading using Health Services `MeasureClient`.

#### Scenario: User triggers manual HR check
- **WHEN** the user taps "Check HR" on the UI
- **THEN** the system SHALL request a single reading from `MeasureClient`
- **AND** the system SHALL display the reading on screen within 5 seconds

### Requirement: Handle Health Services permissions at runtime
The system SHALL request Health Services permissions before accessing sensor data, branching by API level.

#### Scenario: Runtime permission request on API 36+
- **WHEN** the app starts on API 36+
- **THEN** the system SHALL request `HealthPermissions.READ_HEART_RATE` via `HealthConnectManager`
- **AND** the system SHALL show a rationale if permission was previously denied

#### Scenario: Runtime permission request on API 35 and below
- **WHEN** the app starts on API 35 or below
- **THEN** the system SHALL request `BODY_SENSORS` permission at runtime
- **AND** the system SHALL show a rationale if permission was previously denied

### Requirement: Support synthetic data for development
The system SHALL work with synthetic health data when the synthetic provider broadcast is active.

#### Scenario: Synthetic data provider active
- **WHEN** `adb shell am broadcast` has activated synthetic providers
- **THEN** the system SHALL receive synthetic HR data without requiring a physical sensor
- **AND** Health Services SHALL return data as if from a real sensor

### Requirement: Calculate risk level from HR thresholds
The system SHALL compute a risk level (bajo/medio/alto) based on HR thresholds.

#### Scenario: HR is in normal range (60-100 bpm)
- **WHEN** the current HR is between 60 and 100 inclusive
- **THEN** the risk level SHALL be "bajo" (green)

#### Scenario: HR is elevated (100-120 or 40-60 bpm)
- **WHEN** the current HR is between 100 and 120 exclusive, or between 40 and 60 exclusive
- **THEN** the risk level SHALL be "medio" (yellow/amber)

#### Scenario: HR is critical (>=120 or <=40 bpm)
- **WHEN** the current HR is >= 120 or <= 40
- **THEN** the risk level SHALL be "alto" (red)
