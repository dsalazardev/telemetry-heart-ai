# Design: Frontend Architecture and User Experience

## Architecture Overview
The frontend will follow a modular, service-oriented architecture using Angular's standalone components. It will interact with the FastAPI backend using standard HTTP protocols and potentially WebSockets for real-time telemetry if supported.

## Design System (Visual Style)
- **Palette**:
    - Primary: HSL(220, 90%, 50%) - Deep Blue
    - Danger: HSL(0, 80%, 55%) - Alert Crimson
    - Warning: HSL(40, 95%, 50%) - Caution Amber
    - Success: HSL(140, 70%, 45%) - Stable Green
    - Background: HSL(220, 20%, 98%) (Light) / HSL(220, 25%, 10%) (Dark)
- **Typography**: Inter for readability, Outfit for headers.
- **Aesthetics**: Glassmorphism effects for cards, subtle shadows, and smooth hover state transitions.

## Key Modules & Components

### 1. Authentication (`/login`)
- **Login Component**: A centered card layout with medical branding.
- **Auth Guard**: Prevents access to protected routes without a valid JWT.

### 2. Main Layout (`/dashboard`)
- **Shell Component**: Sidebar navigation and Topbar for user profile/notifications.
- **Real-time Alert Bar**: A sticky header or sidebar section displaying the latest high-risk triage events.

### 3. Patient Management (`/pacientes`)
- **Patient List**: Data table with sorting by status/risk.
- **Patient Details**: Expanded view showing history, current telemetry, and predictive model explanations.

### 4. Telemetry Visualization
- **Metrics Chart**: Using a lightweight charting approach (or SVG/CSS) to show heart rate and other vital signs over time.
- **Predictive Results**: A specific section for the "Agentic AI" explanations.

## Data Flow
1. **ApiService**: Centralized service for `GET`, `POST`, `PUT`, `DELETE`.
2. **AuthInterceptor**: Injects `Authorization: Bearer <token>` into outgoing requests.
3. **State Management**: Each module will have a local service managing its state via `BehaviorSubject`.

## Backend Integration
- **Base URL**: `http://localhost:8000` (configurable).
- **Endpoints**:
    - `POST /auth/login`
    - `GET /pacientes`
    - `GET /alertas`
    - `GET /triajes`
    - `GET /telemetria`
