# Pruebas manuales en equipo (4 personas, 1 corrector)

Objetivo: encontrar bugs, huecos de funcionalidad y cosas raras de UX **antes** de seguir construyendo, sin que 4 personas toquen el mismo código y se rompa git.

## La regla de oro

> **Los 4 testers NO modifican código, NO commitean, NO hacen push.** Solo prueban y escriben hallazgos.
> **Una sola persona (el "corrector")** le da todos los hallazgos a su Claude Code y es la única que cambia código.

Así no hay conflictos de merge: el código sale de un único lugar.

## Flujo

1. **Preparación (todos, una vez).** Clonar el repo, cambiar a la rama de pruebas y levantar el sistema (sección "Entorno").
2. **Reparto.** Cada persona toma un set (A, B, C o D) de `plan-de-pruebas.md`. Cada set cubre módulos distintos.
3. **Ejecución.** Cada tester recorre los casos de su set **con el navegador a mano**, y en paralelo puede usar su Claude Code con `prompt-tester.md` para (a) revisar el código de su área buscando sospechas y (b) probar la API por consola.
4. **Registro.** Cada hallazgo se anota en **su propio archivo** `hallazgos/<SET>-<nombre>.md` usando `hallazgos/_PLANTILLA.md`. Un archivo por persona = cero choques.
5. **Entrega.** Los testers **no commitean sus hallazgos**: los mandan por chat/Drive (o los pega en un PR aparte si el corrector lo pide) al corrector.
6. **Corrección.** El corrector copia los 4 archivos a `docs/pruebas/hallazgos/`, abre Claude Code y le pega `prompt-corrector.md`. Ese agente triagea, planifica (y espera aprobación), arregla por lotes en una rama, y deja todo verificado.
7. **Re-prueba.** Cada tester vuelve a pasar los casos de sus hallazgos corregidos y confirma o reabre.

## Entorno (cada tester, en su máquina)

Cada quien tiene su **propia base SQLite local**, así que probar y "romper" datos no afecta a nadie más.

```bash
git fetch && git checkout <rama-de-pruebas>     # la que indique el corrector (hoy: fase-15-formatos-institucionales o main si ya se fusionó)

# Backend
cd backend
source .venv/bin/activate                        # Windows: .venv\Scripts\activate
export DYLD_LIBRARY_PATH=/opt/homebrew/lib       # solo macOS, para PDFs
# Windows: $env:WEASYPRINT_DLL_DIRECTORIES='C:\Program Files\swipl\bin' (ver CLAUDE.md)
rm -f db.sqlite3 && python manage.py migrate
python manage.py seed_demo                       # datos base + imprime usuarios
python manage.py seed_masivo                     # opcional: ~10 estudiantes por sección, notas, pagos, boletines en 3 estados
python manage.py runserver 8000

# Frontend (otra terminal)
cd frontend && npm install && cp .env.example .env && npm run dev   # http://localhost:5173
```

> Entren siempre por **`http://localhost:5173`** (no `127.0.0.1` ni la IP de la red) salvo que el caso diga lo contrario: la cookie de sesión es `SameSite=Strict`.

### Usuarios de prueba (contraseña de todos: `CambiaEstaClave2026`)

| Rol | Usuario | Portal |
|---|---|---|
| Dirección | `dir.demo` | /administrativo |
| Coordinación | `coord.demo` | /administrativo |
| Encargado de pagos | `pagos.demo` | /administrativo |
| Administrador del sistema | `admin.demo` | /administrativo |
| Docente | `docente.demo` | /operativo |
| Docente con sección a cargo (maestro guía) | `guia.demo` | /operativo |
| Tallerista | `tallerista.demo` | /operativo |
| Padre de familia | `familia.demo` | /portal |

Tips: usen **ventanas de incógnito distintas** para tener dos roles a la vez. El login tiene límite de 10 intentos por minuto por IP: si ven "Demasiados intentos seguidos", esperen un minuto, no es un bug. El caso del buzón (RN-16) bloquea `familia.demo` 24 h: háganlo al final o resetéen la base.

## Archivos de esta carpeta

| Archivo | Para quién |
|---|---|
| `plan-de-pruebas.md` | Todos: sets A–D, casos, severidades, checklist transversal, hallazgos ya conocidos |
| `hallazgos/_PLANTILLA.md` | Testers: copiar a `hallazgos/<SET>-<nombre>.md` |
| `prompt-tester.md` | Claude Code de cada tester (solo lectura) |
| `prompt-corrector.md` | **Únicamente** el Claude Code del corrector |
