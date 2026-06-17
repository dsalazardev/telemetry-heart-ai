## ADDED Requirements

### Requirement: Store failed telemetry in Room offline queue
The system SHALL store telemetry payloads that failed to send in a local Room database for later retry.

#### Scenario: Telemetry submission fails
- **WHEN** POST /telemetria fails (network error, timeout, or server error)
- **THEN** the system SHALL insert the telemetry payload into the Room offline queue
- **AND** the queue entry SHALL include: `timestamp`, `payload` (serialized JSON), `estado` ("pendiente"), `intentos` (0), `ultimoIntento` (null)

#### Scenario: Successful telemetry is not queued
- **WHEN** POST /telemetria succeeds with HTTP 201
- **THEN** the system SHALL NOT add the payload to the offline queue

### Requirement: Retry queued telemetry with exponential backoff
The system SHALL periodically attempt to resend queued telemetry entries, with exponential backoff between retries.

#### Scenario: Connectivity restored
- **WHEN** network connectivity becomes available after a period of being offline
- **THEN** the system SHALL query Room for entries with estado "pendiente"
- **AND** attempt to resend them in FIFO order
- **AND** on success, update entry status to "enviado"
- **AND** on failure, increment `intentos` and update `ultimoIntento`

#### Scenario: Exponential backoff
- **WHEN** a queued entry fails to send
- **THEN** the system SHALL wait `min(30 * 2^intentos, 3600)` seconds before next retry
- **AND** entries with more than 10 failed attempts SHALL be marked as "error"

### Requirement: Limit queue size
The system SHALL prevent unbounded growth of the offline queue.

#### Scenario: Queue exceeds 1000 entries
- **WHEN** the offline queue reaches 1000 entries
- **THEN** the system SHALL evict the oldest "pendiente" entries to make room
- **AND** evicted entries SHALL be marked as "descartado" with a reason
