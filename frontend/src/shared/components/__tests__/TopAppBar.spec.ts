import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import TopAppBar from "../TopAppBar.vue";

describe("TopAppBar", () => {
  it("muestra el nombre del estudiante y su sección", () => {
    const wrapper = mount(TopAppBar, {
      props: { nombreEstudiante: "María Ximena Pérez Tzul", nombreSeccion: "Segundo básico A" },
    });
    expect(wrapper.text()).toContain("María Ximena Pérez Tzul");
    expect(wrapper.text()).toContain("Segundo básico A");
  });

  it("emite 'cambiar-estudiante' al presionar el botón", async () => {
    const wrapper = mount(TopAppBar, {
      props: { nombreEstudiante: "María", nombreSeccion: "Segundo básico A" },
    });
    await wrapper.find("button").trigger("click");
    expect(wrapper.emitted("cambiar-estudiante")).toHaveLength(1);
  });
});
