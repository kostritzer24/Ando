# Dirección visual — Fase 2

Documento de diseño exigido por la sección 15.1 del prompt maestro: paleta con nombre, tipografías y su papel, escala tipográfica, escala de espaciado, radios, sombras y principios — más las **dos propuestas distintas** con la pantalla de ejemplo (calendario semanal del portal público, RF-28), para que el equipo elija una antes de construir los componentes base en la Fase 3.

## Punto de partida: el logo

RNF-08 exige usar los colores oficiales del centro, no una paleta genérica. Se extrajeron por muestreo de píxeles del archivo `docs/LOGO LOS PATOJOS VECTORIZADOsin fondo.png` (documentado en `docs/fase-1-plan-maestro.md`):

| Color de marca | Valor extraído del logo |
|---|---|
| Azul | `#2AA9E0` |
| Verde | `#68B840` |
| Amarillo/dorado | `#F8C018` |
| Rojo | `#E83838` |

Estos cuatro valores son el punto de partida de ambas propuestas, pero **no se usan tal cual en texto sobre blanco**: varios (especialmente el amarillo) no alcanzan el contraste mínimo de WCAG 2.1 AA (4.5:1 para texto normal) contra un fondo claro. Cada propuesta deriva de estos cuatro tonos una versión ajustada en profundidad para texto/iconos y conserva el tono original para superficies grandes (chips, fondos de estado). Ambas propuestas fueron revisadas contra la lista de señales de interfaz genérica de la sección 15.4 del prompt maestro (sin degradados decorativos, sin tarjetas idénticas con la misma sombra, sin etiquetas en mayúsculas sostenidas, sin flechas al final de botones, sin emoji como ícono, sin animación de scroll, sin metadatos unidos por puntos medios, sin numeración 01/02/03 fuera de una secuencia real).

## Las dos propuestas

| | Propuesta A — Comunidad | Propuesta B — Trámite claro |
|---|---|---|
| Enlace | [Ver pantalla de ejemplo](https://claude.ai/code/artifact/14e878fa-4b95-4dc4-b9aa-cfc90b90e428) | [Ver pantalla de ejemplo](https://claude.ai/code/artifact/af105aa9-d322-4492-8374-d4dc82e0a965) |
| Referencia de tono | ClassDojo / Seesaw (cálido, familiar) | GOV.UK Design System (claro, funcional) |
| Idea de layout | Agenda vertical por día; el hexágono de cintas del logo se aplana en los chips de día y en la insignia de "próxima clase" | Fila con línea fina en vez de tarjeta; numeral de fecha grande como masthead; color solo en el enlace activo y en tres etiquetas de estado |
| Dónde vive la audacia visual | La forma hexagonal heredada del logo, usada de forma funcional (selector de día, insignia de próxima clase) | El numeral de fecha en tamaño gigante, como en un servicio de trámite en línea |

Ambas muestran la misma pantalla con el mismo contenido (María Ximena Pérez Tzul, Segundo básico A, martes 16 de septiembre) para que la comparación sea sobre estilo, no sobre contenido.

---

## Propuesta A — "Comunidad"

### Paleta
| Nombre | Valor | Uso |
|---|---|---|
| Azul Patojismo | `#1F8FC2` (ajustado de `#2AA9E0` para AA sobre blanco) | Color primario: enlaces, botones, día activo |
| Verde Patojismo | `#4F9A33` (ajustado de `#68B840`) | Categoría de curso, estado positivo, talleres |
| Dorado Patojismo | `#B9821A` (ajustado de `#F8C018`, demasiado claro para texto) | Categoría de curso, avisos institucionales |
| Rojo Patojismo | `#C53A3A` (ajustado de `#E83838`) | Alertas, categoría de curso |
| Tinta | `#16232B` | Texto principal, fondos de énfasis (insignia "próxima clase") |
| Papel | `#FBFDFE` | Fondo de pantalla |

### Tipografía
| Papel | Tipografía | Uso |
|---|---|---|
| Título/display | Baloo 2, 600–700 | Encabezados de pantalla, nombre de la app, insignia de próxima clase |
| Cuerpo/interfaz | Work Sans, 400–600 | Todo el texto de lectura, etiquetas, botones |

Solo dos familias — nada compite con la lectura en un teléfono de gama baja.

### Escala tipográfica
`0.68rem` (etiquetas pequeñas) · `0.78rem` (metadatos) · `0.9rem` (cuerpo) · `1.05rem` (subtítulo) · `1.35rem` (título de pantalla) · `2.6rem` (display, uso puntual)

### Escala de espaciado
`0.15rem · 0.3rem · 0.45rem · 0.6rem · 0.85rem · 1.15rem · 1.3rem` — base de ~4px, múltiplos irregulares a propósito para que el espaciado seleccionado responda al peso visual de cada bloque, no a una tabla rígida de 8 en 8.

### Radios y sombras
Radios entre 6px (chips pequeños) y 18px (tarjeta grande); el hexágono es la única forma no redondeada. Una sola sombra, reservada para el marco del teléfono en esta maqueta y, en producción, para superficies flotantes puntuales (modal, menú) — nunca repetida en cada tarjeta de contenido.

### Principios de esta dirección
- El color de marca clasifica, no decora: cada curso lleva un punto de color según su área, no un color aleatorio.
- La forma hexagonal del logo se reutiliza en un lugar funcional (selector de día, insignia), no como fondo decorativo.
- Tono cálido en el texto ("Lo que María tiene esta semana"), nunca infantil.

---

## Propuesta B — "Trámite claro"

### Paleta
| Nombre | Valor | Uso |
|---|---|---|
| Azul de acción | `#1C6EA4` (ajustado de `#2AA9E0`) | Único color con función interactiva: enlace activo, botón, fecha de hoy |
| Tinta | `#14181C` | Texto principal |
| Papel | `#FFFFFF` | Fondo de pantalla |
| Línea | `#D8DDE1` | Divisores entre filas, en vez de tarjetas |
| Etiqueta taller | fondo `#E4F1DE` / texto `#24531A` (par derivado del verde de marca) | Estado "Taller" |
| Etiqueta aviso | fondo `#FCF0C9` / texto `#6B4E00` (par derivado del dorado de marca) | Estado "Aviso" |

El rojo de marca queda reservado para alertas reales (falta sin justificar, pago vencido) y no aparece en esta pantalla — es deliberado: en esta dirección el color se gasta con cuentagotas.

### Tipografía
| Papel | Tipografía | Uso |
|---|---|---|
| Título/número | Archivo, 700–900 | El numeral de fecha, títulos de pantalla |
| Cuerpo/interfaz/datos | Public Sans, 400–700, `tabular-nums` en horas | Todo el texto de lectura y las horas de la agenda |

Misma familia de espíritu que usan los portales de trámites en línea (Public Sans es la tipografía del sistema de diseño del gobierno de Estados Unidos), elegida por su legibilidad comprobada con público de alfabetización digital dispar — no por moda.

### Escala tipográfica
`0.64rem` (íconos de navegación) · `0.72rem` (metadatos) · `0.8rem` (cuerpo secundario) · `0.88rem` (cuerpo) · `1.05rem` (subtítulo) · `2.6rem` (numeral de fecha)

### Escala de espaciado
`0.15rem · 0.3rem · 0.5rem · 0.65rem · 0.9rem · 1.1rem` — más compacta que la Propuesta A, porque esta dirección prioriza densidad de información sobre aire entre bloques.

### Radios y sombras
Radios de 3–8px en toda la interfaz, casi rectos. Sin sombra en ningún componente de contenido — la separación es siempre una línea de 1px. La única sombra de esta maqueta, igual que en la Propuesta A, es la del marco del teléfono (un recurso de esta presentación, no de la interfaz real).

### Principios de esta dirección
- Una fila, una línea — nunca una tarjeta con sombra por cada clase.
- El color siempre significa algo (enlace, estado); nunca decora.
- El numeral de fecha es el único elemento con licencia para ser grande — todo lo demás se mantiene en un rango tipográfico angosto.

---

## Próximo paso

Con estas dos direcciones documentadas, el punto de control de la Fase 2 es que el equipo elija una (o pida ajustes puntuales sobre una de las dos) antes de construir la biblioteca de componentes base en la Fase 3. Ninguna pantalla de producción se construye todavía con ninguna de las dos paletas — eso es, literalmente, lo que dice la sección 15.1: *"Hasta que haya una elegida, construyes los componentes base."*
