# Fase 4 (frontend) — Datos maestros: cierre

Primera fase del bloque de frontend (ver `docs/pendiente-frontend.md`), arrancado al cerrar la Fase 9 del backend. Cubre RF-02: los 8 catálogos del portal administrativo.

## Qué se construyó

- **Generación de tipos desde el esquema OpenAPI** (sección 12.3 del prompt maestro, pendiente desde la Fase 1): `openapi-typescript` + `npm run types:generate` produce `frontend/src/shared/types/api.ts` contra el backend local corriendo; `shared/types/models.ts` da alias cortos a los tipos que usa cada feature. No se volvió a escribir a mano ningún tipo de modelo del backend.
- **`AdminShell`**, primer layout de escritorio del proyecto: los componentes compartidos que ya existían (`TopAppBar`, `BottomTabBar`, `DayTabs`) son todos del portal público, mobile-first — el administrativo/operativo necesitaba su propio esqueleto (barra lateral con navegación, barra superior con usuario y cerrar sesión). Junto con `DataTable` (fila con línea inferior, nunca tarjeta con sombra — sección 15.4), `AppModal` y `FormSelect`, son la base reutilizable para el resto del bloque de frontend, no solo para esta fase.
- **`shared/api/resource.ts`**: un `crearRecursoCrud<T>()` genérico (listar/crear/actualizar/dar de baja) sobre cualquier endpoint REST estándar del backend — evita repetir la misma llamada a Axios ocho veces.
- **Catálogo genérico + dos pantallas propias**: `CatalogoSimplePage.vue`, con la lista de campos armada por configuración (`features/catalogo/config/campos.ts`), cubre Cursos, Tipos de actividad, Tipos de justificación, Tipos de documento, Becas y Artículos de convivencia — seis catálogos, un solo componente. `CiclosPage.vue` (unidades anidadas, con las fechas de entrega de notas y habilitación del boletín en solo lectura, calculadas por el backend — RN-10) y `SeccionesPage.vue` (selector de maestro guía, que solo aparece si el tipo es "académica" — ADR-0001) son las dos pantallas con lógica propia que ya estaban previstas en `docs/pendiente-frontend.md`.
- **Coordinación ve pero no edita**: `docs/permisos-roles.md` le da a Coordinación `V` en "Datos maestros" — las tres pantallas esconden los botones de agregar/editar/dar de baja para ese rol (el backend igual lo exige con `PermisoPorArea`; esto es solo para no mostrarle un botón que termina en 403).

## Bug real encontrado y corregido: la sesión no sobrevivía a un recargo de página

Al armar la primera prueba de extremo a extremo contra un navegador real, entrar por una URL directa a una pantalla del catálogo mandaba siempre a `/ingresar`, aunque la persona ya hubiera iniciado sesión segundos antes. La causa: el token de acceso vive solo en memoria (sección 14.1, a propósito, nunca en `localStorage`), y nada reconstruía la sesión a partir de la cookie de refresco al arrancar la aplicación — cualquier recargo de página, o abrir un enlace guardado, perdía la sesión aunque la cookie siguiera siendo válida.

La causa raíz era más profunda que un descuido del frontend: **no existía ningún endpoint que devolviera "quién soy"**. `POST /auth/refresh/` solo entrega un token nuevo, y `GET /users/{id}/` es exclusivo de Dirección/Administrador (área "Usuarios y roles") — un docente o una familia no podían consultar su propio perfil por ahí. Se agregó `GET /auth/me/` al backend (`apps/accounts/api/views.py`), separado a propósito del área de administración de usuarios: cualquier persona autenticada consulta su propio perfil, sin pasar por un permiso pensado para administrar cuentas ajenas. Con eso, `main.ts` reconstruye la sesión (`POST /auth/refresh/` + `GET /auth/me/`) antes de montar el router, así el guard de la primera navegación ya sabe quién es el usuario.

Se agregaron 3 pruebas de backend (`apps/accounts/tests/test_auth_me.py`) y 4 pruebas de extremo a punta en un navegador real (`frontend/e2e/sesion-persistente.spec.ts`) que verifican exactamente este escenario: recargar la página, entrar por un enlace directo, quedarse en `/ingresar` sin sesión, y no ver el formulario de login de nuevo si ya hay sesión activa.

## Bug real encontrado y corregido: "dar de baja" no vacía la lista

La primera versión de la prueba de extremo a punta asumía que dar de baja un curso lo sacaba de la lista. Eso reveló que **la prueba estaba mal, no el código**: HU-02 dice que nada se borra de verdad, y el backend (`CatalogViewSet`, sin filtro de `is_active`) efectivamente sigue devolviendo los registros dados de baja — es el diseño correcto, para poder reactivarlos. Lo que faltaba era la mitad del frontend: las tres pantallas de catálogo ahora esconden los dados de baja por omisión (con un botón "Mostrar los dados de baja" para revelarlos) y ofrecen "Reactivar" en vez de "Editar"/"Dar de baja" para esos registros — mismo patrón que ya se había visto del lado del backend en fases anteriores (cuando la prueba asume mal y el código está bien, se corrige la prueba; acá la prueba reveló una pantalla a medio construir).

## Verificación real

34 pruebas de componente (Vitest) más 11 pruebas de extremo a punta contra un navegador real (Playwright/Chromium) y el backend local con `seed_demo`: iniciar sesión, recargar la página, entrar por enlace directo, crear/editar/dar de baja/reactivar un curso, agregar una unidad a un ciclo existente y confirmar que las fechas calculadas (RN-10) aparecen solas, crear una sección académica con maestro guía, confirmar que el selector de maestro guía desaparece para una sección de taller, y confirmar que Coordinación ve el catálogo sin botones de escritura. `vue-tsc --noEmit` y `eslint` sin errores.

Nota sobre la corrida de extremo a punta: el límite de tasa del login (RNF-05, 10 intentos/minuto) es real incluso en desarrollo local — correr la suite completa de Playwright de un tirón hace más de 10 inicios de sesión en menos de 15 segundos y el último puede toparse con el límite. No es un defecto: es el mismo límite de tasa que protege producción, funcionando. Los archivos de prueba están escritos para poder correrse sueltos sin este problema.

## Siguiente

Fase 5 (frontend) — Expedientes y asignaciones: inscribir estudiante, expediente con la pestaña de datos sensibles restringida a Dirección, encargados y sus vínculos, asignación de docente/tallerista a curso-sección. Detalle completo en `docs/pendiente-frontend.md`.
