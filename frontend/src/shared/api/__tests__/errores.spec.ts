import { AxiosError } from "axios";
import { describe, expect, it } from "vitest";

import { mensajeDelServidor } from "../errores";

function error400(data: unknown): AxiosError {
  const error = new AxiosError("falló");
  error.response = { status: 400, data } as AxiosError["response"];
  return error;
}

describe("mensajeDelServidor", () => {
  it("antepone el nombre del campo cuando se conoce", () => {
    const e = error400({ first_name: ["Este campo no puede estar en blanco."] });
    expect(mensajeDelServidor(e, "x")).toBe("Nombres: Este campo no puede estar en blanco.");
  });

  it("usa el mensaje tal cual cuando el campo no tiene etiqueta", () => {
    expect(mensajeDelServidor(error400({ detail: "Ya existe." }), "x")).toBe("Ya existe.");
    expect(mensajeDelServidor(error400(["Hay un cruce de horario."]), "x")).toBe("Hay un cruce de horario.");
  });

  it("devuelve el mensaje por defecto si no es un 400 legible", () => {
    expect(mensajeDelServidor(new Error("red"), "No se pudo guardar.")).toBe("No se pudo guardar.");
    expect(mensajeDelServidor(error400({}), "No se pudo guardar.")).toBe("No se pudo guardar.");
  });
});
