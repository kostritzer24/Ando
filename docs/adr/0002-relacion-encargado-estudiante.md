# ADR-0002: Encargado y Estudiante se relacionan por una tabla intermedia, con parentesco en el vínculo

**Fecha:** 2026-09-20
**Estado:** Aceptado

## Contexto

El Capítulo IV describe a Encargado con un atributo `parentesco` como si fuera propio del encargado, y `usuario` en singular. RF-04 pide "vincular a un encargado con uno o varios estudiantes" y HU-27 exige que una cuenta con varios hijos cambie de estudiante con un selector, sin volver a iniciar sesión.

La dirección confirmó (Fase 0, pregunta 2): *"La cuenta se le da a un encargado, y a esa cuenta se le asignan los niños/estudiantes que tengan, es decir es una cuenta familiar."*

Queda abierto si un mismo Estudiante puede tener más de un Encargado con cuenta propia (por ejemplo, madre y padre separados, cada uno con su usuario). El enunciado no lo prohíbe ni lo exige explícitamente, y el patrón de "cuenta familiar" es compatible con ambos casos si el vínculo se modela como muchos-a-muchos.

## Opciones consideradas

1. **Encargado con lista fija de estudiantes en una sola tabla de unión, sin atributos propios en el vínculo.** El parentesco se queda en Encargado, como en el documento original.
2. **Tabla intermedia `GuardianStudentLink` con el parentesco movido al vínculo**, no al Encargado. Cada fila conecta un Encargado con un Estudiante y guarda el parentesco de esa relación específica.

Mover el parentesco al vínculo cuesta una tabla y un atributo más, pero evita un problema real: en familias reconstituidas un mismo Encargado puede ser "madre" de un estudiante y "tía" o "encargada legal" de otro vinculado a la misma cuenta. Dejar el parentesco en Encargado obligaría a elegir un solo valor que no aplicaría a todos sus estudiantes vinculados.

## Decisión

Se crea `GuardianStudentLink` (Encargado↔Estudiante) como tabla intermedia explícita, con `relationship` (parentesco) como atributo del vínculo, no del Encargado. `Guardian.user` es una relación uno a uno con `accounts.User` (una cuenta = un encargado = posible acceso a varios estudiantes). Un mismo Estudiante puede aparecer en más de un `GuardianStudentLink`, es decir, puede tener más de un Encargado con cuenta propia; RNF-04 (cada familia ve solo a sus estudiantes) se cumple filtrando siempre por los vínculos activos del Encargado autenticado, sin importar cuántos Encargados comparta un Estudiante.

## Consecuencias

- `Guardian` conserva `full_name, phone, messaging_number, occupation` y pierde `parentesco` frente al listado original del Capítulo IV — desviación documentada aquí, no silenciosa.
- El selector de estudiante de HU-27 recorre `GuardianStudentLink` filtrado por `guardian.user == usuario_actual`.
- El control de acceso a nivel de objeto (sección 14.2 del prompt maestro) se implementa siempre contra este vínculo, nunca contra un identificador de estudiante recibido en la URL.
- Si en el futuro un estudiante cambia de encargado principal (por ejemplo, custodia legal), se da de baja lógica al vínculo anterior y se crea uno nuevo; no se sobrescribe.
