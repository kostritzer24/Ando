/**
 * Nombre del archivo que propone el servidor en `Content-Disposition`.
 * Prefiere la versión UTF-8 (`filename*`), que conserva los acentos; si no
 * hay, la simple, y si tampoco, `porOmision`.
 */
export function nombreDeArchivo(headers: Record<string, unknown>, porOmision: string): string {
  const disposicion = String(headers["content-disposition"] ?? "");
  const utf8 = /filename\*=UTF-8''([^;]+)/i.exec(disposicion);
  if (utf8) {
    try {
      return decodeURIComponent(utf8[1]);
    } catch {
      // Codificación rota: se cae a la versión simple.
    }
  }
  return /filename="?([^";]+)"?/.exec(disposicion)?.[1] ?? porOmision;
}
