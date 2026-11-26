// Tokens tomados del manual de imagen de la Bicicleteria 2 de Abril (v1.0).
// Si el manual cambia, este es el unico lugar que hay que tocar.

export const DARK = "#1C1C1C";
export const LIGHT = "#FCFCFC";

export const COLORS = {
  azul: { name: "Azul", accent: "#2F5D8C", on: "#FCFCFC" },
  cobre: { name: "Cobre", accent: "#C48D50", on: "#1C1C1C" },
};

export const FONT_DISPLAY = '"Racing Sans One","Arial Black",system-ui,sans-serif';
export const FONT_BODY = '"Inter",system-ui,-apple-system,"Segoe UI",sans-serif';

// Cada plantilla define su "modo" de composicion y como resuelve
// sus colores de fondo/texto/pill/precio a partir del color elegido.
export const TEMPLATES = {
  oferta: {
    name: "Oferta",
    label: "Oferta",
    mode: "framed",
    colorsFor: (s) => ({ bg: s.accent, fg: s.on, lb: DARK, lf: LIGHT, pb: DARK, pf: LIGHT }),
  },
  nueva: {
    name: "Recién llegada",
    label: "Recién llegada",
    mode: "bleed",
    colorsFor: (s) => ({ bg: DARK, fg: LIGHT, lb: s.accent, lf: s.on, pb: s.accent, pf: s.on }),
  },
  // Foto impresa (polaroid) inclinada y el precio en un sticker redondo.
  usada: {
    name: "Usada en venta",
    label: "Usada en venta",
    mode: "polaroid",
    colorsFor: (s) => ({ bg: s.accent, fg: s.on, lb: DARK, lf: LIGHT, pb: DARK, pf: LIGHT }),
  },
  // Palabra TALLER gigante y la foto entre dos cintas a rayas.
  taller: {
    name: "Taller",
    label: "Servicio de taller",
    palabra: "Taller",
    mode: "banda",
    colorsFor: (s) => ({ bg: DARK, fg: LIGHT, lb: s.accent, lf: s.on, pb: s.accent, pf: s.on, franja: [s.accent, LIGHT] }),
  },
  aviso: {
    name: "Aviso",
    label: "Aviso",
    mode: "backdrop",
    colorsFor: (s) => ({ bg: DARK, fg: LIGHT, lb: s.accent, lf: s.on, pb: s.accent, pf: s.on }),
  },
  // Las que siguen son solo para historias (soloHistoria).
  dos_fotos: {
    name: "Dos fotos",
    label: "Novedades",
    mode: "duo",
    fotos: 2,
    soloHistoria: true,
    colorsFor: (s) => ({ bg: DARK, fg: LIGHT, lb: s.accent, lf: s.on, pb: s.accent, pf: s.on }),
  },
  cuatro_fotos: {
    name: "Cuatro fotos",
    label: "Novedades",
    mode: "grid",
    fotos: 4,
    soloHistoria: true,
    colorsFor: (s) => ({ bg: LIGHT, fg: DARK, lb: DARK, lf: LIGHT, pb: s.accent, pf: s.on }),
  },
  foto: {
    name: "Solo la foto",
    label: "",
    mode: "raw",
    soloHistoria: true,
    sinTexto: true,
    colorsFor: () => ({ bg: DARK, fg: LIGHT }),
  },
};

// Cuantas fotos lleva una plantilla (las de siempre llevan una).
export function fotosDe(tipo) {
  return TEMPLATES[tipo]?.fotos || 1;
}

export const MAX_FOTOS = 4;

export const STORY_WIDTH = 1080;
export const STORY_HEIGHT = 1920;

// Medidas de cada formato de Instagram. El feed usa 4:5, que es el que más
// ocupa la pantalla del celular sin que Instagram lo recorte.
export const FORMATOS = {
  historia: { nombre: "Historia", ancho: STORY_WIDTH, alto: STORY_HEIGHT, proporcion: "9:16" },
  feed: { nombre: "Publicación del feed", ancho: 1080, alto: 1350, proporcion: "4:5" },
};

// Un lugar de foto sin cargar: zoom 1 y centrada.
export const FOTO_VACIA = { img: null, zoom: 1, ox: 0, oy: 0 };
