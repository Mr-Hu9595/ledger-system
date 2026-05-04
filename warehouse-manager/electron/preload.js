const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // 调用后端API
  callAPI: (endpoint, method, data) => {
    return fetch(`http://localhost:8000${endpoint}`, {
      method: method || 'GET',
      headers: { 'Content-Type': 'application/json' },
      body: data ? JSON.stringify(data) : undefined
    }).then(res => res.json());
  },

  // 打开文件对话框
  openFileDialog: () => ipcRenderer.invoke('dialog:openFile'),

  // 保存文件对话框
  saveFileDialog: () => ipcRenderer.invoke('dialog:saveFile')
});