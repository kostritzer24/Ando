import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import FormField from "../FormField.vue";

describe("FormField", () => {
  it("asocia la etiqueta real con el input por id", () => {
    const wrapper = mount(FormField, {
      props: { id: "usuario", etiqueta: "Usuario", modelValue: "" },
    });
    expect(wrapper.find("label").attributes("for")).toBe("usuario");
    expect(wrapper.find("input").attributes("id")).toBe("usuario");
  });

  it("emite update:modelValue al escribir", async () => {
    const wrapper = mount(FormField, {
      props: { id: "usuario", etiqueta: "Usuario", modelValue: "" },
    });
    await wrapper.find("input").setValue("dir.demo");
    expect(wrapper.emitted("update:modelValue")?.[0]).toEqual(["dir.demo"]);
  });

  it("pasa atributos como autocomplete al input, no al contenedor", () => {
    const wrapper = mount(FormField, {
      props: { id: "usuario", etiqueta: "Usuario", modelValue: "" },
      attrs: { autocomplete: "username" },
    });
    expect(wrapper.find("input").attributes("autocomplete")).toBe("username");
  });

  it("muestra el mensaje de error cuando se indica", () => {
    const wrapper = mount(FormField, {
      props: { id: "usuario", etiqueta: "Usuario", modelValue: "", mensajeError: "Campo obligatorio" },
    });
    expect(wrapper.text()).toContain("Campo obligatorio");
    expect(wrapper.find("input").attributes("aria-invalid")).toBe("true");
  });
});
