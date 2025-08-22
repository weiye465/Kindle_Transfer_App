// ==UserScript==
// @name         SCYS文章转PDF工具V3 - 文本版
// @namespace    http://tampermonkey.net/
// @version      3.0.0
// @description  将SCYS网站的文章转换为文本型PDF格式，优化Kindle阅读体验
// @author       Your Name
// @match        https://scys.com/articleDetail/*
// @match        https://*.scys.com/articleDetail/*
// @grant        GM_addStyle
// @grant        GM_xmlhttpRequest
// @require      https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.2.7/pdfmake.min.js
// @require      https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.2.7/vfs_fonts.js
// @run-at       document-end
// ==/UserScript==

(function() {
    'use strict';
    
    console.log('🚀 SCYS文章转PDF插件V3（文本版）已加载');
    console.log('📍 当前页面URL:', window.location.href);
    console.log('📊 文档状态:', document.readyState);

    // 加载中文字体资源
    const FONT_URL = 'https://cdn.jsdelivr.net/gh/kaienfr/Font/font/simhei/simhei-normal.js';
    
    // 添加样式
    GM_addStyle(`
        .pdf-convert-btn-v3 {
            position: fixed;
            top: 100px;
            right: 20px;
            z-index: 9999;
            background: linear-gradient(135deg, #00b4d8 0%, #0077b6 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            box-shadow: 0 4px 15px rgba(0, 119, 182, 0.4);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .pdf-convert-btn-v3:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 119, 182, 0.6);
        }
        
        .pdf-convert-btn-v3.loading {
            background: #6c757d;
            cursor: not-allowed;
            opacity: 0.8;
        }
        
        .pdf-convert-btn-v3 svg {
            width: 16px;
            height: 16px;
        }
        
        .pdf-progress-v3 {
            position: fixed;
            top: 160px;
            right: 20px;
            width: 250px;
            background: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            z-index: 9998;
            display: none;
        }
        
        .pdf-progress-v3.show {
            display: block;
        }
        
        .pdf-progress-text-v3 {
            font-size: 14px;
            color: #333;
            margin-bottom: 10px;
        }
        
        .pdf-progress-bar-v3 {
            width: 100%;
            height: 6px;
            background: #e9ecef;
            border-radius: 3px;
            overflow: hidden;
        }
        
        .pdf-progress-fill-v3 {
            height: 100%;
            background: linear-gradient(90deg, #00b4d8, #0077b6);
            width: 0%;
            transition: width 0.3s ease;
        }
        
        .pdf-status-v3 {
            font-size: 12px;
            color: #666;
            margin-top: 8px;
        }
    `);

    // 创建按钮
    function createButton() {
        console.log('📌 开始创建PDF文本版转换按钮...');
        const button = document.createElement('button');
        button.className = 'pdf-convert-btn-v3';
        button.innerHTML = `
            <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
            </svg>
            转换为文本PDF
        `;
        
        const progressDiv = document.createElement('div');
        progressDiv.className = 'pdf-progress-v3';
        progressDiv.innerHTML = `
            <div class="pdf-progress-text-v3">正在生成文本PDF...</div>
            <div class="pdf-progress-bar-v3">
                <div class="pdf-progress-fill-v3"></div>
            </div>
            <div class="pdf-status-v3"></div>
        `;
        
        document.body.appendChild(button);
        document.body.appendChild(progressDiv);
        
        button.addEventListener('click', handleConvert);
        console.log('✅ PDF文本版转换按钮创建成功');
    }

    // 存储当前使用的字体名称
    let currentChineseFontName = 'helvetica';  // 默认字体
    
    // 加载中文字体 - 简化版本，只使用确定可用的方案
    async function loadChineseFont(pdf) {
        console.log('🔤 加载中文字体...');
        
        try {
            // 方案1：使用已知可用的SimHei字体
            console.log('📥 尝试加载黑体字体...');
            
            // 先尝试CDN版本
            const fontUrl = 'https://cdn.jsdelivr.net/gh/kaienfr/Font@master/font/simhei/simhei-normal.js';
            
            const response = await new Promise((resolve, reject) => {
                GM_xmlhttpRequest({
                    method: 'GET',
                    url: fontUrl,
                    timeout: 10000,
                    onload: resolve,
                    onerror: reject,
                    ontimeout: () => reject(new Error('Timeout'))
                });
            });
            
            if (response.status === 200) {
                // 执行字体脚本
                const scriptContent = response.responseText;
                
                // 创建一个函数来安全执行字体代码
                const loadFontCode = new Function('window', 'jsPDF', scriptContent + '; return window.font;');
                const fontData = loadFontCode(window, window.jspdf);
                
                if (fontData && fontData.SimHei) {
                    // 添加字体到PDF
                    const base64Font = fontData.SimHei;
                    pdf.addFileToVFS('SimHei.ttf', base64Font);
                    pdf.addFont('SimHei.ttf', 'SimHei', 'normal');
                    
                    // 设置为当前字体
                    pdf.setFont('SimHei');
                    currentChineseFontName = 'SimHei';
                    
                    console.log('✅ 黑体字体加载成功');
                    return;
                }
            }
            
        } catch (error) {
            console.error('❌ 主字体加载失败:', error);
        }
        
        // 方案2：尝试备用URL
        try {
            console.log('📥 尝试备用字体源...');
            
            const backupUrl = 'https://raw.githubusercontent.com/kaienfr/Font/master/font/simhei/simhei-normal.js';
            
            const response = await new Promise((resolve, reject) => {
                GM_xmlhttpRequest({
                    method: 'GET',
                    url: backupUrl,
                    timeout: 10000,
                    onload: resolve,
                    onerror: reject,
                    ontimeout: () => reject(new Error('Timeout'))
                });
            });
            
            if (response.status === 200) {
                const scriptContent = response.responseText;
                const loadFontCode = new Function('window', 'jsPDF', scriptContent + '; return window.font;');
                const fontData = loadFontCode(window, window.jspdf);
                
                if (fontData && fontData.SimHei) {
                    const base64Font = fontData.SimHei;
                    pdf.addFileToVFS('SimHei.ttf', base64Font);
                    pdf.addFont('SimHei.ttf', 'SimHei', 'normal');
                    pdf.setFont('SimHei');
                    currentChineseFontName = 'SimHei';
                    
                    console.log('✅ 备用字体加载成功');
                    return;
                }
            }
            
        } catch (error) {
            console.error('❌ 备用字体加载失败:', error);
        }
        
        // 所有方案都失败，使用默认字体
        console.warn('⚠️ 所有中文字体加载失败，将使用默认字体（可能显示乱码）');
        console.warn('💡 建议：检查网络连接或尝试刷新页面');
        currentChineseFontName = 'helvetica';
    }
    
    
    
    // 提取纯文本内容
    function extractTextContent(element) {
        const walker = document.createTreeWalker(
            element,
            NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT,
            {
                acceptNode: function(node) {
                    // 跳过script和style标签
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        if (node.tagName === 'SCRIPT' || node.tagName === 'STYLE') {
                            return NodeFilter.FILTER_REJECT;
                        }
                        return NodeFilter.FILTER_SKIP;
                    }
                    // 跳过空白文本
                    if (node.nodeValue.trim() === '') {
                        return NodeFilter.FILTER_REJECT;
                    }
                    return NodeFilter.FILTER_ACCEPT;
                }
            }
        );

        const content = [];
        let currentNode;
        let currentParagraph = '';
        
        while (currentNode = walker.nextNode()) {
            const parent = currentNode.parentNode;
            const tagName = parent.tagName ? parent.tagName.toLowerCase() : '';
            const text = currentNode.nodeValue.trim();
            
            if (!text) continue;
            
            // 处理块级元素
            if (['p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote'].includes(tagName)) {
                if (currentParagraph) {
                    content.push({
                        type: 'paragraph',
                        text: currentParagraph
                    });
                    currentParagraph = '';
                }
                
                // 处理标题
                if (tagName.startsWith('h')) {
                    content.push({
                        type: 'heading',
                        level: parseInt(tagName[1]),
                        text: text
                    });
                } 
                // 处理列表项
                else if (tagName === 'li') {
                    content.push({
                        type: 'list-item',
                        text: '• ' + text
                    });
                }
                // 处理引用
                else if (tagName === 'blockquote') {
                    content.push({
                        type: 'quote',
                        text: text
                    });
                }
                // 普通段落
                else {
                    currentParagraph = text;
                }
            } else {
                // 内联文本，添加到当前段落
                currentParagraph += (currentParagraph ? ' ' : '') + text;
            }
        }
        
        // 添加最后一个段落
        if (currentParagraph) {
            content.push({
                type: 'paragraph',
                text: currentParagraph
            });
        }
        
        return content;
    }

    // 处理文本内容并生成PDF
    async function generateTextPDF(title, contentElements) {
        console.log('📝 开始生成文本型PDF...');
        
        // 创建PDF文档
        const pdf = new window.jspdf.jsPDF({
            orientation: 'portrait',
            unit: 'mm',
            format: 'a4'
        });
        
        // PDF尺寸常量
        const pageWidth = 210;
        const pageHeight = 297;
        const margin = {
            top: 25,
            bottom: 25,
            left: 20,
            right: 20
        };
        const contentWidth = pageWidth - margin.left - margin.right;
        const contentHeight = pageHeight - margin.top - margin.bottom;
        
        // 添加中文字体支持
        await loadChineseFont(pdf);
        
        // 字体设置 - 使用添加的中文字体
        // 根据实际加载的字体自动设置（已在 loadChineseFont 中设置）
        
        // 当前位置
        let currentY = margin.top;
        let pageNumber = 1;
        
        // 添加页眉（标题）
        function addHeader() {
            pdf.setFontSize(10);
            pdf.setTextColor(150, 150, 150);
            pdf.text(title.substring(0, 50) + (title.length > 50 ? '...' : ''), margin.left, 15);
            pdf.text(`第 ${pageNumber} 页`, pageWidth - margin.right - 20, 15);
            pdf.setTextColor(0, 0, 0);
        }
        
        // 检查是否需要新页
        function checkNewPage(requiredSpace = 10) {
            if (currentY + requiredSpace > pageHeight - margin.bottom) {
                pdf.addPage();
                pageNumber++;
                currentY = margin.top;
                addHeader();
                return true;
            }
            return false;
        }
        
        // 添加文本并自动换行
        function addWrappedText(text, fontSize, isBold = false, indent = 0) {
            pdf.setFontSize(fontSize);
            if (isBold) {
                // 使用当前加载的中文字体
                pdf.setFont(currentChineseFontName, 'bold');
            } else {
                pdf.setFont(currentChineseFontName, 'normal');
            }
            
            const lines = pdf.splitTextToSize(text, contentWidth - indent);
            const lineHeight = fontSize * 0.5;
            
            for (let i = 0; i < lines.length; i++) {
                checkNewPage(lineHeight);
                pdf.text(lines[i], margin.left + indent, currentY);
                currentY += lineHeight;
            }
            
            // 段落间距
            currentY += lineHeight * 0.5;
        }
        
        // 添加第一页标题
        addHeader();
        pdf.setFontSize(18);
        pdf.setFont(currentChineseFontName, 'bold');
        const titleLines = pdf.splitTextToSize(title, contentWidth);
        titleLines.forEach(line => {
            pdf.text(line, margin.left, currentY);
            currentY += 10;
        });
        
        // 添加分隔线
        currentY += 5;
        pdf.setDrawColor(200, 200, 200);
        pdf.line(margin.left, currentY, pageWidth - margin.right, currentY);
        currentY += 10;
        
        // 添加日期
        pdf.setFontSize(10);
        pdf.setTextColor(100, 100, 100);
        pdf.text(`生成日期：${new Date().toLocaleDateString('zh-CN')}`, margin.left, currentY);
        pdf.setTextColor(0, 0, 0);
        currentY += 15;
        
        // 处理内容
        console.log(`📄 开始处理 ${contentElements.length} 个内容块`);
        
        for (let i = 0; i < contentElements.length; i++) {
            const element = contentElements[i];
            
            switch (element.type) {
                case 'heading':
                    // 标题样式
                    const headingSize = 16 - (element.level - 1) * 2;
                    checkNewPage(headingSize * 0.8);
                    addWrappedText(element.text, headingSize, true);
                    break;
                    
                case 'paragraph':
                    // 段落文本
                    addWrappedText(element.text, 11, false);
                    break;
                    
                case 'list-item':
                    // 列表项
                    addWrappedText(element.text, 11, false, 5);
                    break;
                    
                case 'quote':
                    // 引用文本
                    pdf.setTextColor(80, 80, 80);
                    pdf.setFont(currentChineseFontName, 'italic');
                    addWrappedText('「' + element.text + '」', 10, false, 10);
                    pdf.setTextColor(0, 0, 0);
                    pdf.setFont(currentChineseFontName, 'normal');
                    break;
                    
                default:
                    // 默认文本
                    addWrappedText(element.text, 11, false);
            }
            
            // 更新进度
            if (i % 10 === 0) {
                updateProgress(30 + (i / contentElements.length) * 60, 
                    `处理内容: ${i}/${contentElements.length}`);
            }
        }
        
        // 添加最后一页的页脚
        currentY = pageHeight - margin.bottom + 10;
        pdf.setFontSize(8);
        pdf.setTextColor(150, 150, 150);
        pdf.text('由 SCYS文章转PDF工具 V3 生成', pageWidth / 2, currentY, { align: 'center' });
        
        console.log(`✅ PDF生成完成，共 ${pageNumber} 页`);
        return pdf;
    }

    // 更新进度
    function updateProgress(percent, status = '') {
        const progressFill = document.querySelector('.pdf-progress-fill-v3');
        const statusDiv = document.querySelector('.pdf-status-v3');
        
        if (progressFill) {
            progressFill.style.width = percent + '%';
        }
        
        if (statusDiv && status) {
            statusDiv.textContent = status;
        }
    }

    // 主转换函数
    async function handleConvert() {
        console.log('🔄 开始文本PDF转换流程...');
        console.time('PDF转换总耗时');
        
        const button = document.querySelector('.pdf-convert-btn-v3');
        const progressDiv = document.querySelector('.pdf-progress-v3');
        const progressText = document.querySelector('.pdf-progress-text-v3');
        
        if (button.classList.contains('loading')) {
            console.log('⚠️ 转换正在进行中，忽略重复点击');
            return;
        }
        
        try {
            button.classList.add('loading');
            button.innerHTML = `
                <svg viewBox="0 0 24 24" fill="currentColor" class="spinning">
                    <path d="M12,4V2A10,10 0 0,0 2,12H4A8,8 0 0,1 12,4Z"/>
                </svg>
                处理中...
            `;
            progressDiv.classList.add('show');
            updateProgress(10, '查找文章内容...');
            
            // 获取文章元素（使用之前找到的元素或重新查找）
            let titleElement = window.SCYS_PDF_SELECTORS?.title;
            let contentElement = window.SCYS_PDF_SELECTORS?.content;
            
            // 如果之前没有保存，重新查找
            if (!contentElement) {
                const contentSelectors = [
                    '.post-content',
                    '.article-content',
                    '.content',
                    '.detail-content',
                    '[class*="content"]',
                    'article',
                    'main'
                ];
                
                for (const selector of contentSelectors) {
                    contentElement = document.querySelector(selector);
                    if (contentElement && contentElement.textContent.trim().length > 100) {
                        break;
                    }
                }
            }
            
            if (!titleElement) {
                const titleSelectors = [
                    '.post-title',
                    '.article-title',
                    'h1.title',
                    'h1',
                    '[class*="title"]',
                    '.content-title',
                    '.detail-title'
                ];
                
                for (const selector of titleSelectors) {
                    titleElement = document.querySelector(selector);
                    if (titleElement && titleElement.textContent.trim()) {
                        break;
                    }
                }
            }
            
            console.log('🔍 查找文章元素...', {
                titleFound: !!titleElement,
                contentFound: !!contentElement
            });
            
            if (!contentElement) {
                throw new Error('找不到文章内容，请确保在文章页面使用此工具');
            }
            
            // 如果没有找到标题，使用默认标题或从URL提取
            const title = titleElement ? 
                titleElement.textContent.trim() : 
                document.title || '未命名文档';
            console.log('📄 文章标题:', title);
            
            updateProgress(20, '提取文本内容...');
            
            // 提取结构化内容
            const contentElements = extractTextContent(contentElement);
            console.log(`📊 提取到 ${contentElements.length} 个内容块`);
            
            // 统计内容
            const stats = {
                paragraphs: contentElements.filter(e => e.type === 'paragraph').length,
                headings: contentElements.filter(e => e.type === 'heading').length,
                lists: contentElements.filter(e => e.type === 'list-item').length,
                quotes: contentElements.filter(e => e.type === 'quote').length,
                totalChars: contentElements.reduce((sum, e) => sum + e.text.length, 0)
            };
            
            console.log('📈 内容统计:', stats);
            progressText.textContent = `生成文本PDF (约${Math.ceil(stats.totalChars / 500)}页)...`;
            
            updateProgress(30, '生成PDF文档...');
            
            // 生成PDF
            const pdf = await generateTextPDF(title, contentElements);
            
            updateProgress(90, '准备下载...');
            
            // 保存PDF
            const fileName = `${title.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_')}_文本版_${Date.now()}.pdf`;
            console.log('💾 保存PDF文件:', fileName);
            pdf.save(fileName);
            
            updateProgress(100, '转换完成！');
            console.log('✅ 文本PDF保存成功!');
            console.timeEnd('PDF转换总耗时');
            
            // 显示完成信息
            progressText.textContent = '文本PDF生成成功！';
            
            // 恢复按钮
            setTimeout(() => {
                progressDiv.classList.remove('show');
                updateProgress(0, '');
                button.classList.remove('loading');
                button.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                    </svg>
                    转换为文本PDF
                `;
            }, 2000);
            
        } catch (error) {
            console.error('❌ PDF转换失败:', error);
            console.error('错误堆栈:', error.stack);
            console.timeEnd('PDF转换总耗时');
            
            alert('PDF转换失败: ' + error.message);
            
            // 恢复按钮
            progressDiv.classList.remove('show');
            button.classList.remove('loading');
            button.innerHTML = `
                <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                </svg>
                转换为文本PDF
            `;
        }
    }

    // 添加旋转动画
    GM_addStyle(`
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        .spinning {
            animation: spin 1s linear infinite;
        }
    `);

    // 初始化
    function init() {
        console.log('🎬 初始化文本PDF转换插件...');
        
        // 检查是否已有其他版本的按钮
        const existingButtons = document.querySelectorAll('.pdf-convert-btn, .pdf-convert-btn-v3');
        existingButtons.forEach(btn => {
            if (btn.className !== 'pdf-convert-btn-v3') {
                console.log('🔄 移除旧版本按钮');
                btn.remove();
            }
        });
        
        let checkCount = 0;
        const checkInterval = setInterval(() => {
            checkCount++;
            
            // 尝试多种可能的选择器
            const titleSelectors = [
                '.post-title',
                '.article-title', 
                'h1.title',
                'h1',
                '[class*="title"]',
                '.content-title',
                '.detail-title'
            ];
            
            const contentSelectors = [
                '.post-content',
                '.article-content',
                '.content',
                '.detail-content',
                '[class*="content"]',
                'article',
                'main'
            ];
            
            let hasTitle = null;
            let hasContent = null;
            
            // 查找标题元素
            for (const selector of titleSelectors) {
                hasTitle = document.querySelector(selector);
                if (hasTitle && hasTitle.textContent.trim()) {
                    console.log(`  找到标题元素: ${selector}`);
                    break;
                }
            }
            
            // 查找内容元素
            for (const selector of contentSelectors) {
                hasContent = document.querySelector(selector);
                if (hasContent && hasContent.textContent.trim().length > 100) {
                    console.log(`  找到内容元素: ${selector}`);
                    break;
                }
            }
            
            console.log(`🔍 第 ${checkCount} 次检查元素:`, {
                hasTitle: !!hasTitle,
                hasContent: !!hasContent
            });
            
            if (hasTitle && hasContent) {
                clearInterval(checkInterval);
                console.log('✅ 找到必要元素，开始创建按钮');
                
                // 保存找到的选择器以供后续使用
                window.SCYS_PDF_SELECTORS = {
                    title: hasTitle,
                    content: hasContent
                };
                
                createButton();
            }
            
            if (checkCount >= 20) {
                clearInterval(checkInterval);
                console.warn('⏱️ 10秒超时，停止检查元素');
                
                // 即使没找到标题，如果有内容也创建按钮
                if (hasContent) {
                    console.log('⚠️ 未找到标题元素，但找到内容，尝试创建按钮');
                    window.SCYS_PDF_SELECTORS = {
                        title: null,
                        content: hasContent
                    };
                    createButton();
                }
            }
        }, 500);
    }

    // 启动
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        setTimeout(init, 100);
    }
})();