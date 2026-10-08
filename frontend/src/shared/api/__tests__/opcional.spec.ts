import { AxiosError } from "axios";
import { describe, expect, it } from "vitest";

import { opcional } from "../opcional";

function errorHttp(status: number): AxiosError {
  const error = new AxiosError("falló");
  error.response = { status } as AxiosError["response"];
  return error;
}

describe("opcional", () => {
  it("devuelve el resultado cuando la petición sale bien", async () => {
    expect(await opcional(Promise.resolve([1, 2]), [])).toEqual([1, 2]);
  });

  it("usa el valor vacío cuando el rol no tiene permiso (403)", async () => {
    expect(await opcional(Promise.reject(errorHttp(403)), ["vacío"])).toEqual(["vacío"]);
  });

  it("propaga cualquier otro error", async () => {
    await expect(opcional(Promise.reject(errorHttp(500)), [])).rejects.toBeInstanceOf(AxiosError);
  });
});
