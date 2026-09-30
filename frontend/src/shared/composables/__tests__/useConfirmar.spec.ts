import { describe, expect, it } from "vitest";

import { confirmacionPendiente, confirmar } from "../useConfirmar";

describe("confirmar", () => {
  it("queda pendiente hasta que se responde, y se limpia al responder", async () => {
    const respuesta = confirmar({ titulo: "¿Dar de baja?", peligro: true });
    expect(confirmacionPendiente.value?.titulo).toBe("¿Dar de baja?");

    confirmacionPendiente.value?.resolver(true);
    await expect(respuesta).resolves.toBe(true);
    expect(confirmacionPendiente.value).toBeNull();
  });

  it("una confirmación nueva cancela la anterior en vez de dejarla colgada", async () => {
    const primera = confirmar({ titulo: "Primera" });
    const segunda = confirmar({ titulo: "Segunda" });

    await expect(primera).resolves.toBe(false);
    expect(confirmacionPendiente.value?.titulo).toBe("Segunda");
    confirmacionPendiente.value?.resolver(false);
    await expect(segunda).resolves.toBe(false);
  });
});
