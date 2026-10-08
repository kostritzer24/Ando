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
    expect(textos).toEqual(["Elige una opción", "Académico", "Taller"]);
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
      props: { id: "tipo", etiqueta: "Tipo", modelValue: "", opciones, mensajeError: "Elige un tipo" },
    });
    expect(wrapper.text()).toContain("Elige un tipo");
    expect(wrapper.find("select").attributes("aria-invalid")).toBe("true");
  });
});

describe("FormSelect con opción vacía propia", () => {
  it("no agrega el marcador cuando una opción real ya usa el valor vacío", () => {
    const wrapper = mount(FormSelect, {
      props: {
        id: "rol",
        etiqueta: "Rol",
        modelValue: "",
        opciones: [
          { valor: "", etiqueta: "Todos los roles" },
          { valor: "a", etiqueta: "Docente" },
        ],
      },
    });
    const opciones = wrapper.findAll("option").map((o) => o.text());
    expect(opciones).toEqual(["Todos los roles", "Docente"]);
  });
});
