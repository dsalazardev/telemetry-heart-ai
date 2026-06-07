## ADDED Requirements

### Requirement: CRUD de pacientes
El sistema SHALL permitir crear, leer, actualizar y eliminar pacientes. La creación SHALL crear primero un `Usuario` con `tipo="paciente"` y luego un `Paciente` con FK a `usuarios.id`.

#### Scenario: Crear paciente con usuario
- **WHEN** se envía `POST /pacientes` con datos de usuario y fecha de nacimiento
- **THEN** se crean registros en `usuarios` y `pacientes` vinculados por FK

#### Scenario: Listar pacientes
- **WHEN** se envía `GET /pacientes`
- **THEN** la respuesta contiene la lista de pacientes con sus datos de usuario

### Requirement: CRUD de médicos
El sistema SHALL permitir crear, leer, actualizar y eliminar médicos. La creación SHALL crear primero un `Usuario` con `tipo="medico"` y luego un `Medico` con FK a `usuarios.id`.

#### Scenario: Crear médico con especialidad
- **WHEN** se envía `POST /medicos` con datos de usuario, especialidad y licencia
- **THEN** se crean registros en `usuarios` y `medicos` vinculados por FK

### Requirement: Gestión de perfil del paciente
El sistema SHALL permitir consultar y modificar el perfil clínico de un paciente (edad, sexo, tipoSangre, alergias).

#### Scenario: Actualizar perfil
- **WHEN** se envía `PUT /pacientes/{id}/perfil` con nuevos datos
- **THEN** el perfil del paciente se actualiza y persiste en BD

### Requirement: CRUD de patologías
El sistema SHALL permitir crear y listar patologías con código CIE-11, nombre, categoría, factorRiesgoCardiaco y pesoRiesgoModelo.

#### Scenario: Crear patología
- **WHEN** se envía `POST /patologias` con datos válidos
- **THEN** la patología se almacena en la tabla `patologias`

### Requirement: Gestión de historiales médicos
El sistema SHALL permitir asociar historiales médicos a un paciente, vinculados a una patología.

#### Scenario: Crear historial para paciente
- **WHEN** se envía `POST /pacientes/{id}/historiales` con patología_id, severidad y tratamiento
- **THEN** el historial se almacena en `historiales` con FK a `pacientes` y `patologias`
