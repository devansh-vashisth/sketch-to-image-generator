const pad = document.getElementById("pad");
const ctx = pad.getContext("2d");
const sizeInput = document.getElementById("size");
const result = document.getElementById("result");
const download = document.getElementById("download");
const meta = document.getElementById("meta");
const statusPill = document.getElementById("status");
const live = document.getElementById("live");

let tool = "pen";
let drawing = false;
let last = null;
const history = [];

function resetCanvas() {
  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, pad.width, pad.height);
}
resetCanvas();

function pos(e) {
  const r = pad.getBoundingClientRect();
  return { x: (e.clientX - r.left) * pad.width / r.width, y: (e.clientY - r.top) * pad.height / r.height };
}

pad.addEventListener("pointerdown", (e) => {
  history.push(ctx.getImageData(0, 0, pad.width, pad.height));
  if (history.length > 30) history.shift();
  drawing = true;
  last = pos(e);
  pad.setPointerCapture(e.pointerId);
});

pad.addEventListener("pointermove", (e) => {
  if (!drawing) return;
  const p = pos(e);
  ctx.strokeStyle = tool === "pen" ? "#000" : "#fff";
  ctx.lineWidth = tool === "pen" ? Number(sizeInput.value) : Number(sizeInput.value) * 4;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.beginPath();
  ctx.moveTo(last.x, last.y);
  ctx.lineTo(p.x, p.y);
  ctx.stroke();
  last = p;
});

pad.addEventListener("pointerup", () => {
  drawing = false;
  if (live.checked) generate();
});

document.querySelectorAll("[data-tool]").forEach((b) =>
  b.addEventListener("click", () => {
    tool = b.dataset.tool;
    document.querySelectorAll("[data-tool]").forEach((x) => x.classList.toggle("active", x === b));
  })
);

document.getElementById("undo").onclick = () => { if (history.length) ctx.putImageData(history.pop(), 0, 0); };
document.getElementById("clear").onclick = () => {
  history.push(ctx.getImageData(0, 0, pad.width, pad.height));
  resetCanvas();
};

document.getElementById("upload").onchange = (e) => {
  const f = e.target.files[0];
  if (!f) return;
  const img = new Image();
  img.onload = () => {
    history.push(ctx.getImageData(0, 0, pad.width, pad.height));
    resetCanvas();
    const s = Math.min(pad.width / img.width, pad.height / img.height);
    const w = img.width * s, h = img.height * s;
    ctx.drawImage(img, (pad.width - w) / 2, (pad.height - h) / 2, w, h);
    URL.revokeObjectURL(img.src);
  };
  img.src = URL.createObjectURL(f);
};

let busy = false;
async function generate() {
  if (busy) return;
  busy = true;
  result.classList.add("loading");
  try {
    const blob = await new Promise((r) => pad.toBlob(r, "image/png"));
    const fd = new FormData();
    fd.append("file", blob, "sketch.png");
    const res = await fetch("/api/generate", { method: "POST", body: fd });
    if (!res.ok) throw new Error((await res.json()).detail || res.statusText);
    const url = URL.createObjectURL(await res.blob());
    result.innerHTML = "";
    const img = document.createElement("img");
    img.src = url;
    img.alt = "Generated image";
    result.appendChild(img);
    download.href = url;
    download.classList.remove("disabled");
    meta.textContent = `Inference: ${res.headers.get("X-Inference-Ms")} ms`;
  } catch (err) {
    meta.textContent = "Error: " + err.message;
  } finally {
    busy = false;
    result.classList.remove("loading");
  }
}
document.getElementById("generate").onclick = generate;

fetch("/api/health").then((r) => r.json()).then((h) => {
  if (h.model_loaded) {
    statusPill.textContent = `model ready · epoch ${h.epoch} · ${h.device} · ${h.image_size}px`;
    statusPill.classList.add("ok");
  } else {
    statusPill.textContent = "no checkpoint loaded";
    statusPill.classList.add("err");
  }
}).catch(() => { statusPill.textContent = "server unreachable"; statusPill.classList.add("err"); });
