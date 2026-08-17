const { contextBridge, ipcRenderer } = require("electron");

const updateEvents = new Set([
  "checking",
  "available",
  "not-available",
  "download-progress",
  "downloaded",
  "error",
  "disabled",
]);

contextBridge.exposeInMainWorld("editory", {
  updates: {
    getState: () => ipcRenderer.invoke("updates:get-state"),
    check: () => ipcRenderer.invoke("updates:check"),
    download: () => ipcRenderer.invoke("updates:download"),
    install: () => ipcRenderer.invoke("updates:install"),
    openRelease: () => ipcRenderer.invoke("updates:open-release"),
    onStatus: (callback) => {
      if (typeof callback !== "function") return () => {};
      const listener = (_event, payload) => {
        if (payload && updateEvents.has(payload.status)) callback(payload);
      };
      ipcRenderer.on("updates:status", listener);
      return () => ipcRenderer.removeListener("updates:status", listener);
    },
  },
  app: {
    getVersion: () => ipcRenderer.invoke("app:get-version"),
    getPlatform: () => ipcRenderer.invoke("app:get-platform"),
  },
});
