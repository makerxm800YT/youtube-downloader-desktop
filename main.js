const { app, BrowserWindow, Menu, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');

let mainWindow;
let pythonProcess = null;

// Settings storage
const settingsPath = path.join(app.getPath('userData'), 'settings.json');
let appSettings = {
    downloadPath: app.getPath('downloads'),
    theme: 'dark',
    autoUpdate: true
};

function loadSettings() {
    try {
        if (fs.existsSync(settingsPath)) {
            const saved = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
            appSettings = { ...appSettings, ...saved };
        }
    } catch (e) {}
}

function saveSettings() {
    try {
        fs.writeFileSync(settingsPath, JSON.stringify(appSettings, null, 2));
    } catch (e) {}
}

function startPythonBackend() {
    return new Promise((resolve) => {
        const pythonScript = path.join(__dirname, 'app.py');
        const python = process.platform === 'win32' ? 'python' : 'python3';
        
        pythonProcess = spawn(python, [pythonScript]);
        
        pythonProcess.stdout.on('data', (data) => {
            if (data.toString().includes('Running on http://localhost:5000')) {
                resolve();
            }
        });
        
        setTimeout(() => resolve(), 3000);
    });
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 900,
        minHeight: 600,
        icon: path.join(__dirname, 'icon.png'),
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        backgroundColor: '#0b0b0b',
        show: false,
        titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default'
    });

    // Custom menu
    const menuTemplate = [
        {
            label: 'YouTube Downloader',
            submenu: [
                { label: 'About', click: () => showAboutDialog() },
                { type: 'separator' },
                { label: 'Quit', accelerator: 'CmdOrCtrl+Q', click: () => app.quit() }
            ]
        },
        {
            label: 'View',
            submenu: [
                { label: 'Reload', accelerator: 'CmdOrCtrl+R', click: () => mainWindow.reload() },
                { label: 'Toggle DevTools', accelerator: 'CmdOrCtrl+Shift+I', click: () => mainWindow.webContents.toggleDevTools() }
            ]
        }
    ];

    const menu = Menu.buildFromTemplate(menuTemplate);
    Menu.setApplicationMenu(menu);

    mainWindow.loadURL('http://localhost:5000');
    
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    mainWindow.on('closed', () => {
        if (pythonProcess) pythonProcess.kill();
        mainWindow = null;
    });
}

function showAboutDialog() {
    dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'About YouTube Downloader',
        message: 'YouTube Downloader Desktop',
        detail: `Version: 1.0.0\n\nA powerful YouTube video downloader\n\n• Free & Unlimited\n• Up to 4K Quality\n• Built-in Audio\n• Account Management`,
        buttons: ['OK']
    });
}

// IPC Handlers
ipcMain.handle('get-settings', () => appSettings);
ipcMain.handle('save-settings', (event, settings) => {
    appSettings = { ...appSettings, ...settings };
    saveSettings();
    return appSettings;
});
ipcMain.handle('select-download-folder', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
        properties: ['openDirectory', 'createDirectory'],
        title: 'Select Download Folder',
        defaultPath: appSettings.downloadPath
    });
    if (!result.canceled && result.filePaths[0]) {
        appSettings.downloadPath = result.filePaths[0];
        saveSettings();
        return result.filePaths[0];
    }
    return appSettings.downloadPath;
});
ipcMain.handle('get-app-version', () => app.getVersion());

app.whenReady().then(async () => {
    loadSettings();
    await startPythonBackend();
    createWindow();
});

app.on('window-all-closed', () => {
    if (pythonProcess) pythonProcess.kill();
    if (process.platform !== 'darwin') app.quit();
});
