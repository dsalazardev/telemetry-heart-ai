## ADDED Requirements

### Requirement: Login de médicos con JWT
El sistema SHALL autenticar médicos por `correo` y `password`. Al validar, SHALL generar un access token JWT con `sub=usuario_id`, `tipo="medico"` y expiración de 30 minutos.

#### Scenario: Login exitoso
- **WHEN** se envía `POST /auth/login` con credenciales válidas de un médico
- **THEN** la respuesta contiene `access_token` (JWT) y `token_type: bearer`

#### Scenario: Login fallido por credenciales inválidas
- **WHEN** se envía `POST /auth/login` con credenciales incorrectas
- **THEN** la respuesta es HTTP 401 con detalle "Credenciales inválidas"

### Requirement: Hashing de contraseñas con bcrypt
El sistema SHALL hashear contraseñas con `passlib[bcrypt]` al crear usuarios. SHALL verificar passwords con `verify()`.

#### Scenario: Crear usuario con contraseña hasheada
- **WHEN** se crea un usuario con password "clave123"
- **THEN** el campo `password` almacenado en BD comienza con `$2b$`

### Requirement: Refresh de token
El sistema SHALL permitir renovar el access token con un refresh token válido.

#### Scenario: Refresh token exitoso
- **WHEN** se envía `POST /auth/refresh` con un refresh token válido
- **THEN** la respuesta contiene un nuevo `access_token` y `refresh_token`

### Requirement: Protección de endpoints con dependencia
El sistema SHALL exponer `get_current_user()` como dependencia FastAPI que verifica el JWT en el header `Authorization: Bearer <token>`.

#### Scenario: Acceder a endpoint protegido
- **WHEN** se envía una request a `GET /pacientes` con un JWT válido de médico
- **THEN** el endpoint responde con HTTP 200 y la lista de pacientes

#### Scenario: Acceder sin token
- **WHEN** se envía una request a `GET /pacientes` sin header Authorization
- **THEN** el endpoint responde con HTTP 401

### Requirement: Token JWT rotable para dispositivos WearOS
El sistema SHALL generar un JWT con `sub=dispositivo_id` y `exp=30d` al registrar un dispositivo. SHALL invalidar el token al revocar.

#### Scenario: Registrar dispositivo y obtener token
- **WHEN** se envía `POST /dispositivos` para vincular un dispositivo a un paciente
- **THEN** la respuesta contiene un `token_autenticacion` (JWT) válido por 30 días

#### Scenario: Revocar token de dispositivo
- **WHEN** se envía `PUT /dispositivos/{id}/revocar`
- **THEN** el token queda invalidado y requests posteriores con ese token reciben HTTP 401
