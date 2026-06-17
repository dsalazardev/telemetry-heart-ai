## ADDED Requirements

### Requirement: Display heart rate on Tile
The Wear OS Tile SHALL display the current heart rate and connection status using `Material3TileService`.

#### Scenario: HR data available
- **WHEN** the tile is rendered
- **AND** HR data is available from `HealthDataHolder`
- **THEN** the tile SHALL display the current HR as a large number
- **AND** the tile SHALL display the risk level indicator (color: green/yellow/red)

#### Scenario: HR data unavailable
- **WHEN** the tile is rendered
- **AND** no HR data is available (device not worn, permissions not granted)
- **THEN** the tile SHALL display "--" or "No data"
- **AND** the indicator SHALL show a neutral color (gray)

### Requirement: Tile updates with new HR data
The system SHALL push tile updates when new HR data arrives.

#### Scenario: New HR received
- **WHEN** a new HR value is received from Health Services
- **THEN** the system SHALL call `TileService.requestRebuild()` or update via `Timeline`
- **AND** the tile SHALL render the updated value on next display
