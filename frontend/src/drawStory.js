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
  const price = fmtPrice(state.precio);
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

/**
 * Dibuja la pieza completa (historia o post del feed) en el canvas dado.
 * @param {HTMLCanvasElement} canvas  del tamaño de FORMATOS[state.formato]
 * @param {object} state  { formato, tipo, color, imagen (HTMLImageElement|null), zoom, ox, oy, titulo, detalle, precio, whatsapp }
 * @param {HTMLImageElement|null} logoImg  imagen del isologotipo ya cargada, o null
 * @param {HTMLImageElement} sampleImg  imagen de ejemplo cuando no hay foto propia
 */
export function drawStory(canvas, state, logoImg, sampleImg) {
  const ctx = canvas.getContext("2d");
  const formato = FORMATOS[state.formato] ? state.formato : "historia";
  const { ancho, alto } = FORMATOS[formato];
  const t = TEMPLATES[state.tipo] || TEMPLATES.usada;
  const s = COLORS[state.color] || COLORS.azul;
  const c = t.colorsFor(s);
  const img = state.imagen || sampleImg;
  const L = LAYOUTS[formato][t.mode] || LAYOUTS[formato].backdrop;
  const k = L.texto.k || 1;

  ctx.textBaseline = "top";
  ctx.textAlign = "left";
  ctx.globalAlpha = 1;
  ctx.fillStyle = c.bg;
  ctx.fillRect(0, 0, ancho, alto);

  const drawLogo = ([x, y, size]) => {
    if (logoImg) ctx.drawImage(logoImg, x, y, size, size);
  };

  if (!img) return;

  if (t.mode === "framed") {
    cover(ctx, img, ...L.foto, state.zoom, state.ox, state.oy);
    drawLogo(L.logo);
    ctx.save();
    ctx.translate(L.pill.x, L.pill.y);
    ctx.rotate(L.pill.rot);
    pill(ctx, t.label, 0, 0, c.lb, c.lf, true, k);
    ctx.restore();
  } else if (t.mode === "bleed") {
    cover(ctx, img, ...L.foto, state.zoom, state.ox, state.oy);
    const g = ctx.createLinearGradient(0, 0, 0, L.degrade);
    g.addColorStop(0, "rgba(0,0,0,.6)");
    g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, ancho, L.degrade);
    drawLogo(L.logo);
    pill(ctx, t.label, L.pill.x, L.pill.y, c.lb, c.lf, false, k);
  } else {
    cover(ctx, img, 0, 0, ancho, alto, state.zoom, state.ox, state.oy);
    ctx.fillStyle = "rgba(20,24,28,.68)";
    ctx.fillRect(0, 0, ancho, alto);
    drawLogo(L.logo);
    pill(ctx, t.label, L.pill.x, L.pill.y, c.lb, c.lf, false, k);
  }
  textBlock(ctx, state, L.texto.y, c, L.texto);
}
