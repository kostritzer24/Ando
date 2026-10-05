/**
 * Código de Conducta y Convivencia Escolar 2026 — texto institucional
 * transcrito sin cambios del documento oficial del centro
 * (formatos_institucionales/Manual de convivencia.docx). Si Dirección
 * actualiza el manual, se actualiza este archivo; el resto de la pantalla
 * no cambia.
 */

export interface ArticuloConvivencia {
  numero: number;
  titulo: string;
  /** Texto corrido, en el orden del documento. */
  parrafos: string[];
  /** Viñetas que acompañan al texto. */
  items: string[];
}

export interface CapituloConvivencia {
  titulo: string;
  articulos: ArticuloConvivencia[];
}

export interface ManualConvivencia {
  titulo: string;
  institucion: string;
  introduccion: string[];
  principios: { titulo: string; texto: string }[];
  capitulos: CapituloConvivencia[];
  cierre: string[];
}

export const manualConvivencia: ManualConvivencia =  {
  "titulo": "CÓDIGO DE CONDUCTA Y CONVIVENCIA ESCOLAR 2026",
  "institucion": "Centro de Oportunidades",
  "introduccion": [
    "Este Código establece los principios y normas que rigen la convivencia en nuestra comunidad educativa. Tiene como propósito fundamental crear y mantener un ambiente seguro, respetuoso, inclusivo y propicio para el aprendizaje y el desarrollo integral de todos los estudiantes, desde 1° Básico hasta 5° Bachillerato. Su cumplimiento es un compromiso compartido entre estudiantes, familias, educadores y personal administrativo."
  ],
  "principios": [
    {
      "titulo": "Respeto y Dignidad",
      "texto": "Trato a cada miembro de la comunidad con dignidad, consideración y empatía."
    },
    {
      "titulo": "Responsabilidad",
      "texto": "Asumo las consecuencias de mis actos y cumplo con mis deberes académicos y comunitarios."
    },
    {
      "titulo": "Integridad",
      "texto": "Actúo con honestidad en todas mis acciones y en mi trabajo académico."
    },
    {
      "titulo": "Inclusión",
      "texto": "Valoro y respeto la diversidad, rechazando toda forma de discriminación."
    },
    {
      "titulo": "Cuidado",
      "texto": "Protejo mi salud, mi seguridad y los bienes comunes de la institución."
    }
  ],
  "capitulos": [
    {
      "titulo": "CAPÍTULO I: RESPETO Y DIGNIDAD EN LA CONVIVENCIA",
      "articulos": [
        {
          "numero": 1,
          "titulo": "Respeto a las Personas y sus Pertenecías",
          "parrafos": [
            "Respeto, cuido y no tomo las pertenencias de otros miembros de la comunidad escolar sin su autorización expresa."
          ],
          "items": []
        },
        {
          "numero": 2,
          "titulo": "Inclusión y No Discriminación",
          "parrafos": [
            "Empatizo con personas de diferente etnia, género, identidad de género, orientación sexual, situación económica, religión, discapacidad, apariencia física o nacionalidad. Me comprometo a:"
          ],
          "items": [
            "No realizar ningún acto de discriminación, hostigamiento, burla o exclusión.",
            "Abstenerme de utilizar lenguaje, gestos, símbolos o iconografía asociados a grupos que promuevan el odio, la violencia o la discriminación.",
            "No participar en la creación o difusión de mensajes (escritos, audiovisuales o digitales) que atenten contra la dignidad de cualquier persona o grupo.",
            "Fomentar un ambiente de respeto mutuo en todas las actividades, incluidas las deportivas y culturales."
          ]
        },
        {
          "numero": 3,
          "titulo": "Demostraciones de Afecto y Espacio Personal",
          "parrafos": [
            "La escuela es un espacio de aprendizaje y convivencia respetuosa.",
            "Las demostraciones de afecto deben ser moderadas, discretas y apropiadas para el entorno educativo.",
            "Se consideran aceptables los saludos breves como abrazos o besos en la mejilla, siempre que ambas partes estén de acuerdo.",
            "Se prohíbe el contacto físico íntimo o excesivo (besos en la boca, caricias inapropiadas) dentro de las instalaciones y horarios escolares.",
            "Respeto los límites y el espacio personal de mis compañeros y de todo el personal."
          ],
          "items": []
        },
        {
          "numero": 4,
          "titulo": "Relación Respetuosa con los Educadores",
          "parrafos": [
            "Mi compromiso con el respeto hacia los educadores incluye:"
          ],
          "items": [
            "Evitar interrupciones durante las clases y no retirarme del salón sin autorización.",
            "Respetar el tiempo y esfuerzo invertido en las lecciones y actividades.",
            "Mantener un tono de voz adecuado y un trato cortés en todo momento.",
            "Abstenerme de realizar comentarios despectivos o burlas, contribuyendo a un ambiente de aprendizaje colaborativo."
          ]
        }
      ]
    },
    {
      "titulo": "CAPÍTULO II: SEGURIDAD, SALUD E INTEGRIDAD FÍSICA",
      "articulos": [
        {
          "numero": 5,
          "titulo": "Prohibición de Sustancias y Objetos Peligrosos",
          "parrafos": [
            "Para cuidar mi salud y la de los demás, así como la seguridad de la comunidad, me comprometo a no ingresar, portar, consumir o distribuir:"
          ],
          "items": [
            "Bebidas alcohólicas, tabaco, vapes o cualquier tipo de droga (lícitas o ilícitas).",
            "Armas de cualquier tipo (reales, de imitación o réplicas).",
            "Objetos punzocortantes o cualquier instrumento que pueda ser utilizado como arma o que represente un peligro."
          ]
        },
        {
          "numero": 6,
          "titulo": "Contenido Sensible e Inapropiado",
          "parrafos": [
            "Me abstengo de ver, mostrar, compartir o acceder a cualquier contenido considerado sensible dentro de las instalaciones escolares o en actividades oficiales. Esto incluye, pero no se limita a:"
          ],
          "items": [
            "Material pornográfico o de naturaleza sexual explícita.",
            "Contenido violento, gráfico (gore) o que represente daño físico/emocional.",
            "Cualquier material que promueva el odio, la discriminación, la violencia o el acoso."
          ]
        }
      ]
    },
    {
      "titulo": "CAPÍTULO III: USO ADECUADO DE LA TECNOLOGÍA",
      "articulos": [
        {
          "numero": 7,
          "titulo": "Uso de Dispositivos Electrónicos",
          "parrafos": [
            "El uso de teléfonos celulares, tabletas, audífonos y dispositivos de audio/entretenimiento está prohibido dentro de los salones de clase y áreas de estudio.",
            "Solo podrán usarse en los espacios y horarios expresamente autorizados por la dirección (ej., durante el receso, en zonas designadas).",
            "El incumplimiento de esta norma puede derivar en la retención del dispositivo, el cual será devuelto únicamente al padre, madre o encargado legal."
          ],
          "items": []
        },
        {
          "numero": 8,
          "titulo": "Responsabilidad Digital y Ciberconvivencia",
          "parrafos": [
            "Hago un uso ético y responsable de la tecnología:"
          ],
          "items": [
            "No tomo fotos, grabo videos, creo stickers o memes de compañeros, educadores o personal sin su consentimiento expreso.",
            "Asumo plena responsabilidad por el contenido que publico en redes sociales respecto a la comunidad escolar.",
            "Evito participar en, promover o difundir cualquier forma de ciberacoso, difamación, hostigamiento o suplantación de identidad."
          ]
        }
      ]
    },
    {
      "titulo": "CAPÍTULO IV: RESPONSABILIDAD ACADÉMICA Y ASISTENCIA",
      "articulos": [
        {
          "numero": 9,
          "titulo": "Puntualidad y Asistencia",
          "parrafos": [
            "Soy puntual en la llegada a la escuela, a cada clase y en la entrega de trabajos y asignaciones.",
            "Asisto a clase regularmente. Las inasistencias deben ser justificadas por el encargado según el procedimiento oficial establecido."
          ],
          "items": []
        },
        {
          "numero": 10,
          "titulo": "Honestidad Académica",
          "parrafos": [
            "Cumplo con mis tareas, proyectos y estudios en los plazos asignados, desarrollando una ética de trabajo responsable.",
            "Practico la honestidad académica. No copio en exámenes, ni plagio trabajos (utilizo la información de otras fuentes dando siempre el crédito correspondiente)."
          ],
          "items": []
        },
        {
          "numero": 11,
          "titulo": "Uso Adecuado del Tiempo de Clase",
          "parrafos": [
            "Limito mis visitas al baño durante la clase, utilizando los periodos de receso para este fin.",
            "Solo solicito salir por emergencia real y con la autorización del educador, informando de manera discreta."
          ],
          "items": []
        }
      ]
    },
    {
      "titulo": "CAPÍTULO V: CUIDADO DEL ENTORNO Y BIENES COMUNES",
      "articulos": [
        {
          "numero": 12,
          "titulo": "Responsabilidad sobre el Mobiliario e Instalaciones",
          "parrafos": [
            "Soy responsable en el uso y cuidado del mobiliario, equipo tecnológico, material didáctico e instalaciones de la escuela (aulas, baños, canchas, biblioteca, etc.).",
            "Informo de inmediato a un docente o autoridad si encuentro algún daño o desperfecto."
          ],
          "items": []
        },
        {
          "numero": 13,
          "titulo": "Compromiso con la Limpieza e Higiene",
          "parrafos": [
            "Mantengo limpio y ordenado mi espacio de trabajo personal (escritorio, área de laboratorio, taller).",
            "Deposito la basura y los materiales reciclables en los contenedores correspondientes.",
            "Cuido los baños y áreas comunes, dejándolos en las condiciones en que me gustaría encontrarlos."
          ],
          "items": []
        },
        {
          "numero": 14,
          "titulo": "Convivencia en Espacios Comunes",
          "parrafos": [
            "Me desplazo por pasillos y escaleras de manera ordenada y tranquila, respetando el silencio de las aulas en sesión.",
            "Durante los recreos o actividades libres, utilizo los espacios designados (canchas, patios, biblioteca) de forma segura, respetuosa y siguiendo las indicaciones del personal supervisor."
          ],
          "items": []
        }
      ]
    },
    {
      "titulo": "CAPÍTULO VI: SANCIONES Y PROCEDIMIENTOS",
      "articulos": [
        {
          "numero": 15,
          "titulo": "Aplicación de Medidas Formativas y Sanciones",
          "parrafos": [
            "El incumplimiento de las normas establecidas en este Código conlleva consecuencias, las cuales tienen un carácter formativo y son proporcionales a la gravedad de la falta.",
            "Faltas Leves: (Ej.: falta de aseo en el puesto, interrupciones menores en clase). Consecuencia: Llamado de atención verbal, amonestación escrita, tarea reparadora.",
            "Faltas Graves: (Ej.: falta de respeto reiterada, uso de celular en clase, daño menor a propiedad ajena). Consecuencia: Reporte oficial, comunicación a la familia, suspensión temporal de actividades extracurriculares, servicio comunitario.",
            "Faltas Muy Graves: (Ej.: agresión física o verbal grave, acoso, discriminación, posesión de sustancias/armas prohibidas, vandalismo, ciberacoso, suplantación de identidad). Consecuencia: Suspensión inmediata, citación a consejo de convivencia con la familia, evaluación de expulsión."
          ],
          "items": []
        },
        {
          "numero": 16,
          "titulo": "Procedimiento para la Aplicación de Sanciones",
          "parrafos": [
            "Toda sanción será aplicada siguiendo un debido proceso, que incluye:"
          ],
          "items": [
            "Investigación objetiva de los hechos.",
            "Derecho del estudiante a ser escuchado y a presentar su descargo.",
            "Análisis del caso por un comité integrado por el maestro guía, un miembro del equipo directivo y, de ser necesario, el departamento de orientación.",
            "Comunicación formal y clara de la decisión y sus razones al estudiante y a su familia.",
            "Establecimiento de compromisos y medidas de reparación cuando sea posible."
          ]
        }
      ]
    }
  ],
  "cierre": [
    "Este Código de Convivencia es un documento vivo que podrá ser revisado y actualizado con la participación de la comunidad educativa para responder a sus necesidades en la búsqueda constante de una convivencia escolar positiva.",
    "Centro de Oportunidades, 2026."
  ]
};
