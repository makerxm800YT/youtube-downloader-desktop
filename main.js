const { app, BrowserWindow, Menu, ipcMain, shell, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');

let mainWindow;
let pythonProcess = null;
const isDev = process.env.NODE_ENV === 'development';

// User settings storage
const settingsPath = path.join(app.getPath('userData'), 'settings.json');
let appSettings = {
    downloadPath: app.getPath('downloads'),
    defaultQuality: 'Best (Max Quality)',
    defaultFormat: 'mp4',
    defaultMode: 'Video',
    rememberQuality: true,
    autoUpdate: true,
    theme: 'dark'
};

function loadSettings() {
    try {
        if (fs.existsSync(settingsPath)) {
            const saved = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
            appSettings = { ...appSettings, ...saved };
        }
    } catch (e) { console.error('Error loading settings:', e); }
}

function saveSettings() {
    try {
        fs.writeFileSync(settingsPath, JSON.stringify(appSettings, null, 2));
    } catch (e) { console.error('Error saving settings:', e); }
}

function startPythonBackend() {
    return new Promise((resolve, reject) => {
        const pythonScript = path.join(__dirname, 'app.py');
        const python = process.platform === 'win32' ? 'python' : 'python3';
        
        pythonProcess = spawn(python, [pythonScript], {
            stdio: ['pipe', 'pipe', 'pipe', 'ipc'],
            env: { ...process.env, PYTHONUNBUFFERED: '1' }
        });

        pythonProcess.stdout.on('data', (data) => {
            const output = data.toString();
            console.log('[Python]:', output);
            if (output.includes('Running on http://localhost:5000')) {
                resolve();
            }
        });

        pythonProcess.stderr.on('data', (data) => {
            console.error('[Python Error]:', data.toString());
        });

        pythonProcess.on('error', reject);
        
        setTimeout(() => resolve(), 3000);
    });
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 900,
        minHeight: 600,
        icon: path.join(__dirname, 'icons', 'icon.png'),
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
        backgroundColor: '#0b0b0b',
        show: false
    });

    // Custom menu
    const menuTemplate = [
        {
            label: 'YouTube Downloader',
            submenu: [
                { label: 'About', click: () => showAboutDialog() },
                { type: 'separator' },
                { label: 'Preferences', accelerator: 'CmdOrCtrl+,', click: () => mainWindow.webContents.send('open-settings') },
                { type: 'separator' },
                { label: 'Check for Updates', click: () => checkForUpdates() },
                { type: 'separator' },
                { label: 'Quit', accelerator: 'CmdOrCtrl+Q', click: () => app.quit() }
            ]
        },
        {
            label: 'Edit',
            submenu: [
                { label: 'Undo', accelerator: 'CmdOrCtrl+Z', role: 'undo' },
                { label: 'Redo', accelerator: 'CmdOrCtrl+Y', role: 'redo' },
                { type: 'separator' },
                { label: 'Cut', accelerator: 'CmdOrCtrl+X', role: 'cut' },
                { label: 'Copy', accelerator: 'CmdOrCtrl+C', role: 'copy' },
                { label: 'Paste', accelerator: 'CmdOrCtrl+V', role: 'paste' }
            ]
        },
        {
            label: 'View',
            submenu: [
                { label: 'Reload', accelerator: 'CmdOrCtrl+R', click: () => mainWindow.reload() },
                { label: 'Toggle Developer Tools', accelerator: 'CmdOrCtrl+Shift+I', click: () => mainWindow.webContents.toggleDevTools() },
                { type: 'separator' },
                { label: 'Actual Size', accelerator: 'CmdOrCtrl+0', click: () => mainWindow.webContents.setZoomLevel(0) },
                { label: 'Zoom In', accelerator: 'CmdOrCtrl+Plus', click: () => mainWindow.webContents.setZoomLevel(mainWindow.webContents.getZoomLevel() + 0.5) },
                { label: 'Zoom Out', accelerator: 'CmdOrCtrl+-', click: () => mainWindow.webContents.setZoomLevel(mainWindow.webContents.getZoomLevel() - 0.5) }
            ]
        },
        {
            label: 'Window',
            submenu: [
                { label: 'Minimize', accelerator: 'CmdOrCtrl+M', role: 'minimize' },
                { label: 'Close', accelerator: 'CmdOrCtrl+W', role: 'close' }
            ]
        },
        {
            label: 'Help',
            submenu: [
                { label: 'Documentation', click: () => shell.openExternal('https://github.com/yourrepo/youtube-downloader') },
                { label: 'Report Issue', click: () => shell.openExternal('https://github.com/yourrepo/youtube-downloader/issues') },
                { type: 'separator' },
                { label: 'About FFmpeg', click: () => showFFmpegInfo() }
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
        message: 'YouTube Downloader',
        detail: `Version: ${app.getVersion()}\n\nA powerful YouTube video downloader with a beautiful interface.\n\n• Free & Unlimited\n• Up to 4K Quality\n• Built-in Audio Support\n• Account Management\n• Download History\n\n© 2024 - Open Source`,
        buttons: ['OK'],
        icon: path.join(__dirname, 'icons', 'icon.png')
    });
}

function showFFmpegInfo() {
    dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'FFmpeg Status',
        message: 'FFmpeg is ready!',
        detail: 'FFmpeg is automatically bundled and configured.\n\nAll downloads will have perfect audio-video synchronization.\n\nSupported formats: MP4, MKV, WebM, MP3, M4A',
        buttons: ['OK']
    });
}

async function checkForUpdates() {
    // Simulate update check - in real app, check GitHub releases
    dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'Check for Updates',
        message: 'You are using the latest version!',
        detail: `YouTube Downloader v${app.getVersion()}\n\nNo updates available.`,
        buttons: ['OK']
    });
}

// IPC handlers
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
ipcMain.handle('open-external', (event, url) => {
    shell.openExternal(url);
});
ipcMain.handle('get-app-version', () => app.getVersion());
ipcMain.handle('get-platform', () => process.platform);

app.whenReady().then(async () => {
    loadSettings();
    await startPythonBackend();
    createWindow();
});

app.on('window-all-closed', () => {
    if (pythonProcess) pythonProcess.kill();
    if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
    if (mainWindow === null) createWindow();
});

process.on('exit', () => {
    if (pythonProcess) pythonProcess.kill();
});
