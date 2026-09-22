export type TipoCampo = "texto" | "textarea" | "booleano" | "select";

export interface CampoConfig {
  clave: string;
  etiqueta: string;
  tipo: TipoCampo;
  opciones?: { valor: string; etiqueta: string }[];
  pista?: string;
}

export interface CatalogoConfig {
  titulo: string;
  tituloSingular: string;
  campos: CampoConfig[];
  columnas: { clave: string; etiqueta: string }[];
}

export const CONFIG_CURSOS: CatalogoConfig = {
  titulo: "Cursos",
  tituloSingular: "curso",
  campos: [
    { clave: "name", etiqueta: "Nombre", tipo: "texto" },
    {
      clave: "type",
      etiqueta: "Tipo",
      tipo: "select",
      opciones: [
        { valor: "academico", etiqueta: "Académico" },
        { valor: "taller", etiqueta: "Taller" },
      ],
    },
  ],
  columnas: [
    { clave: "name", etiqueta: "Nombre" },
    { clave: "type", etiqueta: "Tipo" },
  ],
};

export const CONFIG_TIPOS_ACTIVIDAD: CatalogoConfig = {
  titulo: "Tipos de actividad evaluativa",
  tituloSingular: "tipo de actividad",
  campos: [
    { clave: "name", etiqueta: "Nombre", tipo: "texto" },
    {
      clave: "counts_as_short_quiz",
      etiqueta: "Cuenta como prueba corta",
      tipo: "booleano",
      pista: "RN-04: se usa para exigir el mínimo de 4 pruebas cortas por unidad.",
    },
  ],
  columnas: [{ clave: "name", etiqueta: "Nombre" }],
};

export const CONFIG_TIPOS_JUSTIFICACION: CatalogoConfig = {
  titulo: "Tipos de justificación",
  tituloSingular: "tipo de justificación",
  campos: [
    { clave: "name", etiqueta: "Nombre", tipo: "texto" },
    { clave: "requires_document", etiqueta: "Requiere documento de respaldo", tipo: "booleano" },
  ],
  columnas: [{ clave: "name", etiqueta: "Nombre" }],
};

export const CONFIG_TIPOS_DOCUMENTO: CatalogoConfig = {
  titulo: "Tipos de documento",
  tituloSingular: "tipo de documento",
  campos: [
    { clave: "name", etiqueta: "Nombre", tipo: "texto" },
    {
      clave: "template_key",
      etiqueta: "Plantilla técnica",
      tipo: "texto",
      pista:
        "Tiene que coincidir exactamente con una plantilla ya programada en el sistema " +
        "(constancia_solvencia, constancia_estudio, constancia_conducta o carta_membretada). " +
        "Un valor distinto rompe la emisión de ese documento.",
    },
  ],
  columnas: [
    { clave: "name", etiqueta: "Nombre" },
    { clave: "template_key", etiqueta: "Plantilla técnica" },
  ],
};

export const CONFIG_BECAS: CatalogoConfig = {
  titulo: "Becas",
  tituloSingular: "beca",
  campos: [
    { clave: "name", etiqueta: "Nombre", tipo: "texto" },
    { clave: "description", etiqueta: "Descripción", tipo: "textarea" },
  ],
  columnas: [
    { clave: "name", etiqueta: "Nombre" },
    { clave: "description", etiqueta: "Descripción" },
  ],
};

export const CONFIG_ARTICULOS_CONVIVENCIA: CatalogoConfig = {
  titulo: "Artículos del código de convivencia",
  tituloSingular: "artículo",
  campos: [
    { clave: "chapter", etiqueta: "Capítulo", tipo: "texto" },
    { clave: "code", etiqueta: "Código", tipo: "texto" },
    { clave: "description", etiqueta: "Descripción", tipo: "textarea" },
  ],
  columnas: [
    { clave: "chapter", etiqueta: "Capítulo" },
    { clave: "code", etiqueta: "Código" },
    { clave: "description", etiqueta: "Descripción" },
  ],
};
