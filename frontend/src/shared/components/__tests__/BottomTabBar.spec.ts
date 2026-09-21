import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import BottomTabBar from "../BottomTabBar.vue";

const items = [
  { valor: "inicio", etiqueta: "Inicio" },
  { valor: "notas", etiqueta: "Notas" },
];

describe("BottomTabBar", () => {
  it("marca como página actual el item activo", () => {
    const wrapper = mount(BottomTabBar, { props: { items, modelValue: "notas" } });
    const botones = wrapper.findAll("button");
    expect(botones[1].attributes("aria-current")).toBe("page");
    expect(botones[0].attributes("aria-current")).toBeUndefined();
  });

  it("emite update:modelValue al elegir otra pestaña", async () => {
    const wrapper = mount(BottomTabBar, { props: { items, modelValue: "inicio" } });
    await wrapper.findAll("button")[1].trigger("click");
    expect(wrapper.emitted("update:modelValue")?.[0]).toEqual(["notas"]);
  });
});
