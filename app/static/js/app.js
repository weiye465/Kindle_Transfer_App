// Kindle Transfer App - 前端JavaScript

let currentFile = null;

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    loadConfig();
    loadHistory();
    setupDragDrop();
    setupFileInput();
});

// 设置拖拽上传
function setupDragDrop() {
    const dropZone = document.getElementById('dropZone');
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
}

// 设置文件输入
function setupFileInput() {
    const fileInput = document.getElementById('fileInput');
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });
}

// 处理文件
function handleFile(file) {
    currentFile = file;
    
    // 显示文件信息
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileSize').textContent = (file.size / 1024 / 1024).toFixed(2) + ' MB';
    document.getElementById('fileInfo').classList.remove('hidden');
    
    // 显示通知
    showNotification('文件已选择，点击"发送到Kindle"开始处理', 'info');
}

// 处理并发送文件
async function processFile() {
    if (!currentFile) {
        showNotification('请先选择文件', 'error');
        return;
    }
    
    // 显示进度条
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressPercent = document.getElementById('progressPercent');
    
    progressContainer.classList.remove('hidden');
    
    try {
        // 上传文件
        progressText.textContent = '上传文件中...';
        updateProgress(30);
        
        const formData = new FormData();
        formData.append('file', currentFile);
        
        const response = await fetch('/api/process', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            updateProgress(100);
            progressText.textContent = '发送成功！';
            showNotification(result.message, 'success');
            
            // 刷新历史记录
            setTimeout(() => {
                loadHistory();
                resetUploadArea();
            }, 2000);
        } else {
            throw new Error(result.message);
        }
        
    } catch (error) {
        showNotification('处理失败: ' + error.message, 'error');
        progressContainer.classList.add('hidden');
    }
}

// 更新进度条
function updateProgress(percent) {
    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');
    
    progressBar.style.width = percent + '%';
    progressPercent.textContent = percent + '%';
}

// 重置上传区域
function resetUploadArea() {
    currentFile = null;
    document.getElementById('fileInfo').classList.add('hidden');
    document.getElementById('progressContainer').classList.add('hidden');
    document.getElementById('fileInput').value = '';
    updateProgress(0);
}

// 加载配置
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();
        
        // 更新显示
        document.getElementById('currentKindleEmail').textContent = config.kindle_email || '未配置';
        document.getElementById('currentSenderEmail').textContent = config.smtp_email || '未配置';
        document.getElementById('currentSmtpServer').textContent = config.smtp_server || '未配置';
        
        // 填充设置表单
        if (config.kindle_email) document.getElementById('kindleEmail').value = config.kindle_email;
        if (config.smtp_email) document.getElementById('smtpEmail').value = config.smtp_email;
        if (config.smtp_password) document.getElementById('smtpPassword').value = config.smtp_password;
        if (config.smtp_server) document.getElementById('smtpServer').value = config.smtp_server;
        if (config.smtp_port) document.getElementById('smtpPort').value = config.smtp_port;
        
    } catch (error) {
        console.error('加载配置失败:', error);
    }
}

// 加载历史记录
async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const history = await response.json();
        
        const historyList = document.getElementById('historyList');
        
        if (history.length === 0) {
            historyList.innerHTML = '<p class="text-gray-500 text-center py-4">暂无传输记录</p>';
        } else {
            historyList.innerHTML = history.map(item => `
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
                    <div class="flex items-center">
                        <i class="fas fa-file-alt text-gray-400 mr-3"></i>
                        <div>
                            <p class="text-sm font-medium text-gray-800">${item.name}</p>
                            <p class="text-xs text-gray-500">${item.time} · ${item.size} MB</p>
                        </div>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('加载历史失败:', error);
    }
}

// 显示设置模态框
function showSettings() {
    document.getElementById('settingsModal').classList.remove('hidden');
}

// 隐藏设置模态框
function hideSettings() {
    document.getElementById('settingsModal').classList.add('hidden');
}

// 保存设置
async function saveSettings() {
    const config = {
        kindle_email: document.getElementById('kindleEmail').value,
        smtp_email: document.getElementById('smtpEmail').value,
        smtp_password: document.getElementById('smtpPassword').value,
        smtp_server: document.getElementById('smtpServer').value || 'smtp.163.com',
        smtp_port: document.getElementById('smtpPort').value || '465'
    };
    
    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('配置保存成功', 'success');
            hideSettings();
            loadConfig();
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        showNotification('保存失败: ' + error.message, 'error');
    }
}

// 显示通知
function showNotification(message, type = 'info') {
    const colors = {
        'success': 'bg-green-500',
        'error': 'bg-red-500',
        'info': 'bg-blue-500',
        'warning': 'bg-yellow-500'
    };
    
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50 fade-in`;
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'times-circle' : 'info-circle'} mr-2"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}