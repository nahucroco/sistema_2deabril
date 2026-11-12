// Logica de dibujo de la historia en <canvas>, portada del prototipo (artifact)
// para reusarla igual en la app real. Mismas reglas visuales, mismos tokens de brand.js.

import { COLORS, FONT_BODY, FONT_DISPLAY, STORY_HEIGHT, STORY_WIDTH, TEMPLATES } from "./brand";

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

function pill(ctx, text, x, y, bg, fg, alignRight) {
  font(ctx, 400, 50, true);
  const t = text.toUpperCase();
  const w = ctx.measureText(t).width + 60;
  const hh = 84;
  const px = alignRight ? x - w : x;
  ctx.fillStyle = bg;
  ctx.fillRect(px, y, w, hh);
  ctx.fillStyle = fg;
  ctx.fillText(t, px + 30, y + 20);
  return hh;
}

function textBlock(ctx, state, y, c, opt) {
  const maxW = STORY_WIDTH - 160;
  let fit = null;
  const title = (state.titulo || "").trim();
  if (title) {
    for (let size = opt.max; size >= opt.min; size -= 6) {
      font(ctx, 400, size, true);
      const lines = wrap(ctx, title, maxW);
      if (lines.length <= opt.lines) {
        fit = { size, lines };
        break;
      }
    }
    if (!fit) {
      font(ctx, 400, opt.min, true);
      fit = { size: opt.min, lines: clampLines(ctx, wrap(ctx, title, maxW), opt.lines + 1, maxW) };
    }
    font(ctx, 400, fit.size, true);
    ctx.fillStyle = c.fg;
    for (const line of fit.lines) {
      ctx.fillText(line, 80, y);
      y += Math.round(fit.size * 1.02);
    }
    y += 22;
  }
  if ((state.detalle || "").trim()) {
    font(ctx, 500, 42, false);
    ctx.fillStyle = c.fg;
    ctx.globalAlpha = 0.88;
    for (const line of clampLines(ctx, wrap(ctx, state.detalle.trim(), maxW), 2, maxW)) {
      ctx.fillText(line, 80, y);
      y += 56;
    }
    ctx.globalAlpha = 1;
    y += 28;
  }
  const price = fmtPrice(state.precio);
  if (price) {
    let ps = 104;
    font(ctx, 400, ps, true);
    while (ps > 60 && ctx.measureText(price).width > maxW - 72) {
      ps -= 6;
      font(ctx, 400, ps, true);
    }
    if (c.pb) {
      const w = ctx.measureText(price).width + 72;
      ctx.fillStyle = c.pb;
      ctx.fillRect(80, y, w, ps + 26);
      ctx.fillStyle = c.pf;
      ctx.fillText(price, 116, y + 14);
      y += ps + 26;
    } else {
      ctx.fillStyle = c.pf;
      ctx.fillText(price, 80, y);
      y += ps;
    }
    y += 40;
  }
  ctx.fillStyle = c.fg;
  ctx.fillRect(80, y, 120, 6);
  y += 26;
  font(ctx, 600, 40, false);
  const wa = (state.whatsapp || "").trim();
  ctx.fillText(wa ? `Escribinos al WhatsApp  ${wa}` : "Escribinos por mensaje", 80, y);
}

/**
 * Dibuja la historia completa en el canvas dado.
 * @param {HTMLCanvasElement} canvas
 * @param {object} state  { tipo, color, imagen (HTMLImageElement|null), zoom, ox, oy, titulo, detalle, precio, whatsapp }
 * @param {HTMLImageElement|null} logoImg  imagen del isologotipo ya cargada, o null
 * @param {HTMLImageElement} sampleImg  imagen de ejemplo cuando no hay foto propia
 */
export function drawStory(canvas, state, logoImg, sampleImg) {
  const ctx = canvas.getContext("2d");
  const t = TEMPLATES[state.tipo] || TEMPLATES.usada;
  const s = COLORS[state.color] || COLORS.azul;
  const c = t.colorsFor(s);
  const img = state.imagen || sampleImg;

  ctx.textBaseline = "top";
  ctx.textAlign = "left";
  ctx.globalAlpha = 1;
  ctx.fillStyle = c.bg;
  ctx.fillRect(0, 0, STORY_WIDTH, STORY_HEIGHT);

  const drawLogo = (x, y, size) => {
    if (logoImg) ctx.drawImage(logoImg, x, y, size, size);
  };

  if (!img) return;

  if (t.mode === "framed") {
    cover(ctx, img, 80, 340, 920, 560, state.zoom, state.ox, state.oy);
    drawLogo(50, 240, 200);
    ctx.save();
    ctx.translate(1020, 860);
    ctx.rotate(-0.05);
    pill(ctx, t.label, 0, 0, c.lb, c.lf, true);
    ctx.restore();
    textBlock(ctx, state, 980, c, { max: 100, min: 68, lines: 2 });
  } else if (t.mode === "bleed") {
    cover(ctx, img, 0, 0, STORY_WIDTH, 840, state.zoom, state.ox, state.oy);
    const g = ctx.createLinearGradient(0, 0, 0, 420);
    g.addColorStop(0, "rgba(0,0,0,.6)");
    g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, STORY_WIDTH, 420);
    drawLogo(70, 250, 200);
    pill(ctx, t.label, 80, 798, c.lb, c.lf, false);
    textBlock(ctx, state, 940, c, { max: 100, min: 68, lines: 2 });
  } else {
    cover(ctx, img, 0, 0, STORY_WIDTH, STORY_HEIGHT, state.zoom, state.ox, state.oy);
    ctx.fillStyle = "rgba(20,24,28,.68)";
    ctx.fillRect(0, 0, STORY_WIDTH, STORY_HEIGHT);
    drawLogo(80, 250, 220);
    pill(ctx, t.label, 80, 560, c.lb, c.lf, false);
    textBlock(ctx, state, 690, c, { max: 124, min: 76, lines: 4 });
  }
}
