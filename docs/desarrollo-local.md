# Cómo levantar el proyecto en local

Guía para correr el backend y el frontend en tu máquina y mostrarle al equipo lo que hay construido. Corré `cd backend && python manage.py seed_demo` después de las migraciones para tener datos de ejemplo (estudiantes, secciones, pagos con solventes e insolventes, etc.) — las credenciales de cada rol de prueba quedan impresas en la consola al correrlo.

Esto **no** es la guía de despliegue a producción (esa es `docs/despliegue.md`, se escribe en la Fase 14). Esto es solo para desarrollo y demostración local.

---

## 1. Requisitos

- **Python 3.12** (`python3 --version`)
- **Node.js 20 o superior** (`node --version`)
- **Git**

No hace falta PostgreSQL ni Neon para esto: en local, el backend usa SQLite automáticamente si no hay `DATABASE_URL` configurada.

---

## 2. Backend (Django)

Desde la raíz del repositorio:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # en Windows: .venv\Scripts\activate
pip install -r requirements/local.txt
```

Preparar la base de datos y los datos de prueba:

```bash
python manage.py migrate
python manage.py seed_demo
```

`seed_demo` crea los 8 roles del proyecto con un usuario de prueba por cada uno (la lista completa de usuarios y contraseñas queda impresa en la terminal, y también más abajo en este documento), más un ciclo escolar completo con secciones, estudiantes, asignaciones y pagos de ejemplo (algunos solventes, otros no) para poder mostrar el sistema con datos reales sin cargarlos a mano. Es un comando idempotente — correrlo de nuevo no duplica nada.

Levantar el servidor:

```bash
python manage.py runserver 8000
```

Dejalo corriendo. Podés confirmar que responde abriendo `http://localhost:8000/api/schema/docs/` en el navegador — ahí se ve la documentación interactiva de la API (Swagger).

---

## 3. Frontend (Vue)

Abrí **otra** terminal (el backend tiene que seguir corriendo en la primera). Desde la raíz del repositorio:

```bash
cd frontend
npm install
```

Crear el archivo de configuración local (una sola vez):

```bash
cp .env.example .env
```

El valor por defecto (`http://localhost:8000/api/v1`) ya apunta al backend que levantaste en el paso 2 — no hace falta cambiarlo.

Levantar el servidor de desarrollo:

```bash
npm run dev
```

Te va a dar una URL, normalmente `http://localhost:5173`. Abrila en el navegador.

---

## 4. Usuarios para probar

Los ocho, todos con la misma contraseña de siembra (**solo para desarrollo, nunca la uses en producción**):

| Usuario | Rol | Adónde entra |
|---|---|---|
| `dir.demo` | Dirección | Portal administrativo |
| `coord.demo` | Coordinación | Portal administrativo |
| `pagos.demo` | Encargado de pagos | Portal administrativo |
| `admin.demo` | Administrador del sistema | Portal administrativo |
| `docente.demo` | Docente | Portal operativo |
| `guia.demo` | Docente con sección a cargo | Portal operativo |
| `tallerista.demo` | Tallerista | Portal operativo |
| `familia.demo` | Padre de familia | Portal público |

**Contraseña para los ocho:** `CambiaEstaClave2026`

Con cualquiera de estos, `http://localhost:5173/ingresar` te deja entrar y te manda al portal que le corresponde a ese rol. Ahora mismo esa pantalla de destino solo dice "Hola, `<usuario>`" y una nota de qué falta — es exactamente lo que se construyó en esta fase, ni más ni menos.

**Qué sí podés mostrarle al equipo en esta fase:**

- Inicio de sesión real, contra una base de datos real.
- Que cada rol termina en el portal que le corresponde.
- Que una contraseña incorrecta muestra un error claro, sin decir si el usuario existe o no.
- Documentación interactiva de la API en `http://localhost:8000/api/schema/docs/`.

**Qué todavía no existe** (llega en fases siguientes): estudiantes, notas, asistencia, pagos, horarios, calendario, documentos, avisos, buzón. La Fase 3 es intencionalmente solo el cimiento de seguridad — así lo pide la sección 18 del prompt maestro.

---

## 5. Apagar todo

`Ctrl+C` en cada una de las dos terminales (backend y frontend).

---

## 6. Volver a empezar con datos limpios

Si el equipo rompe algo probando o querés reiniciar la demo:

```bash
cd backend
rm db.sqlite3
python manage.py migrate
python manage.py seed_demo
```

---

## 7. Si algo no arranca

- **`ModuleNotFoundError` o `ImportError` en el backend:** seguramente el entorno virtual no está activado. Corré `source .venv/bin/activate` de nuevo dentro de `backend/`.
- **El frontend no logra conectarse al backend (errores de red en la consola del navegador):** confirmá que el backend sigue corriendo en la terminal 1, y que `frontend/.env` tiene `VITE_API_BASE_URL=http://localhost:8000/api/v1`.
- **"Address already in use" al levantar el backend:** ya hay algo corriendo en el puerto 8000. Cerralo o usá otro puerto: `python manage.py runserver 8001` (y actualizá `VITE_API_BASE_URL` en consecuencia).
- **Querés confirmar que el backend por sí solo está sano:** desde `backend/`, con el entorno activado, corré `python manage.py check` y `python -m pytest -q` — no debería haber errores.

---

## 8. Para quien quiera ver las pruebas automatizadas correr

```bash
# Backend
cd backend && source .venv/bin/activate
ruff check .
python -m pytest -q

# Frontend
cd frontend
npm run lint
npm run typecheck
npm test

# Frontend, de extremo a punta contra un navegador real (necesita el
# backend corriendo con datos de seed_demo, y el frontend con `npm run dev`)
npm run e2e
```

Si cambiaste algo en el backend que afecte el contrato de la API (un campo nuevo, un endpoint nuevo), regenerá los tipos de TypeScript del frontend contra el backend local corriendo: `cd frontend && npm run types:generate`. Los tipos no se escriben a mano (sección 12.3 del prompt maestro).
