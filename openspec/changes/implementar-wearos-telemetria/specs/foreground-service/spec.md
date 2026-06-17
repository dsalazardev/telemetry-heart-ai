## ADDED Requirements

### Requirement: Foreground Service collects HR continuously
The system SHALL run a `Foreground Service` with type `health` that continuously collects HR data and manages telemetry submission.

#### Scenario: Foreground service starts with the application
- **WHEN** the application launches
- **THEN** the system SHALL create a notification for the foreground service
- **AND** start the service with `startForeground()`
- **AND** the notification SHALL display current HR and risk level

#### Scenario: Foreground service registers Health Services listener
- **WHEN** the foreground service starts
- **THEN** the system SHALL register a `PassiveListenerConfig` with `PassiveMonitoringClient`
- **AND** the system SHALL set `HealthDataHolder.dataAvailable = true`

### Requirement: Foreground service notification updates with live data
The system SHALL update the foreground service notification periodically with the latest HR value.

#### Scenario: Notification updates on HR change
- **WHEN** a new HR value is received from Health Services
- **THEN** the system SHALL update the notification text with the current HR
- **AND** the notification SHALL reflect the current risk level color

### Requirement: Auto-start at boot
The system SHALL start the foreground service when the device boots up, if the user has granted permissions.

#### Scenario: Device boots with permissions granted
- **WHEN** the device finishes booting (`ACTION_BOOT_COMPLETED`)
- **AND** the user has granted Health Services permissions
- **THEN** the system SHALL start the foreground service
- **AND** begin collecting HR data

### Requirement: Foreground service stops on app close
The system SHALL stop the foreground service when the user swipes the app away or explicitly stops monitoring.

#### Scenario: User closes the app
- **WHEN** the user removes the app from recent tasks
- **THEN** the system SHALL stop the foreground service
- **AND** clean up Health Services listeners
