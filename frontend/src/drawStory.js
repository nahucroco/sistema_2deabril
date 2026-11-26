// Logica de dibujo de la historia (9:16) o del post del feed (4:5) en <canvas>.
// Mismas reglas visuales y mismos tokens de brand.js para los dos formatos:
// cambia solo donde va cada cosa (LAYOUTS) y un poco el tamaño del texto.

import { COLORS, FONT_BODY, FONT_DISPLAY, FORMATOS, TEMPLATES } from "./brand";

const ANCHO = 1080;

// Posiciones por formato y por modo de plantilla. En la historia todo arranca
// mas abajo porque Instagram tapa la parte de arriba con el nombre de la cuenta.
const LAYOUTS = {
  historia: {
    framed: {
      foto: [80, 340, 920, 560],
      logo: [50, 240, 200],
      pill: { x: 1020, y: 860, rot: -0.05 },
      texto: { y: 980, max: 100, min: 68, lineas: 2 },
    },
    bleed: {
      foto: [0, 0, ANCHO, 840],
      degrade: 420,
      logo: [70, 250, 200],
      pill: { x: 80, y: 798 },
      texto: { y: 940, max: 100, min: 68, lineas: 2 },
    },
    backdrop: {
      logo: [80, 250, 220],
      pill: { x: 80, y: 560 },
      texto: { y: 690, max: 124, min: 76, lineas: 4 },
    },
    // Foto impresa (polaroid) inclinada, con el precio en un sticker redondo.
    polaroid: {
      marco: [110, 380, 860, 780],
      foto: [140, 410, 800, 650],
      rot: -0.03,
      sticker: { x: 880, y: 1100, r: 150, rot: -0.12 },
      logo: [50, 225, 180],
      pill: { x: 1000, y: 290 },
      texto: { y: 1240, max: 92, min: 64, lineas: 2, detalleLineas: 1, sinPrecio: true },
    },
    // Palabra gigante arriba y la foto en una banda entre dos cintas a rayas.
    banda: {
      palabra: { x: 80, y: 270, max: 200, maxW: 780 },
      logo: [880, 240, 160],
      foto: [0, 540, ANCHO, 520],
      franja: 28,
      texto: { y: 1140, max: 84, min: 58, lineas: 2, k: 0.85, detalleLineas: 1 },
    },
    // Dos fotos verticales lado a lado.
    duo: {
      fotos: [
        [80, 330, 450, 620],
        [550, 330, 450, 620],
      ],
      logo: [50, 225, 180],
      pill: { x: 1020, y: 910, rot: -0.05 },
      texto: { y: 1030, max: 96, min: 64, lineas: 2, detalleLineas: 1 },
    },
    // Cuatro fotos en grilla de 2 x 2.
    grid: {
      fotos: [
        [80, 330, 450, 380],
        [550, 330, 450, 380],
        [80, 730, 450, 380],
        [550, 730, 450, 380],
      ],
      logo: [50, 225, 180],
      pill: { x: 1020, y: 1070, rot: -0.05 },
      texto: { y: 1180, max: 84, min: 58, lineas: 2, k: 0.85, detalleLineas: 1 },
    },
  },
  feed: {
    framed: {
      foto: [80, 190, 920, 540],
      logo: [40, 30, 150],
      pill: { x: 1020, y: 690, rot: -0.05 },
      texto: { y: 790, max: 84, min: 58, lineas: 2, k: 0.85, detalleLineas: 1 },
    },
    bleed: {
      foto: [0, 0, ANCHO, 690],
      degrade: 300,
      logo: [50, 40, 160],
      pill: { x: 80, y: 650 },
      texto: { y: 780, max: 84, min: 58, lineas: 2, k: 0.85, detalleLineas: 1 },
    },
    backdrop: {
      logo: [80, 70, 180],
      pill: { x: 80, y: 320 },
      texto: { y: 450, max: 110, min: 68, lineas: 4, k: 0.9, detalleLineas: 2 },
    },
    polaroid: {
      marco: [150, 160, 780, 690],
      foto: [175, 185, 730, 565],
      rot: -0.03,
      sticker: { x: 870, y: 790, r: 125, rot: -0.12 },
      logo: [40, 30, 140],
      pill: { x: 1040, y: 50 },
      texto: { y: 900, max: 80, min: 58, lineas: 2, k: 0.85, detalleLineas: 1, sinPrecio: true },
    },
    banda: {
      palabra: { x: 80, y: 40, max: 150, maxW: 800 },
      logo: [920, 30, 130],
      foto: [0, 230, ANCHO, 500],
      franja: 28,
      texto: { y: 800, max: 80, min: 58, lineas: 2, k: 0.85, detalleLineas: 1 },
    },
  },
};

function font(ctx, weight, size, display) {
  ctx.font = `${display ? 400 : weight} ${size}px ${display ? FONT_DISPLAY : FONT_BODY}`;
}

function wrap(ctx, text, maxW) {
  const words = text.trim().split(/\s+/).filter(Boolean);
  const lines = [];
  let cur = "";
  for (const w of words) {
    const t = cur ? `${cur} ${w}` : w;
    if (cur && ctx.measureText(t).width > maxW) {
      lines.push(cur);
      cur = w;
    } else {
      cur = t;
    }
  }
  if (cur) lines.push(cur);
  return lines;
}

function clampLines(ctx, lines, max, maxW) {
  if (lines.length <= max) return lines;
  const out = lines.slice(0, max);
  let last = out[max - 1];
  while (last.length > 1 && ctx.measureText(`${last}…`).width > maxW) last = last.slice(0, -1);
  out[max - 1] = `${last.trimEnd()}…`;
  return out;
}

function fmtPrice(v) {
  const s = (v || "").trim();
  if (!s) return "";
  const d = s.replace(/[.\s$]/g, "");
  return /^\d+$/.test(d) ? `$${Number(d).toLocaleString("es-AR")}` : s;
}

function cover(ctx, img, x, y, w, h, zoom, ox, oy) {
  zoom = Math.max(1, zoom); // alejar de mas dejaria bordes vacios
  const iw = img.naturalWidth || img.width;
  const ih = img.naturalHeight || img.height;
  const s = Math.max(w / iw, h / ih) * zoom;
  const dw = iw * s;
  const dh = ih * s;
  ctx.save();
  ctx.beginPath();
  ctx.rect(x, y, w, h);
  ctx.clip();
  ctx.drawImage(img, x + (w - dw) / 2 + (ox * (dw - w)) / 2, y + (h - dh) / 2 + (oy * (dh - h)) / 2, dw, dh);
  ctx.restore();
}

function pill(ctx, text, x, y, bg, fg, alignRight, k = 1) {
  font(ctx, 400, Math.round(50 * k), true);
  const t = text.toUpperCase();
  const w = ctx.measureText(t).width + 60 * k;
  const hh = Math.round(84 * k);
  const px = alignRight ? x - w : x;
  ctx.fillStyle = bg;
  ctx.fillRect(px, y, w, hh);
  ctx.fillStyle = fg;
  ctx.fillText(t, px + 30 * k, y + 20 * k);
  return hh;
}

function textBlock(ctx, state, y, c, opt) {
  const maxW = ANCHO - 160;
  const k = opt.k || 1;
  const px = (n) => Math.round(n * k);
  let fit = null;
  const title = (state.titulo || "").trim();
  if (title) {
    for (let size = opt.max; size >= opt.min; size -= 6) {
      font(ctx, 400, size, true);
      const lines = wrap(ctx, title, maxW);
      if (lines.length <= opt.lineas) {
        fit = { size, lines };
        break;
      }
    }
    if (!fit) {
      font(ctx, 400, opt.min, true);
      fit = { size: opt.min, lines: clampLines(ctx, wrap(ctx, title, maxW), opt.lineas + 1, maxW) };
    }
    font(ctx, 400, fit.size, true);
    ctx.fillStyle = c.fg;
    for (const line of fit.lines) {
      ctx.fillText(line, 80, y);
      y += Math.round(fit.size * 1.02);
    }
    y += px(22);
  }
  if ((state.detalle || "").trim()) {
    font(ctx, 500, px(42), false);
    ctx.fillStyle = c.fg;
    ctx.globalAlpha = 0.88;
    for (const line of clampLines(ctx, wrap(ctx, state.detalle.trim(), maxW), opt.detalleLineas || 2, maxW)) {
      ctx.fillText(line, 80, y);
      y += px(56);
    }
    ctx.globalAlpha = 1;
    y += px(28);
  }
  const price = opt.sinPrecio ? "" : fmtPrice(state.precio);
  if (price) {
    let ps = px(104);
    font(ctx, 400, ps, true);
    while (ps > px(60) && ctx.measureText(price).width > maxW - 72) {
      ps -= 6;
      font(ctx, 400, ps, true);
    }
    if (c.pb) {
      const w = ctx.measureText(price).width + px(72);
      ctx.fillStyle = c.pb;
      ctx.fillRect(80, y, w, ps + px(26));
      ctx.fillStyle = c.pf;
      ctx.fillText(price, 80 + px(36), y + px(14));
      y += ps + px(26);
    } else {
      ctx.fillStyle = c.pf;
      ctx.fillText(price, 80, y);
      y += ps;
    }
    y += px(40);
  }
  ctx.fillStyle = c.fg;
  ctx.fillRect(80, y, 120, 6);
  y += px(26);
  font(ctx, 600, px(40), false);
  const wa = (state.whatsapp || "").trim();
  ctx.fillText(wa ? `Escribinos al WhatsApp  ${wa}` : "Escribinos por mensaje", 80, y);
}

// Precio dentro de un sticker redondo, un poco inclinado.
function sticker(ctx, precio, { x, y, r, rot }, bg, fg) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(rot);
  ctx.fillStyle = bg;
  ctx.beginPath();
  ctx.arc(0, 0, r, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = fg;
  ctx.globalAlpha = 0.45;
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.arc(0, 0, r - 14, 0, Math.PI * 2);
  ctx.stroke();
  ctx.globalAlpha = 1;
  ctx.fillStyle = fg;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  font(ctx, 700, Math.round(r * 0.19), false);
  ctx.fillText("PRECIO", 0, -r * 0.42);
  let size = Math.round(r * 0.5);
  font(ctx, 400, size, true);
  while (size > 24 && ctx.measureText(precio).width > r * 1.6) {
    size -= 4;
    font(ctx, 400, size, true);
  }
  ctx.fillText(precio, 0, r * 0.08);
  ctx.restore();
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
}

// Cinta a rayas diagonales (como la de "obra en construccion").
function franja(ctx, x, y, w, h, [c1, c2]) {
  ctx.save();
  ctx.beginPath();
  ctx.rect(x, y, w, h);
  ctx.clip();
  ctx.fillStyle = c2;
  ctx.fillRect(x, y, w, h);
  ctx.fillStyle = c1;
  for (let i = x - h; i < x + w + h; i += 56) {
    ctx.beginPath();
    ctx.moveTo(i, y + h);
    ctx.lineTo(i + 28, y + h);
    ctx.lineTo(i + 28 + h, y);
    ctx.lineTo(i + h, y);
    ctx.closePath();
    ctx.fill();
  }
  ctx.restore();
}

// La foto completa con su fondo: la misma foto agrandada y desenfocada, y
// encima la foto entera sin recortar (para fotos que no son verticales).
function entera(ctx, img, ancho, alto, zoom) {
  const iw = img.naturalWidth || img.width;
  const ih = img.naturalHeight || img.height;
  ctx.save();
  ctx.filter = "blur(40px) brightness(.7)";
  cover(ctx, img, -60, -60, ancho + 120, alto + 120, 1, 0, 0);
  ctx.restore();
  // Algunos navegadores no aplican filter: un velo oscuro mantiene la foto al frente.
  ctx.fillStyle = "rgba(20,24,28,.35)";
  ctx.fillRect(0, 0, ancho, alto);
  const s = Math.min(ancho / iw, alto / ih) * zoom;
  const w = iw * s;
  const h = ih * s;
  ctx.drawImage(img, (ancho - w) / 2, (alto - h) / 2, w, h);
}

function elegirFormato(state) {
  return FORMATOS[state.formato] ? state.formato : "historia";
}

function elegirLayout(formato, t) {
  // Las plantillas de varias fotos son solo de historia: en otro formato se arman como "framed".
  return LAYOUTS[formato][t.mode] || LAYOUTS[formato].framed;
}

/**
 * Rectangulos (x, y, ancho, alto) donde va cada foto, en pixeles del canvas.
 * Sirve para saber que foto se esta arrastrando en la vista previa.
 */
export function rectsDeFotos(state) {
  const formato = elegirFormato(state);
  const { ancho, alto } = FORMATOS[formato];
  const t = TEMPLATES[state.tipo] || TEMPLATES.usada;
  if (t.mode === "raw" || t.mode === "backdrop") return [[0, 0, ancho, alto]];
  const L = elegirLayout(formato, t);
  return L.fotos || [L.foto];
}

/**
 * Dibuja la pieza completa (historia o post del feed) en el canvas dado.
 * @param {HTMLCanvasElement} canvas  del tamaño de FORMATOS[state.formato]
 * @param {object} state  { formato, tipo, color, fotos: [{img, zoom, ox, oy}], ajuste, titulo, detalle, precio, whatsapp }
 * @param {HTMLImageElement|null} logoImg  imagen del isologotipo ya cargada, o null
 * @param {HTMLImageElement} sampleImg  imagen de ejemplo cuando no hay foto propia
 */
export function drawStory(canvas, state, logoImg, sampleImg) {
  const ctx = canvas.getContext("2d");
  const formato = elegirFormato(state);
  const { ancho, alto } = FORMATOS[formato];
  const t = TEMPLATES[state.tipo] || TEMPLATES.usada;
  const s = COLORS[state.color] || COLORS.azul;
  const c = t.colorsFor(s);
  // Cada lugar de foto: la elegida o, si todavia no hay, la bici de ejemplo.
  const foto = (i) => {
    const f = state.fotos?.[i] || {};
    return { img: f.img || sampleImg, zoom: f.zoom || 1, ox: f.ox || 0, oy: f.oy || 0 };
  };
  const img = foto(0).img;
  const L = elegirLayout(formato, t);
  const k = L.texto?.k || 1;

  ctx.textBaseline = "top";
  ctx.textAlign = "left";
  ctx.globalAlpha = 1;
  ctx.fillStyle = c.bg;
  ctx.fillRect(0, 0, ancho, alto);

  const drawLogo = ([x, y, size]) => {
    if (logoImg) ctx.drawImage(logoImg, x, y, size, size);
  };

  if (!img) return;

  if (t.mode === "raw") {
    // Sin plantilla: solo la foto, sin logo ni texto.
    const f = foto(0);
    if (state.ajuste === "entera") entera(ctx, f.img, ancho, alto, f.zoom);
    else cover(ctx, f.img, 0, 0, ancho, alto, f.zoom, f.ox, f.oy);
    return;
  }

  const { zoom, ox, oy } = foto(0);
  if (L.fotos) {
    L.fotos.forEach((r, i) => {
      const f = foto(i);
      cover(ctx, f.img, ...r, f.zoom, f.ox, f.oy);
    });
    drawLogo(L.logo);
    ctx.save();
    ctx.translate(L.pill.x, L.pill.y);
    ctx.rotate(L.pill.rot);
    pill(ctx, t.label, 0, 0, c.lb, c.lf, true, k);
    ctx.restore();
  } else if (t.mode === "framed" || !LAYOUTS[formato][t.mode]) {
    cover(ctx, img, ...L.foto, zoom, ox, oy);
    drawLogo(L.logo);
    ctx.save();
    ctx.translate(L.pill.x, L.pill.y);
    ctx.rotate(L.pill.rot);
    pill(ctx, t.label, 0, 0, c.lb, c.lf, true, k);
    ctx.restore();
  } else if (t.mode === "polaroid") {
    // Marco blanco con sombra, inclinado; la foto va adentro con el mismo giro.
    const [mx, my, mw, mh] = L.marco;
    const cx = mx + mw / 2;
    const cy = my + mh / 2;
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(L.rot);
    ctx.translate(-cx, -cy);
    ctx.shadowColor = "rgba(0,0,0,.35)";
    ctx.shadowBlur = 30;
    ctx.shadowOffsetY = 12;
    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(mx, my, mw, mh);
    ctx.shadowColor = "transparent";
    cover(ctx, img, ...L.foto, zoom, ox, oy);
    ctx.restore();
    drawLogo(L.logo);
    pill(ctx, t.label, L.pill.x, L.pill.y, c.lb, c.lf, true, k);
    const precio = fmtPrice(state.precio);
    if (precio) sticker(ctx, precio, L.sticker, c.pb, c.pf);
  } else if (t.mode === "banda") {
    // Palabra gigante, lo mas grande que entre al lado del logo.
    const P = L.palabra;
    let size = P.max;
    font(ctx, 400, size, true);
    const palabra = t.palabra.toUpperCase();
    while (size > 60 && ctx.measureText(palabra).width > P.maxW) {
      size -= 6;
      font(ctx, 400, size, true);
    }
    ctx.fillStyle = c.lb;
    ctx.fillText(palabra, P.x, P.y + (P.max - size) / 2);
    drawLogo(L.logo);
    const [fx, fy, fw, fh] = L.foto;
    cover(ctx, img, fx, fy, fw, fh, zoom, ox, oy);
    franja(ctx, fx, fy - L.franja, fw, L.franja, c.franja);
    franja(ctx, fx, fy + fh, fw, L.franja, c.franja);
  } else if (t.mode === "bleed") {
    cover(ctx, img, ...L.foto, zoom, ox, oy);
    const g = ctx.createLinearGradient(0, 0, 0, L.degrade);
    g.addColorStop(0, "rgba(0,0,0,.6)");
    g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, ancho, L.degrade);
    drawLogo(L.logo);
    pill(ctx, t.label, L.pill.x, L.pill.y, c.lb, c.lf, false, k);
  } else {
    cover(ctx, img, 0, 0, ancho, alto, zoom, ox, oy);
    ctx.fillStyle = "rgba(20,24,28,.68)";
    ctx.fillRect(0, 0, ancho, alto);
    drawLogo(L.logo);
    pill(ctx, t.label, L.pill.x, L.pill.y, c.lb, c.lf, false, k);
  }
  textBlock(ctx, state, L.texto.y, c, L.texto);
}
