# ADR-0008: El buzón pasa de mensajes enlazados a conversaciones con lectura por usuario

**Fecha:** 2026-10-26
**Estado:** Aceptado (reemplaza la nota de la sección 8.5 del prompt maestro sobre el buzón)

## Contexto

Hasta la Fase 16 el buzón guardaba mensajes enlazados por `original_message`: el mensaje raíz traía la sección, el asunto y un `status` único (`enviado`, `leido`, `respondido`). Solo la familia iniciaba un hilo y solo el centro respondía.

Tras la capacitación con docentes, Dirección encarga a una docente la comunicación con los padres (RF-38, RN-19). Ahora:

- docentes y Dirección inician conversaciones con un encargado puntual;
- todos los participantes responden, la familia incluida;
- cada persona necesita saber qué conversaciones tiene sin leer.

Un `status` en el mensaje raíz es compartido: si un docente abre el hilo, queda "leído" también para Dirección y para la familia. Además, el mensaje raíz no guardaba de qué estudiante se trataba, solo la sección.

## Opciones consideradas

1. **Mantener los mensajes enlazados** y agregar una tabla de lectura por usuario colgada del mensaje raíz. El estudiante, el encargado y la fecha del último mensaje tendrían que vivir en el mensaje raíz o recalcularse en cada listado.
2. **Un objeto `Conversation`** con estudiante, encargado, sección, asunto, quién la inició y `last_message_at`. Debajo van los `Message` y una `ConversationRead` (usuario, `last_read_at`) por persona.

## Decisión

Opción 2. El "no leído" se calcula por usuario comparando `last_message_at` con su `last_read_at`. Quien envía un mensaje queda como lector hasta ese momento, para que su propio mensaje no le aparezca como pendiente. La lectura nunca se le muestra a otro participante: sigue sin haber indicador de "visto" (HU-25).

La sección de la conversación es la sección activa del estudiante al iniciarla. Define qué docentes la ven, junto con quien la inició y Dirección.

## Consecuencias

- **Migración de datos.** Cada mensaje raíz se convierte en una conversación. El encargado sale del remitente y el estudiante es el vinculado a ese encargado con inscripción en la sección del mensaje. Las respuestas se cuelgan de la conversación sin recrearse, así que conservan `public_id`, fechas y remitentes. Del `status` viejo solo se puede traducir lo atribuible: cada remitente leyó hasta su último mensaje. Un "leído" sin respuesta no dice quién lo leyó y queda como no leído.
- **API.** `/messages/` se reemplaza por `/conversations/`, con `reply`, `unread-count` y `recipients`.
- **Borrado de datos.** `poblar_ciclo_2026` borra las tres tablas nuevas, en lugar de borrar `Message` sola.
