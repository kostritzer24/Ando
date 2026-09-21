import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import DayTabs from "../DayTabs.vue";

const dias = [
  { valor: "lun", etiqueta: "lun 15" },
  { valor: "mar", etiqueta: "mar 16" },
];

describe("DayTabs", () => {
  it("marca como activo el día que coincide con modelValue", () => {
    const wrapper = mount(DayTabs, { props: { dias, modelValue: "mar" } });
    const botones = wrapper.findAll("button");
    expect(botones[1].classes()).toContain("day-tabs__boton--activo");
    expect(botones[1].attributes("aria-current")).toBe("true");
  });

  it("emite update:modelValue con el valor del día presionado", async () => {
    const wrapper = mount(DayTabs, { props: { dias, modelValue: "lun" } });
    await wrapper.findAll("button")[1].trigger("click");
    expect(wrapper.emitted("update:modelValue")?.[0]).toEqual(["mar"]);
  });
});
