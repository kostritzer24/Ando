import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import AppButton from "../AppButton.vue";

describe("AppButton", () => {
  it("muestra el texto que recibe en el slot", () => {
    const wrapper = mount(AppButton, { slots: { default: "Guardar" } });
    expect(wrapper.text()).toBe("Guardar");
  });

  it("emite click al presionarlo", async () => {
    const wrapper = mount(AppButton, { slots: { default: "Guardar" } });
    await wrapper.trigger("click");
    expect(wrapper.emitted("click")).toHaveLength(1);
  });

  it("no emite click cuando está deshabilitado", async () => {
    const wrapper = mount(AppButton, {
      props: { deshabilitado: true },
      slots: { default: "Guardar" },
    });
    await wrapper.trigger("click");
    expect(wrapper.emitted("click")).toBeUndefined();
  });

  it("usa la variante secundaria cuando se indica", () => {
    const wrapper = mount(AppButton, {
      props: { variante: "secundario" },
      slots: { default: "Cancelar" },
    });
    expect(wrapper.classes()).toContain("app-button--secundario");
  });
});
