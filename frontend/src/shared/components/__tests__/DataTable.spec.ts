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

describe("DataTable — búsqueda, orden y paginación", () => {
  const columnas = [
    { clave: "nombre", etiqueta: "Nombre" },
    { clave: "codigo", etiqueta: "Código" },
  ];
  const filas = Array.from({ length: 30 }, (_, i) => ({
    public_id: `id-${i}`,
    nombre: i === 7 ? "María Pérez" : `Estudiante ${i + 1}`,
    codigo: `ES${String(i + 1).padStart(3, "0")}`,
  }));

  it("busca sin distinguir mayúsculas ni tildes", async () => {
    const wrapper = mount(DataTable, { props: { columnas, filas, buscable: true } });
    await wrapper.find("input[type=search]").setValue("perez");
    const filasHtml = wrapper.findAll("tbody tr");
    expect(filasHtml).toHaveLength(1);
    expect(filasHtml[0].text()).toContain("María Pérez");
  });

  it("avisa cuando la búsqueda no encuentra nada", async () => {
    const wrapper = mount(DataTable, { props: { columnas, filas, buscable: true } });
    await wrapper.find("input[type=search]").setValue("zzz");
    expect(wrapper.text()).toContain("Nada coincide");
  });

  it("pagina en el cliente y muestra el rango", async () => {
    const wrapper = mount(DataTable, { props: { columnas, filas, porPagina: 25 } });
    expect(wrapper.findAll("tbody tr")).toHaveLength(25);
    expect(wrapper.text()).toContain("1–25 de 30");

    await wrapper.find('button[aria-label="Página siguiente"]').trigger("click");
    expect(wrapper.findAll("tbody tr")).toHaveLength(5);
    expect(wrapper.text()).toContain("26–30 de 30");
  });

  it("ordena al tocar el encabezado y lo anuncia con aria-sort", async () => {
    const wrapper = mount(DataTable, { props: { columnas, filas, porPagina: 0 } });
    const encabezadoCodigo = wrapper.findAll("th")[1];

    await encabezadoCodigo.find("button").trigger("click");
    await encabezadoCodigo.find("button").trigger("click");

    expect(encabezadoCodigo.attributes("aria-sort")).toBe("descending");
    expect(wrapper.find("tbody tr").text()).toContain("ES030");
  });
});

describe("DataTable — celdas vacías", () => {
  it("deja la celda sin contenido (el CSS la oculta en el teléfono)", () => {
    const wrapper = mount(DataTable, {
      props: { columnas: [{ clave: "nombre", etiqueta: "Nombre" }, { clave: "letra", etiqueta: "Letra" }], filas: [{ nombre: "Segundo básico", letra: "" }] },
    });
    expect(wrapper.findAll("td")[1].element.textContent).toBe("");
  });
});
