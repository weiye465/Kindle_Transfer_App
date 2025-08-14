// ==UserScript==
// @name         SCYS文章转PDF工具
// @namespace    http://tampermonkey.net/
// @version      1.0.0
// @description  将SCYS网站的文章转换为PDF格式下载
// @author       Your Name
// @match        https://scys.com/articleDetail/*
// @match        https://*.scys.com/articleDetail/*
// @grant        GM_addStyle
// @require      https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js
// @require      https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js
// @run-at       document-end
// ==/UserScript==

(function() {
    'use strict';
    
    console.log('🚀 SCYS文章转PDF插件已加载');
    console.log('📍 当前页面URL:', window.location.href);

    // 添加样式
    GM_addStyle(`
        .pdf-convert-btn {
            position: fixed;
            top: 100px;
            right: 20px;
            z-index: 9999;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .pdf-convert-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        
        .pdf-convert-btn:active {
            transform: translateY(0);
        }
        
        .pdf-convert-btn.loading {
            background: #6c757d;
            cursor: not-allowed;
            opacity: 0.8;
        }
        
        .pdf-convert-btn svg {
            width: 18px;
            height: 18px;
        }
        
        .pdf-progress {
            position: fixed;
            top: 160px;
            right: 20px;
            width: 200px;
            background: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            z-index: 9998;
            display: none;
        }
        
        .pdf-progress.show {
            display: block;
        }
        
        .pdf-progress-bar {
            width: 100%;
            height: 6px;
            background: #e9ecef;
            border-radius: 3px;
            overflow: hidden;
            margin-top: 10px;
        }
        
        .pdf-progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.3s ease;
        }
        
        .pdf-progress-text {
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }
    `);

    // 创建转换按钮
    function createConvertButton() {
        console.log('📌 开始创建PDF转换按钮');
        const button = document.createElement('button');
        button.className = 'pdf-convert-btn';
        button.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            转换为PDF
        `;
        
        // 创建进度条
        const progressDiv = document.createElement('div');
        progressDiv.className = 'pdf-progress';
        progressDiv.innerHTML = `
            <div class="pdf-progress-text">正在生成PDF...</div>
            <div class="pdf-progress-bar">
                <div class="pdf-progress-fill"></div>
            </div>
        `;
        
        document.body.appendChild(button);
        document.body.appendChild(progressDiv);
        
        button.addEventListener('click', handleConvert);
        console.log('✅ PDF转换按钮创建成功');
    }

    // 处理转换
    async function handleConvert() {
        console.log('🔄 开始PDF转换流程');
        const button = document.querySelector('.pdf-convert-btn');
        const progressDiv = document.querySelector('.pdf-progress');
        const progressFill = document.querySelector('.pdf-progress-fill');
        const progressText = document.querySelector('.pdf-progress-text');
        
        // 检查是否正在处理
        if (button.classList.contains('loading')) {
            console.log('⚠️ 转换正在进行中，忽略重复点击');
            return;
        }
        
        try {
            // 开始处理
            button.classList.add('loading');
            button.innerHTML = `
                <svg class="animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
                    <path d="M12 2a10 10 0 0 1 10 10" stroke-opacity="0.75"></path>
                </svg>
                处理中...
            `;
            progressDiv.classList.add('show');
            
            // 获取文章内容
            progressText.textContent = '正在提取文章内容...';
            progressFill.style.width = '20%';
            
            const articleData = extractArticleContent();
            if (!articleData) {
                throw new Error('无法提取文章内容');
            }
            console.log('📄 文章内容提取成功:', {
                title: articleData.title,
                hasContent: !!articleData.content
            });
            
            progressText.textContent = '正在准备PDF内容...';
            progressFill.style.width = '40%';
            
            // 创建临时容器用于渲染
            const tempContainer = createTempContainer(articleData);
            document.body.appendChild(tempContainer);
            console.log('📦 临时容器已创建并添加到页面');
            
            // 等待图片加载
            console.log('🖼️ 开始等待图片加载...');
            await waitForImages(tempContainer);
            console.log('✅ 所有图片加载完成');
            
            progressText.textContent = '正在生成PDF...';
            progressFill.style.width = '60%';
            
            // 使用html2canvas截图
            console.log('📸 开始使用html2canvas生成截图...');
            
            // 确保容器可见
            tempContainer.style.left = '0';
            tempContainer.style.top = '0';
            tempContainer.style.visibility = 'visible';
            tempContainer.style.opacity = '1';
            
            const canvas = await html2canvas(tempContainer, {
                scale: 2,
                useCORS: true,
                allowTaint: true,
                logging: true,
                backgroundColor: '#ffffff',
                width: 794,
                windowWidth: 794,
                onclone: (clonedDoc) => {
                    // 处理克隆文档中的样式
                    const clonedElement = clonedDoc.querySelector('#pdf-temp-container');
                    if (clonedElement) {
                        clonedElement.style.position = 'static';
                        clonedElement.style.width = '794px'; // A4宽度
                        clonedElement.style.padding = '40px';
                        clonedElement.style.fontSize = '14px';
                        clonedElement.style.lineHeight = '1.6';
                    }
                }
            });
            console.log('✅ Canvas生成成功:', {
                width: canvas.width,
                height: canvas.height
            });
            
            progressText.textContent = '正在创建PDF文件...';
            progressFill.style.width = '80%';
            
            // 创建PDF
            console.log('📝 开始创建PDF文档...');
            const pdf = new window.jspdf.jsPDF({
                orientation: 'portrait',
                unit: 'mm',
                format: 'a4'
            });
            
            // 计算尺寸
            const imgWidth = 210; // A4宽度（mm）
            const imgHeight = (canvas.height * imgWidth) / canvas.width;
            const pageHeight = 297; // A4高度（mm）
            console.log('📐 PDF尺寸计算:', {
                imgWidth,
                imgHeight,
                pageHeight,
                totalPages: Math.ceil(imgHeight / pageHeight)
            });
            
            let heightLeft = imgHeight;
            let position = 0;
            
            // 添加第一页
            pdf.addImage(
                canvas.toDataURL('image/jpeg', 0.95),
                'JPEG',
                0,
                position,
                imgWidth,
                imgHeight
            );
            heightLeft -= pageHeight;
            
            // 添加额外页面（如果需要）
            let pageCount = 1;
            while (heightLeft > 0) {
                position = heightLeft - imgHeight;
                pdf.addPage();
                pageCount++;
                console.log(`📄 添加第 ${pageCount} 页，position: ${position}`);
                pdf.addImage(
                    canvas.toDataURL('image/jpeg', 0.95),
                    'JPEG',
                    0,
                    position,
                    imgWidth,
                    imgHeight
                );
                heightLeft -= pageHeight;
            }
            
            progressText.textContent = '正在保存PDF...';
            progressFill.style.width = '100%';
            
            // 保存PDF
            const fileName = `${articleData.title || '文章'}_${new Date().getTime()}.pdf`;
            console.log('💾 保存PDF文件:', fileName);
            pdf.save(fileName);
            console.log('✅ PDF保存成功');
            
            // 清理
            if (tempContainer && tempContainer.parentNode) {
                document.body.removeChild(tempContainer);
                console.log('🧹 临时容器已清理');
            }
            
            // 完成
            console.log('🎉 PDF转换流程完成');
            setTimeout(() => {
                progressDiv.classList.remove('show');
                progressFill.style.width = '0%';
                button.classList.remove('loading');
                button.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                        <polyline points="10 9 9 9 8 9"></polyline>
                    </svg>
                    转换为PDF
                `;
            }, 1000);
            
        } catch (error) {
            console.error('❌ PDF转换失败:', error);
            console.error('错误堆栈:', error.stack);
            
            // 清理临时容器
            const tempContainer = document.querySelector('#pdf-temp-container');
            if (tempContainer) {
                document.body.removeChild(tempContainer);
            }
            
            alert('PDF转换失败: ' + error.message);
            
            // 重置按钮
            progressDiv.classList.remove('show');
            button.classList.remove('loading');
            button.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                    <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
                转换为PDF
            `;
        }
    }

    // 提取文章内容
    function extractArticleContent() {
        console.log('🔍 开始提取文章内容...');
        const titleElement = document.querySelector('.post-title');
        const contentElement = document.querySelector('.post-content');
        
        console.log('查找结果:', {
            titleFound: !!titleElement,
            contentFound: !!contentElement
        });
        
        if (!titleElement || !contentElement) {
            console.error('❌ 找不到文章标题或内容元素');
            console.error('页面DOM结构:', {
                hasPostTitle: !!document.querySelector('.post-title'),
                hasPostContent: !!document.querySelector('.post-content'),
                allClasses: [...new Set([...document.querySelectorAll('[class]')].map(el => el.className))]
            });
            return null;
        }
        
        const result = {
            title: titleElement.textContent.trim(),
            content: contentElement.cloneNode(true)
        };
        console.log('✅ 文章内容提取成功:', {
            titleLength: result.title.length,
            contentLength: result.content.textContent.length
        });
        return result;
    }

    // 创建临时容器
    function createTempContainer(articleData) {
        console.log('🔨 创建临时PDF渲染容器...');
        const container = document.createElement('div');
        container.id = 'pdf-temp-container';
        container.style.cssText = `
            position: absolute;
            left: 0;
            top: 0;
            width: 794px;
            background: white;
            padding: 40px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: #333;
            line-height: 1.6;
            z-index: 999999;
            visibility: visible;
            opacity: 1;
        `;
        
        // 添加标题
        const titleEl = document.createElement('h1');
        titleEl.style.cssText = `
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 30px;
            color: #1a1a1a;
            line-height: 1.3;
            padding-bottom: 15px;
            border-bottom: 2px solid #e0e0e0;
        `;
        titleEl.textContent = articleData.title;
        container.appendChild(titleEl);
        
        // 添加内容
        const contentEl = articleData.content;
        contentEl.style.cssText = `
            font-size: 14px;
            line-height: 1.8;
            color: #333;
        `;
        
        // 处理内容中的图片
        const images = contentEl.querySelectorAll('img');
        console.log(`🖼️ 找到 ${images.length} 张图片`);
        images.forEach(img => {
            img.style.cssText = `
                max-width: 100%;
                height: auto;
                display: block;
                margin: 20px auto;
            `;
        });
        
        // 处理段落
        const paragraphs = contentEl.querySelectorAll('p');
        paragraphs.forEach(p => {
            p.style.cssText = `
                margin: 15px 0;
                text-align: justify;
            `;
        });
        
        // 处理标题
        contentEl.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(h => {
            h.style.cssText = `
                margin: 20px 0 10px;
                font-weight: bold;
            `;
        });
        
        container.appendChild(contentEl);
        
        console.log('✅ 临时容器创建完成');
        return container;
    }

    // 等待图片加载
    function waitForImages(container) {
        const images = container.querySelectorAll('img');
        console.log(`⏳ 等待 ${images.length} 张图片加载...`);
        const promises = Array.from(images).map(img => {
            return new Promise((resolve) => {
                if (img.complete) {
                    console.log('✅ 图片已加载:', img.src);
                    resolve();
                } else {
                    img.onload = () => {
                        console.log('✅ 图片加载成功:', img.src);
                        resolve();
                    };
                    img.onerror = () => {
                        console.warn('⚠️ 图片加载失败:', img.src);
                        resolve();
                    }; // 即使加载失败也继续
                }
            });
        });
        
        return Promise.all(promises);
    }

    // 等待页面加载完成
    function init() {
        console.log('🎬 初始化PDF转换插件...');
        // 检查必要的元素是否存在
        let checkCount = 0;
        const checkElements = setInterval(() => {
            checkCount++;
            const hasTitle = document.querySelector('.post-title');
            const hasContent = document.querySelector('.post-content');
            
            console.log(`🔍 第 ${checkCount} 次检查元素:`, {
                hasTitle: !!hasTitle,
                hasContent: !!hasContent
            });
            
            if (hasTitle && hasContent) {
                clearInterval(checkElements);
                console.log('✅ 找到必要元素，开始创建按钮');
                createConvertButton();
            }
        }, 500);
        
        // 10秒后停止检查
        setTimeout(() => {
            clearInterval(checkElements);
            console.warn('⏱️ 10秒超时，停止检查元素');
        }, 10000);
    }

    // 启动
    console.log('📊 文档状态:', document.readyState);
    if (document.readyState === 'loading') {
        console.log('⏳ 等待DOM加载完成...');
        document.addEventListener('DOMContentLoaded', init);
    } else {
        console.log('✅ DOM已加载，直接初始化');
        init();
    }
})();