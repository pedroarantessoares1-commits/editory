const { app, ipcMain, shell } = require("electron");
const { autoUpdater } = require("electron-updater");
const fs = require("node:fs");
const path = require("node:path");
const semver = require("semver");

const DEFAULT_STATE = {
  status: "idle",
  currentVersion: app.getVersion(),
  latestVersion: null,
  releaseName: "",
  releaseNotes: "",
  releaseUrl: "",
  assetUrl: "",
  platform: process.platform,
  percent: 0,
  error: "",
  isPackaged: app.isPackaged,
  updateMode: process.platform === "darwin" ? "manual-mac-alpha" : "auto",
};

function loadUpdateConfig() {
  const root = path.join(__dirname, "..");
  const candidates = [
    path.join(root, "distribution", "update-config.json"),
    path.join(process.resourcesPath || root, "distribution", "update-config.json"),
  ];

  for (const candidate of candidates) {
    try {
      if (fs.existsSync(candidate)) {
        return JSON.parse(fs.readFileSync(candidate, "utf-8"));
      }
    } catch (error) {
      console.warn("Nao foi possivel ler update-config.json:", error.message);
    }
  }

  return {};
}

function normalizeVersion(version) {
  return semver.valid(String(version || "").replace(/^v/i, ""));
}

function isAllowedChannel(version, channel) {
  const parsed = semver.parse(version);
  if (!parsed) return false;
  if (!parsed.prerelease.length) return channel === "stable";
  return parsed.prerelease[0] === channel;
}

function releaseToNotes(release) {
  return String(release.body || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .slice(0, 12)
    .join("\n");
}

function preferredMacAsset(release) {
  const assets = Array.isArray(release.assets) ? release.assets : [];
  return assets.find((asset) => /arm64.*\.dmg$/i.test(asset.name))
    || assets.find((asset) => /\.dmg$/i.test(asset.name) && !/x64|intel/i.test(asset.name))
    || assets.find((asset) => /arm64.*\.zip$/i.test(asset.name))
    || null;
}

function createUpdater(mainWindow) {
  const config = loadUpdateConfig();
  let state = { ...DEFAULT_STATE };
  let manualCheck = false;

  const hasGitHubConfig = Boolean(config.owner && config.repo);
  const releasesApi = hasGitHubConfig
    ? `https://api.github.com/repos/${config.owner}/${config.repo}/releases`
    : "";

  function publish(nextState) {
    state = { ...state, ...nextState };
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send("updates:status", state);
    }
    return state;
  }

  function disabled(reason) {
    return publish({
      status: "disabled",
      error: reason,
      releaseUrl: config.releaseUrl || "",
    });
  }

  async function fetchLatestRelease() {
    if (!hasGitHubConfig) {
      return { disabled: true, reason: "Repositorio GitHub de updates ainda nao configurado." };
    }

    const response = await fetch(releasesApi, {
      headers: {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Editory-Updater",
      },
    });

    if (!response.ok) {
      throw new Error(`GitHub Releases indisponivel (${response.status})`);
    }

    const releases = await response.json();
    const current = normalizeVersion(app.getVersion());
    const channel = config.channel || "alpha";
    const candidates = releases
      .filter((release) => !release.draft)
      .map((release) => ({
        release,
        version: normalizeVersion(release.tag_name || release.name),
      }))
      .filter((item) => item.version)
      .filter((item) => (config.allowPrerelease ? true : !item.release.prerelease))
      .filter((item) => isAllowedChannel(item.version, channel))
      .filter((item) => current && semver.gt(item.version, current))
      .sort((a, b) => semver.rcompare(a.version, b.version));

    return candidates[0] || null;
  }

  async function checkWithGitHubApi() {
    publish({ status: "checking", error: "" });
    const latest = await fetchLatestRelease();
    if (!latest) {
      return publish({ status: "not-available", latestVersion: null, error: "" });
    }
    if (latest.disabled) return disabled(latest.reason);

    const asset = process.platform === "darwin" ? preferredMacAsset(latest.release) : null;
    return publish({
      status: "available",
      latestVersion: latest.version,
      releaseName: latest.release.name || latest.release.tag_name || latest.version,
      releaseNotes: releaseToNotes(latest.release),
      releaseUrl: latest.release.html_url || config.releaseUrl || "",
      assetUrl: asset?.browser_download_url || latest.release.html_url || "",
      percent: 0,
      error: "",
    });
  }

  async function checkForUpdates({ manual = false } = {}) {
    manualCheck = manual;

    if (!hasGitHubConfig) {
      return disabled("Configure distribution/update-config.json com owner e repo antes de habilitar updates.");
    }

    try {
      if (process.platform === "win32" && app.isPackaged) {
        publish({ status: "checking", error: "" });
        return await autoUpdater.checkForUpdates();
      }
      return await checkWithGitHubApi();
    } catch (error) {
      const message = error?.message || "Nao foi possivel verificar atualizacoes.";
      if (manualCheck) return publish({ status: "error", error: message });
      console.warn("Update check falhou:", message);
      return publish({ status: "idle", error: "" });
    }
  }

  async function downloadUpdate() {
    if (process.platform === "darwin") {
      return openRelease();
    }

    if (!app.isPackaged) {
      return openRelease();
    }

    publish({ status: "checking", error: "" });
    return autoUpdater.downloadUpdate();
  }

  function installUpdate() {
    if (process.platform === "darwin" || !app.isPackaged) return openRelease();
    autoUpdater.quitAndInstall(false, true);
    return publish({ status: "downloaded" });
  }

  async function openRelease() {
    const target = state.assetUrl || state.releaseUrl || config.releaseUrl;
    if (!target) return publish({ status: "error", error: "Nenhum link de release configurado." });
    await shell.openExternal(target);
    return state;
  }

  autoUpdater.autoDownload = false;
  autoUpdater.allowPrerelease = Boolean(config.allowPrerelease);
  autoUpdater.autoInstallOnAppQuit = false;

  if (hasGitHubConfig) {
    autoUpdater.setFeedURL({
      provider: "github",
      owner: config.owner,
      repo: config.repo,
      releaseType: config.allowPrerelease ? "prerelease" : "release",
    });
  }

  autoUpdater.on("update-available", (info) => {
    publish({
      status: "available",
      latestVersion: normalizeVersion(info.version) || info.version,
      releaseName: info.releaseName || `Editory ${info.version}`,
      releaseNotes: Array.isArray(info.releaseNotes) ? info.releaseNotes.join("\n") : String(info.releaseNotes || ""),
      releaseUrl: config.releaseUrl || "",
      error: "",
    });
  });

  autoUpdater.on("update-not-available", () => {
    publish({ status: "not-available", latestVersion: null, error: "" });
  });

  autoUpdater.on("download-progress", (progress) => {
    publish({ status: "download-progress", percent: Math.round(progress.percent || 0), error: "" });
  });

  autoUpdater.on("update-downloaded", (info) => {
    publish({
      status: "downloaded",
      latestVersion: normalizeVersion(info.version) || state.latestVersion,
      percent: 100,
      error: "",
    });
  });

  autoUpdater.on("error", (error) => {
    const message = error?.message || "Erro no updater.";
    if (manualCheck) publish({ status: "error", error: message });
    else console.warn("Updater falhou:", message);
  });

  ipcMain.handle("updates:get-state", () => state);
  ipcMain.handle("updates:check", () => checkForUpdates({ manual: true }));
  ipcMain.handle("updates:download", () => downloadUpdate());
  ipcMain.handle("updates:install", () => installUpdate());
  ipcMain.handle("updates:open-release", () => openRelease());
  ipcMain.handle("app:get-version", () => app.getVersion());
  ipcMain.handle("app:get-platform", () => process.platform);

  return {
    checkForUpdates,
    getState: () => state,
  };
}

module.exports = { createUpdater };
