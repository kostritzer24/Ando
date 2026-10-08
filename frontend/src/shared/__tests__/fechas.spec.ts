import { describe, expect, it } from "vitest";

import { aFechaIso, fechaLegible, ultimoDiaHabilIso } from "../fechas";

describe("aFechaIso", () => {
  it("usa la fecha local, no la de UTC", () => {
    // 23:35 locales del 6 de octubre: en UTC-6 ya serían las 05:35 del día 7.
    expect(aFechaIso(new Date(2026, 9, 6, 23, 35))).toBe("2026-10-06");
  });

  it("rellena mes y día con ceros", () => {
    expect(aFechaIso(new Date(2026, 0, 5))).toBe("2026-01-05");
  });
});

describe("ultimoDiaHabilIso", () => {
  it("deja el día cuando es de lunes a viernes", () => {
    expect(ultimoDiaHabilIso(new Date(2026, 9, 7))).toBe("2026-10-07"); // miércoles
  });

  it("retrocede al viernes en sábado y domingo", () => {
    expect(ultimoDiaHabilIso(new Date(2026, 9, 10))).toBe("2026-10-09"); // sábado
    expect(ultimoDiaHabilIso(new Date(2026, 9, 11))).toBe("2026-10-09"); // domingo
  });
});

describe("fechaLegible", () => {
  it("pasa AAAA-MM-DD a DD/MM/AAAA", () => {
    expect(fechaLegible("2015-01-01")).toBe("01/01/2015");
  });

  it("deja igual lo que no es una fecha", () => {
    expect(fechaLegible("María")).toBe("María");
    expect(fechaLegible(12)).toBe(12);
    expect(fechaLegible(null)).toBe(null);
  });
});
