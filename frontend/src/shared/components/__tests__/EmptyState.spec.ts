import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import EmptyState from "../EmptyState.vue";

describe("EmptyState", () => {
  it("muestra título y descripción", () => {
    const wrapper = mount(EmptyState, {
      props: { titulo: "Sin avisos", descripcion: "Todavía no hay avisos publicados." },
    });
    expect(wrapper.text()).toContain("Sin avisos");
    expect(wrapper.text()).toContain("Todavía no hay avisos publicados.");
  });

  it("emite 'accion' al presionar el botón de la invitación", async () => {
    const wrapper = mount(EmptyState, {
      props: { titulo: "Sin notas", descripcion: "Aún no hay notas.", etiquetaAccion: "Ver curso" },
    });
    await wrapper.find("button").trigger("click");
    expect(wrapper.emitted("accion")).toHaveLength(1);
  });
});
