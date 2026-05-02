const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    getSettings: () => ipcRenderer.invoke('get-settings'),
    saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),
    selectDownloadFolder: () => ipcRenderer.invoke('select-download-folder'),
    openExternal: (url) => ipcRenderer.invoke('open-external', url),
    getAppVersion: () => ipcRenderer.invoke('get-app-version'),
    getPlatform: () => ipcRenderer.invoke('get-platform'),
    onOpenSettings: (callback) => ipcRenderer.on('open-settings', callback),
    isElectron: true
});
