import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import FormBuscador from "../FormBuscador.vue";

const opciones = [
  { valor: "1", etiqueta: "María Ximena Pérez" },
  { valor: "2", etiqueta: "Juan Carlos López" },
  { valor: "3", etiqueta: "Pedro Ajú" },
];

function montar(modelValue = "") {
  return mount(FormBuscador, {
    props: { id: "persona", etiqueta: "Persona", modelValue, opciones },
  });
}

describe("FormBuscador", () => {
  it("asocia la etiqueta con el campo", () => {
    const wrapper = montar();
    expect(wrapper.find("label").attributes("for")).toBe("persona");
    expect(wrapper.find("input").attributes("id")).toBe("persona");
  });

  it("acota la lista al escribir, sin importar tildes ni mayúsculas", async () => {
    const wrapper = montar();
    await wrapper.find("input").trigger("focus");
    await wrapper.find("input").setValue("maria");
    expect(wrapper.findAll("[role=option]").map((o) => o.text())).toEqual(["María Ximena Pérez"]);
  });

  it("emite el valor de la opción elegida", async () => {
    const wrapper = montar();
    await wrapper.find("input").trigger("focus");
    await wrapper.findAll("[role=option]")[1].trigger("mousedown");
    expect(wrapper.emitted("update:modelValue")?.[0]).toEqual(["2"]);
  });

  it("se elige con el teclado: flecha abajo y Enter", async () => {
    const wrapper = montar();
    await wrapper.find("input").trigger("focus");
    await wrapper.find("input").trigger("keydown", { key: "ArrowDown" });
    await wrapper.find("input").trigger("keydown", { key: "Enter" });
    expect(wrapper.emitted("update:modelValue")?.[0]).toEqual(["2"]);
  });

  it("avisa cuando no hay coincidencias", async () => {
    const wrapper = montar();
    await wrapper.find("input").trigger("focus");
    await wrapper.find("input").setValue("zzz");
    expect(wrapper.text()).toContain("Sin coincidencias");
  });

  it("muestra la opción elegida como texto del campo", () => {
    const wrapper = montar("3");
    expect((wrapper.find("input").element as HTMLInputElement).value).toBe("Pedro Ajú");
  });
});
