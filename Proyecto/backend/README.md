# Backend — API Central y Gestión del Dominio Clínico

## Responsabilidad Arquitectónica

Núcleo del ecosistema que expone una API centralizada, gestiona la persistencia de datos relacionales y orquesta la lógica de negocio del dominio clínico del paciente. Actúa como punto de integración entre todos los módulos del sistema.

## Alcance Funcional

- Exposición de API REST para la comunicación entre el frontend, el microservicio de IA y los dispositivos de telemetría.
- Persistencia y consulta de datos maestros de pacientes, historiales clínicos y registros de triaje.
- Gestión del ciclo de vida del paciente dentro del sistema (registro, evaluación, alta, referencia).
- Coordinación de flujos de datos entre el motor de orquestación, la capa de IA y los dispositivos vestibles.
- Autenticación, autorización y control de acceso basado en roles del personal médico.
- Registro de auditoría y trazabilidad de todas las operaciones clínicas.

## Límites del Módulo

- No ejecuta modelos predictivos ni algoritmos de inteligencia artificial.
- No realiza procesamiento de señales biomédicas en tiempo real.
- No gestiona la comunicación directa con dispositivos IoT; recibe datos ya procesados desde la capa de adquisición.
