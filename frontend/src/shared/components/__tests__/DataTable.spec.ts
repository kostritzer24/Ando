import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import DataTable from "../DataTable.vue";

describe("DataTable", () => {
  const columnas = [
    { clave: "nombre", etiqueta: "Nombre" },
    { clave: "tipo", etiqueta: "Tipo" },
  ];
  const filas = [
    { nombre: "Matemática", tipo: "Académico" },
    { nombre: "Panadería", tipo: "Taller" },
  ];

  it("dibuja el encabezado con las etiquetas de columna", () => {
    const wrapper = mount(DataTable, { props: { columnas, filas: [] } });
    const encabezados = wrapper.findAll("th").map((th) => th.text());
    expect(encabezados).toEqual(["Nombre", "Tipo"]);
  });

  it("dibuja una fila por registro, con sus valores en orden de columna", () => {
    const wrapper = mount(DataTable, { props: { columnas, filas } });
    const filasHtml = wrapper.findAll("tbody tr");
    expect(filasHtml).toHaveLength(2);
    expect(filasHtml[0].text()).toContain("Matemática");
    expect(filasHtml[1].text()).toContain("Taller");
  });

  it("no agrega la columna de acciones si nadie pasa ese slot", () => {
    const wrapper = mount(DataTable, { props: { columnas, filas } });
    expect(wrapper.text()).not.toContain("Acciones");
  });

  it("usa el slot con nombre de una columna para personalizar su celda", () => {
    const wrapper = mount(DataTable, {
      props: { columnas, filas },
      slots: { "celda-tipo": `<template #celda-tipo="{ fila }">[{{ fila.tipo }}]</template>` },
    });
    expect(wrapper.text()).toContain("[Académico]");
  });
});
