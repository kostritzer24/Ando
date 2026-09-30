import { mount, RouterLinkStub } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import PageHeader from "../PageHeader.vue";

describe("PageHeader", () => {
  it("dibuja el título como h1 y la descripción", () => {
    const wrapper = mount(PageHeader, {
      props: { titulo: "Estudiantes", descripcion: "Inscritos en el ciclo 2026" },
    });
    expect(wrapper.find("h1").text()).toBe("Estudiantes");
    expect(wrapper.text()).toContain("Inscritos en el ciclo 2026");
  });

  it("muestra las acciones y el enlace para volver solo cuando se pasan", () => {
    const sinExtras = mount(PageHeader, { props: { titulo: "Estudiantes" } });
    expect(sinExtras.find(".page-header__acciones").exists()).toBe(false);
    expect(sinExtras.find(".page-header__volver").exists()).toBe(false);

    const conExtras = mount(PageHeader, {
      props: { titulo: "María", volverA: "/administrativo/estudiantes", etiquetaVolver: "Estudiantes" },
      slots: { acciones: "<button>Guardar</button>" },
      global: { stubs: { RouterLink: RouterLinkStub } },
    });
    expect(conExtras.findComponent(RouterLinkStub).props("to")).toBe("/administrativo/estudiantes");
    expect(conExtras.find(".page-header__acciones").text()).toBe("Guardar");
  });
});

describe("PageHeader — acciones condicionales", () => {
  it("no deja el contenedor de acciones cuando el slot llega vacío (botón con v-if falso)", () => {
    const wrapper = mount(PageHeader, {
      props: { titulo: "Secciones" },
      slots: { acciones: '<button v-if="false">Agregar</button>' },
    });
    expect(wrapper.find(".page-header__acciones").exists()).toBe(false);
  });
});
