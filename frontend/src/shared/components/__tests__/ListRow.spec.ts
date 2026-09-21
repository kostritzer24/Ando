import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ListRow from "../ListRow.vue";

describe("ListRow", () => {
  it("muestra el contenido de cada slot", () => {
    const wrapper = mount(ListRow, {
      slots: {
        tiempo: "8:00",
        default: "Matemática",
        final: "Ahora",
      },
    });
    expect(wrapper.text()).toContain("8:00");
    expect(wrapper.text()).toContain("Matemática");
    expect(wrapper.text()).toContain("Ahora");
  });

  it("quita la línea inferior cuando sinLinea es verdadero", () => {
    const wrapper = mount(ListRow, { props: { sinLinea: true } });
    expect(wrapper.classes()).toContain("list-row--sin-linea");
  });
});
