// Bici de ejemplo dibujada a mano, para que el paso de la foto no arranque vacio.
// Portado del prototipo (artifact) tal cual.

export function makeSampleImage() {
  const c = document.createElement("canvas");
  c.width = 1400;
  c.height = 1100;
  const g = c.getContext("2d");

  const wall = g.createLinearGradient(0, 0, 0, 860);
  wall.addColorStop(0, "#D5DCE0");
  wall.addColorStop(1, "#BCC6CB");
  g.fillStyle = wall;
  g.fillRect(0, 0, 1400, 860);
  g.fillStyle = "#8B969C";
  g.fillRect(0, 860, 1400, 240);
  g.fillStyle = "rgba(0,0,0,.18)";
  g.beginPath();
  g.ellipse(700, 935, 430, 26, 0, 0, Math.PI * 2);
  g.fill();

  g.lineCap = "round";
  g.lineJoin = "round";

  for (const x of [400, 1000]) {
    g.strokeStyle = "#8C979D";
    g.lineWidth = 2;
    for (let i = 0; i < 18; i++) {
      const a = (i * Math.PI) / 9;
      g.beginPath();
      g.moveTo(x, 720);
      g.lineTo(x + Math.cos(a) * 190, 720 + Math.sin(a) * 190);
      g.stroke();
    }
    g.strokeStyle = "#A9B3B8";
    g.lineWidth = 8;
    g.beginPath();
    g.arc(x, 720, 190, 0, Math.PI * 2);
    g.stroke();
    g.strokeStyle = "#1B1B1B";
    g.lineWidth = 28;
    g.beginPath();
    g.arc(x, 720, 208, 0, Math.PI * 2);
    g.stroke();
  }

  const L = (a, b, c2, d, col, w) => {
    g.strokeStyle = col;
    g.lineWidth = w;
    g.beginPath();
    g.moveTo(a, b);
    g.lineTo(c2, d);
    g.stroke();
  };
  L(930, 520, 1000, 720, "#23282C", 18);
  L(400, 720, 640, 720, "#D7372F", 16);
  L(400, 720, 580, 440, "#D7372F", 16);
  L(640, 720, 580, 440, "#D7372F", 22);
  L(580, 440, 900, 430, "#D7372F", 22);
  L(640, 720, 930, 520, "#D7372F", 24);
  L(900, 430, 930, 520, "#D7372F", 24);
  L(580, 440, 566, 376, "#555", 12);
  L(516, 372, 624, 372, "#111", 24);
  L(900, 430, 886, 360, "#555", 12);
  L(846, 356, 950, 350, "#111", 18);

  g.fillStyle = "#23282C";
  g.beginPath();
  g.arc(640, 720, 44, 0, Math.PI * 2);
  g.fill();
  L(640, 720, 690, 790, "#23282C", 12);
  L(668, 794, 712, 786, "#111", 14);

  return c;
}
