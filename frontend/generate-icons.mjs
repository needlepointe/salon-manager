// Run with: node generate-icons.mjs
// Generates PWA icons as simple colored PNGs
import { createCanvas } from "canvas";
import { writeFileSync } from "fs";

function makeIcon(size, outPath) {
  const canvas = createCanvas(size, size);
  const ctx = canvas.getContext("2d");

  // Purple background
  ctx.fillStyle = "#7c3aed";
  const r = size * 0.2;
  ctx.beginPath();
  ctx.moveTo(r, 0);
  ctx.lineTo(size - r, 0);
  ctx.quadraticCurveTo(size, 0, size, r);
  ctx.lineTo(size, size - r);
  ctx.quadraticCurveTo(size, size, size - r, size);
  ctx.lineTo(r, size);
  ctx.quadraticCurveTo(0, size, 0, size - r);
  ctx.lineTo(0, r);
  ctx.quadraticCurveTo(0, 0, r, 0);
  ctx.closePath();
  ctx.fill();

  // White S letter
  ctx.fillStyle = "#ffffff";
  ctx.font = `bold ${size * 0.6}px Arial`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("S", size / 2, size / 2);

  writeFileSync(outPath, canvas.toBuffer("image/png"));
  console.log(`Created ${outPath}`);
}

makeIcon(192, "public/pwa-192.png");
makeIcon(512, "public/pwa-512.png");
makeIcon(180, "public/apple-touch-icon.png");
