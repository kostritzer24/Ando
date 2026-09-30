import { AxiosError, AxiosHeaders, type InternalAxiosRequestConfig } from "axios";
import { afterEach, describe, expect, it, vi } from "vitest";

import { http } from "../http";

function error401(url: string, detail: string): AxiosError {
  const config = { url, method: "post", headers: new AxiosHeaders() } as InternalAxiosRequestConfig;
  return new AxiosError("401", "ERR_BAD_REQUEST", config, null, {
    status: 401,
    statusText: "Unauthorized",
    data: { detail },
    headers: {},
    config,
  });
}

describe("interceptor de http", () => {
  afterEach(() => vi.restoreAllMocks());

  it("un 401 del login llega tal cual a la pantalla, sin intentar renovar el token", async () => {
    const post = vi.spyOn(http, "post");
    const bloqueada = "Esta cuenta está bloqueada temporalmente. Podés volver a intentar después de las 10:30.";
    const manejador = (http.interceptors.response as unknown as {
      handlers: { rejected: (e: unknown) => Promise<unknown> }[];
    }).handlers[0].rejected;

    await expect(manejador(error401("/auth/login/", bloqueada))).rejects.toMatchObject({
      response: { data: { detail: bloqueada } },
    });
    expect(post).not.toHaveBeenCalled();
  });
});
