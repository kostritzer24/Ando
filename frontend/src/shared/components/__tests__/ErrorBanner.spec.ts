import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ErrorBanner from "../ErrorBanner.vue";

describe("ErrorBanner", () => {
  it("muestra el mensaje recibido", () => {
    const wrapper = mount(ErrorBanner, { props: { mensaje: "No se pudo guardar la asistencia." } });
    expect(wrapper.text()).toContain("No se pudo guardar la asistencia.");
    expect(wrapper.attributes("role")).toBe("alert");
  });

  it("no muestra el botón de acción si no se pasa la etiqueta", () => {
    const wrapper = mount(ErrorBanner, { props: { mensaje: "Error" } });
    expect(wrapper.find("button").exists()).toBe(false);
  });

  it("emite 'accion' al presionar el botón", async () => {
    const wrapper = mount(ErrorBanner, {
      props: { mensaje: "Error", etiquetaAccion: "Reintentar" },
    });
    await wrapper.find("button").trigger("click");
    expect(wrapper.emitted("accion")).toHaveLength(1);
  });
});
