import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import TagPill from "../TagPill.vue";

describe("TagPill", () => {
  it("aplica la clase de la variante indicada", () => {
    const wrapper = mount(TagPill, {
      props: { variante: "taller" },
      slots: { default: "Taller" },
    });
    expect(wrapper.classes()).toContain("tag-pill--taller");
    expect(wrapper.text()).toBe("Taller");
  });

  it("usa 'hoy' como variante por defecto", () => {
    const wrapper = mount(TagPill, { slots: { default: "Ahora" } });
    expect(wrapper.classes()).toContain("tag-pill--hoy");
  });
});
