const { app, BrowserWindow, dialog } = require("electron");
const { spawn } = require("node:child_process");
const path = require("node:path");

const PORT = 8765;
const HOST = "127.0.0.1";
const APP_URL = `http://${HOST}:${PORT}/`;
const HEALTH_URL = `http://${HOST}:${PORT}/api/health`;
const ENGINE_URL = `http://${HOST}:${PORT}/api/engine`;
const WARMUP_URL = `http://${HOST}:${PORT}/api/engine/warmup`;

let backend = null;
let mainWindow = null;
let ownsBackend = false;

function pythonExecutable() {
  const exe = process.platform === "win32" ? "python.exe" : "python";
  return path.join(__dirname, "..", ".venv", process.platform === "win32" ? "Scripts" : "bin", exe);
}

function cudaPathPrefix() {
  const root = path.join(__dirname, "..");
  const venvPackages = path.join(root, ".venv", "Lib", "site-packages");
  const programFiles = process.env.ProgramFiles || "C:\\Program Files";
  const cudaRoot = path.join(programFiles, "NVIDIA GPU Computing Toolkit", "CUDA");
  const candidates = [
    path.join(venvPackages, "nvidia", "cublas", "bin"),
    path.join(venvPackages, "nvidia", "cudnn", "bin"),
    path.join(venvPackages, "nvidia", "cuda_runtime", "bin"),
    ...["v12.6", "v12.5", "v12.4", "v12.3", "v12.2", "v12.1", "v12.0"].map((version) =>
      path.join(cudaRoot, version, "bin")
    ),
  ];
  return candidates.join(path.delimiter);
}

async function healthCheck() {
  try {
    const response = await fetch(HEALTH_URL);
    return response.ok;
  } catch {
    return false;
  }
}

async function waitForBackend(timeoutMs = 45000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    if (await healthCheck()) return true;
    await new Promise((resolve) => setTimeout(resolve, 700));
  }
  return false;
}

async function waitForEngine(timeoutMs = 15 * 60 * 1000) {
  const startedAt = Date.now();
  await fetch(WARMUP_URL, { method: "POST" });
  while (Date.now() - startedAt < timeoutMs) {
    try {
      const response = await fetch(ENGINE_URL);
      const data = await response.json();
      if (["ready", "failed"].includes(data.status)) return data;
    } catch {
      // Keep waiting while the backend starts.
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  return { status: "failed", message: "Tempo limite ao carregar motor" };
}

async function startBackend() {
  if (await healthCheck()) {
    ownsBackend = false;
    return true;
  }

  const python = pythonExecutable();
  backend = spawn(
    python,
    ["-m", "uvicorn", "app.main:app", "--host", HOST, "--port", String(PORT)],
    {
      cwd: path.join(__dirname, ".."),
      windowsHide: true,
      stdio: "ignore",
      env: {
        ...process.env,
        PATH: `${cudaPathPrefix()}${path.delimiter}${process.env.PATH || ""}`,
      },
    }
  );
  ownsBackend = true;

  backend.on("exit", () => {
    backend = null;
  });

  return waitForBackend();
}

function createWindow() {
  const brandAssetUrl = encodeURI(
    `file:///${path.join(__dirname, "..", "web", "assets", "editory-brand.png").replace(/\\/g, "/")}`
  );

  mainWindow = new BrowserWindow({
    width: 1240,
    height: 860,
    minWidth: 980,
    minHeight: 680,
    backgroundColor: "#000000",
    title: "Editory",
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
  });

  mainWindow.loadURL(
    "data:text/html;charset=utf-8," +
      encodeURIComponent(`
        <!doctype html>
        <html>
          <head>
            <meta charset="utf-8" />
            <style>
              body {
                margin: 0;
                height: 100vh;
                overflow: hidden;
                display: grid;
                place-items: center;
                background:
                  radial-gradient(46vmax 46vmax at -8% -10%, rgba(75,19,159,.55), transparent 65%),
                  radial-gradient(42vmax 42vmax at 108% 112%, rgba(118,14,165,.42), transparent 65%),
                  radial-gradient(120% 80% at 50% 40%, #050526 0%, #010131 42%, #030318 72%, #000000 100%);
                color: #ffffff;
                font-family: Inter, "Segoe UI", Arial, sans-serif;
              }
              .stack {
                width: min(620px, calc(100vw - 48px));
                display: grid;
                justify-items: center;
                gap: 24px;
                text-align: center;
                animation: enter .8s cubic-bezier(.2,.7,.2,1) both;
              }
              .brand {
                width: min(560px, 86vw);
                height: auto;
                filter: drop-shadow(0 28px 62px rgba(0,0,0,.34)) drop-shadow(0 0 32px rgba(118,14,165,.2));
              }
              p {
                margin: 0;
                color: rgba(255,255,255,.62);
                letter-spacing: .08em;
                font-size: 14px;
                font-weight: 700;
              }
              .bar {
                width: min(360px, 82vw);
                height: 5px;
                border-radius: 999px;
                overflow: hidden;
                background: rgba(255,255,255,.06);
              }
              .bar span {
                display: block;
                width: 64%;
                height: 100%;
                border-radius: inherit;
                background: linear-gradient(90deg, #4b139f, #760ea5);
                box-shadow: 0 0 12px rgba(118,14,165,.55), inset 0 0 6px rgba(255,255,255,.25);
                animation: load 2.6s ease-in-out infinite;
              }
              @keyframes spin { to { transform: rotate(360deg); } }
              @keyframes load {
                0% { width: 18%; }
                55% { width: 78%; }
                100% { width: 92%; }
              }
              @keyframes enter {
                from { opacity: 0; transform: translateY(14px); }
                to { opacity: 1; transform: translateY(0); }
              }
              @media (prefers-reduced-motion: reduce) {
                *, *:before { animation: none !important; }
              }
            </style>
          </head>
          <body>
            <div class="stack">
              <img class="brand" src="${brandAssetUrl}" alt="Editory" />
              <p>Ligando os motores...</p>
              <div class="bar" aria-hidden="true"><span></span></div>
            </div>
          </body>
        </html>
      `)
  );
}

function stopBackend() {
  if (backend && ownsBackend) {
    backend.kill();
  }
}

app.whenReady().then(async () => {
  createWindow();

  const ready = await startBackend();
  if (!ready) {
    await dialog.showMessageBox({
      type: "error",
      title: "Editory",
      message: "Nao foi possivel iniciar o backend local.",
      detail: "Rode scripts/install.ps1 e tente abrir o app novamente.",
    });
    app.quit();
    return;
  }

  await waitForEngine();
  if (mainWindow) mainWindow.loadURL(APP_URL);

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("before-quit", stopBackend);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
