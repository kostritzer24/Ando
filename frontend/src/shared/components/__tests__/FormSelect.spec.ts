import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import FormSelect from "../FormSelect.vue";

const opciones = [
  { valor: "academico", etiqueta: "Académico" },
  { valor: "taller", etiqueta: "Taller" },
];

describe("FormSelect", () => {
  it("asocia la etiqueta real con el select por id", () => {
    const wrapper = mount(FormSelect, {
      props: { id: "tipo", etiqueta: "Tipo", modelValue: "", opciones },
    });
    expect(wrapper.find("label").attributes("for")).toBe("tipo");
    expect(wrapper.find("select").attributes("id")).toBe("tipo");
  });

  it("dibuja una opción por cada valor de la lista", () => {
    const wrapper = mount(FormSelect, {
      props: { id: "tipo", etiqueta: "Tipo", modelValue: "", opciones },
    });
    const textos = wrapper.findAll("option").map((opcion) => opcion.text());
    expect(textos).toEqual(["Elegí una opción", "Académico", "Taller"]);
  });

  it("emite update:modelValue al elegir una opción", async () => {
    const wrapper = mount(FormSelect, {
      props: { id: "tipo", etiqueta: "Tipo", modelValue: "", opciones },
    });
    await wrapper.find("select").setValue("taller");
    expect(wrapper.emitted("update:modelValue")?.[0]).toEqual(["taller"]);
  });

  it("muestra el mensaje de error cuando se indica", () => {
    const wrapper = mount(FormSelect, {
      props: { id: "tipo", etiqueta: "Tipo", modelValue: "", opciones, mensajeError: "Elegí un tipo" },
    });
    expect(wrapper.text()).toContain("Elegí un tipo");
    expect(wrapper.find("select").attributes("aria-invalid")).toBe("true");
  });
});
