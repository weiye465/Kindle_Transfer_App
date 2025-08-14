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
    
    const startTime = Date.now();
    console.log('=== 开始上传文件 ===');
    console.log(`文件名: ${currentFile.name}`);
    console.log(`文件大小: ${(currentFile.size / 1024 / 1024).toFixed(2)} MB`);
    console.log(`文件类型: ${currentFile.type}`);
    
    try {
        // 准备上传
        progressText.textContent = '准备上传...';
        updateProgress(10);
        
        const formData = new FormData();
        formData.append('file', currentFile);
        
        // 创建XMLHttpRequest以监控上传进度
        const xhr = new XMLHttpRequest();
        
        // 监听上传进度
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 100);
                const uploadSpeed = (e.loaded / 1024 / 1024) / ((Date.now() - startTime) / 1000);
                
                console.log(`上传进度: ${percentComplete}%, 速度: ${uploadSpeed.toFixed(2)} MB/s`);
                
                // 上传阶段占60%进度
                const displayPercent = Math.round(percentComplete * 0.6);
                updateProgress(displayPercent);
                progressText.textContent = `上传中... ${percentComplete}% (${uploadSpeed.toFixed(1)} MB/s)`;
            }
        });
        
        // 监听状态变化
        xhr.onreadystatechange = function() {
            console.log(`XHR状态: readyState=${xhr.readyState}, status=${xhr.status}`);
            
            if (xhr.readyState === 4) {
                const uploadTime = (Date.now() - startTime) / 1000;
                console.log(`上传完成，耗时: ${uploadTime.toFixed(2)}秒`);
                
                if (xhr.status === 200) {
                    try {
                        const result = JSON.parse(xhr.responseText);
                        console.log('服务器响应:', result);
                        
                        if (result.success) {
                            updateProgress(100);
                            progressText.textContent = '发送成功！';
                            showNotification(result.message, 'success');
                            
                            if (result.details && result.details.processing_time) {
                                console.log(`服务器处理时间: ${result.details.processing_time}`);
                            }
                            
                            // 刷新历史记录
                            setTimeout(() => {
                                loadHistory();
                                resetUploadArea();
                            }, 2000);
                        } else {
                            throw new Error(result.message);
                        }
                    } catch (e) {
                        console.error('解析响应失败:', e);
                        throw new Error('服务器响应格式错误');
                    }
                } else {
                    console.error(`上传失败: HTTP ${xhr.status}`);
                    throw new Error(`上传失败: HTTP ${xhr.status}`);
                }
            }
        };
        
        // 监听错误
        xhr.onerror = function() {
            const uploadTime = (Date.now() - startTime) / 1000;
            console.error(`网络错误，耗时: ${uploadTime.toFixed(2)}秒`);
            showNotification('网络连接失败，请检查网络', 'error');
            progressContainer.classList.add('hidden');
        };
        
        // 监听超时
        xhr.ontimeout = function() {
            const uploadTime = (Date.now() - startTime) / 1000;
            console.error(`请求超时，耗时: ${uploadTime.toFixed(2)}秒`);
            showNotification('上传超时，请重试', 'error');
            progressContainer.classList.add('hidden');
        };
        
        // 设置超时（5分钟）
        xhr.timeout = 300000;
        
        // 开始上传
        console.log('开始发送请求...');
        progressText.textContent = '连接服务器...';
        updateProgress(5);
        
        xhr.open('POST', '/api/process', true);
        xhr.send(formData);
        
    } catch (error) {
        console.error('处理失败:', error);
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