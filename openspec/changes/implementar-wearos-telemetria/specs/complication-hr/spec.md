## ADDED Requirements

### Requirement: Display heart rate on watch face complication
The system SHALL display the current heart rate as a `SHORT_TEXT` complication on the watch face, using `SuspendingComplicationDataSourceService`.

#### Scenario: HR data available
- **WHEN** the system requests complication data via `onComplicationRequest`
- **AND** HR data is available from `HealthDataHolder`
- **THEN** the complication SHALL return a `ShortTextComplicationData` with the HR value as primary text
- **AND** the complication SHALL include the risk level as content description
- **AND** the complication SHALL use green/yellow/red color coding based on risk

#### Scenario: HR data unavailable
- **WHEN** the system requests complication data
- **AND** no HR data is available
- **THEN** the complication SHALL return "--" as primary text
- **AND** the content description SHALL indicate "No data"

### Requirement: Push complication updates on HR change
The system SHALL notify the system when complications should be updated with new HR data.

#### Scenario: New HR received, complication notified
- **WHEN** a new HR value is received from Health Services
- **THEN** the system SHALL call `SuspendingComplicationDataSourceService.notifyComplicationUpdate()`
- **AND** the complication SHALL render the updated value on next watch face refresh
