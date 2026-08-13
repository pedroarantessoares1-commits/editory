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
  mainWindow = new BrowserWindow({
    width: 1240,
    height: 860,
    minWidth: 980,
    minHeight: 680,
    backgroundColor: "#070b12",
    title: "App Transcript",
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
                display: grid;
                place-items: center;
                background: radial-gradient(circle at 50% 20%, rgba(47,128,255,.24), transparent 34%), #070b12;
                color: #e8edf7;
                font-family: Segoe UI, Arial, sans-serif;
              }
              .box {
                width: min(440px, calc(100vw - 40px));
                border: 1px solid #253047;
                border-radius: 8px;
                background: #111827;
                padding: 28px;
                text-align: center;
                box-shadow: 0 24px 80px rgba(0,0,0,.45);
              }
              .spin {
                width: 42px;
                height: 42px;
                margin: 0 auto 18px;
                border: 4px solid #20304a;
                border-top-color: #2f80ff;
                border-radius: 50%;
                animation: spin .9s linear infinite;
              }
              @keyframes spin { to { transform: rotate(360deg); } }
              h1 { margin: 0 0 8px; font-size: 24px; }
              p { margin: 0; color: #8f9bb3; }
            </style>
          </head>
          <body>
            <div class="box">
              <div class="spin"></div>
              <h1>Preparando motor de transcricao</h1>
              <p>Carregando tudo de uma vez para evitar travar por video.</p>
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
      title: "App Transcript",
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
