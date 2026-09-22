import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import AppModal from "../AppModal.vue";

describe("AppModal", () => {
  it("muestra el título y el contenido del slot", () => {
    const wrapper = mount(AppModal, {
      props: { titulo: "Agregar curso" },
      slots: { default: "<p>Contenido del formulario</p>" },
    });
    expect(wrapper.text()).toContain("Agregar curso");
    expect(wrapper.text()).toContain("Contenido del formulario");
  });

  it("emite cerrar al hacer clic en el botón de cerrar", async () => {
    const wrapper = mount(AppModal, { props: { titulo: "Agregar curso" } });
    await wrapper.find(".app-modal__cerrar").trigger("click");
    expect(wrapper.emitted("cerrar")).toHaveLength(1);
  });

  it("emite cerrar al hacer clic en el fondo, pero no al hacer clic dentro del diálogo", async () => {
    const wrapper = mount(AppModal, {
      props: { titulo: "Agregar curso" },
      slots: { default: "<p>Contenido</p>" },
    });
    await wrapper.find(".app-modal").trigger("click");
    expect(wrapper.emitted("cerrar")).toBeUndefined();

    await wrapper.find(".app-modal__fondo").trigger("click");
    expect(wrapper.emitted("cerrar")).toHaveLength(1);
  });
});
