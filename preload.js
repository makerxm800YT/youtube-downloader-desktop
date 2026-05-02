const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    isElectron: true,
    getSettings: () => ipcRenderer.invoke('get-settings'),
    saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),
    selectDownloadFolder: () => ipcRenderer.invoke('select-download-folder'),
    getAppVersion: () => ipcRenderer.invoke('get-app-version')
});
