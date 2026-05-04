const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let serverProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  // 开发模式加载 Vite 开发服务器
  mainWindow.loadURL('http://localhost:5173');
  // 生产模式加载打包后的文件
  // mainWindow.loadFile(path.join(__dirname, '../client/dist/index.html'));

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startServer() {
  const isDev = process.env.NODE_ENV !== 'production';
  if (isDev) {
    serverProcess = spawn('python', ['-m', 'uvicorn', 'server.main:app', '--reload', '--port', '8000'], {
      cwd: path.join(__dirname, '../server'),
      shell: true
    });
    serverProcess.stdout.on('data', (data) => {
      console.log(`Server: ${data}`);
    });
  }
}

app.whenReady().then(() => {
  startServer();
  createWindow();
});

app.on('window-all-closed', () => {
  if (serverProcess) {
    serverProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});