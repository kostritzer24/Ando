import { beforeEach, describe, expect, it, vi } from "vitest";

import { http } from "@/app/http";

import { obtenerTodas } from "../resource";

vi.mock("@/app/http", () => ({ http: { get: vi.fn() } }));

const get = vi.mocked(http.get);

describe("obtenerTodas", () => {
  beforeEach(() => get.mockReset());

  it("pide la página grande y devuelve todos los registros aunque haya más de 25", async () => {
    const registros = Array.from({ length: 144 }, (_, i) => ({ public_id: String(i) }));
    get.mockResolvedValueOnce({ data: { count: 144, next: null, previous: null, results: registros } });

    const lista = await obtenerTodas("/students/", { section: "abc" });

    expect(get).toHaveBeenCalledWith("/students/", { params: { page_size: 200, section: "abc" } });
    expect(lista.results).toHaveLength(144);
  });

  it("sigue `next` hasta la última página", async () => {
    get
      .mockResolvedValueOnce({ data: { count: 3, next: "/students/?page=2", previous: null, results: [{ public_id: "1" }] } })
      .mockResolvedValueOnce({ data: { count: 3, next: "/students/?page=3", previous: null, results: [{ public_id: "2" }] } })
      .mockResolvedValueOnce({ data: { count: 3, next: null, previous: null, results: [{ public_id: "3" }] } });

    const lista = await obtenerTodas<{ public_id: string }>("/students/");

    expect(lista.results.map((r) => r.public_id)).toEqual(["1", "2", "3"]);
    expect(lista.next).toBeNull();
  });
});
