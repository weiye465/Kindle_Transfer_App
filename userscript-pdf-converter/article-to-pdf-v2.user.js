// ==UserScript==
// @name         SCYS文章转PDF工具V2
// @namespace    http://tampermonkey.net/
// @version      2.0.0
// @description  将SCYS网站的文章转换为PDF格式下载（优化版）
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
    
    console.log('🚀 SCYS文章转PDF插件V2已加载');
    console.log('📍 当前页面URL:', window.location.href);
    console.log('📊 文档状态:', document.readyState);

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
        
        .pdf-convert-btn.loading {
            background: #6c757d;
            cursor: not-allowed;
            opacity: 0.8;
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
    `);

    // 创建按钮
    function createButton() {
        console.log('📌 开始创建PDF转换按钮...');
        const button = document.createElement('button');
        button.className = 'pdf-convert-btn';
        button.innerHTML = '转换为PDF';
        
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

    // 新的转换方法 - 直接使用原始DOM
    async function handleConvert() {
        console.log('🔄 开始PDF转换流程...');
        console.time('PDF转换总耗时');
        const button = document.querySelector('.pdf-convert-btn');
        const progressDiv = document.querySelector('.pdf-progress');
        const progressFill = document.querySelector('.pdf-progress-fill');
        
        if (button.classList.contains('loading')) {
            console.log('⚠️ 转换正在进行中，忽略重复点击');
            return;
        }
        
        try {
            button.classList.add('loading');
            button.textContent = '处理中...';
            progressDiv.classList.add('show');
            
            // 获取文章元素
            const titleElement = document.querySelector('.post-title');
            const contentElement = document.querySelector('.post-content');
            
            console.log('🔍 查找文章元素...', {
                titleFound: !!titleElement,
                contentFound: !!contentElement
            });
            
            if (!titleElement || !contentElement) {
                console.error('❌ 找不到文章元素');
                throw new Error('找不到文章内容');
            }
            
            const title = titleElement.textContent.trim();
            console.log('📄 文章标题:', title);
            console.log('📏 内容长度:', contentElement.textContent.length, '字符');
            
            // 创建PDF
            const pdf = new window.jspdf.jsPDF({
                orientation: 'portrait',
                unit: 'mm',
                format: 'a4'
            });
            
            // 设置字体
            pdf.setFont('helvetica');
            pdf.setFontSize(12);
            
            progressFill.style.width = '20%';
            
            // 克隆内容并准备
            console.log('📋 克隆文章内容...');
            const clonedContent = contentElement.cloneNode(true);
            
            // 创建渲染容器
            const renderContainer = document.createElement('div');
            renderContainer.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 794px;
                padding: 40px;
                background: white;
                z-index: 10000;
                font-size: 14px;
                line-height: 1.6;
            `;
            
            // 添加标题
            const titleDiv = document.createElement('h1');
            titleDiv.textContent = title;
            titleDiv.style.cssText = `
                font-size: 24px;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid #e0e0e0;
            `;
            renderContainer.appendChild(titleDiv);
            
            // 添加内容
            clonedContent.style.cssText = `
                font-size: 14px;
                line-height: 1.8;
            `;
            
            // 处理所有标题样式 - 统一设置合理的大小
            const allHeadings = clonedContent.querySelectorAll('h1, h2, h3, h4, h5, h6');
            console.log(`📝 找到 ${allHeadings.length} 个标题元素`);
            allHeadings.forEach(heading => {
                const tagName = heading.tagName.toLowerCase();
                switch(tagName) {
                    case 'h1':
                        heading.style.cssText = 'font-size: 20px; font-weight: bold; margin: 20px 0 10px; color: #1a1a1a;';
                        break;
                    case 'h2':
                        heading.style.cssText = 'font-size: 18px; font-weight: bold; margin: 18px 0 10px; color: #2a2a2a;';
                        break;
                    case 'h3':
                        heading.style.cssText = 'font-size: 16px; font-weight: bold; margin: 15px 0 10px; color: #333;';
                        break;
                    case 'h4':
                        heading.style.cssText = 'font-size: 15px; font-weight: bold; margin: 12px 0 8px; color: #333;';
                        break;
                    case 'h5':
                        heading.style.cssText = 'font-size: 14px; font-weight: bold; margin: 10px 0 8px; color: #444;';
                        break;
                    case 'h6':
                        heading.style.cssText = 'font-size: 13px; font-weight: bold; margin: 10px 0 8px; color: #555;';
                        break;
                }
            });
            
            // 处理段落
            const paragraphs = clonedContent.querySelectorAll('p');
            console.log(`📄 找到 ${paragraphs.length} 个段落`);
            paragraphs.forEach(p => {
                p.style.cssText = 'font-size: 14px; line-height: 1.8; margin: 10px 0; text-align: justify; color: #333;';
            });
            
            // 处理列表
            const lists = clonedContent.querySelectorAll('ul, ol');
            lists.forEach(list => {
                list.style.cssText = 'font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px; color: #333;';
            });
            
            const listItems = clonedContent.querySelectorAll('li');
            listItems.forEach(li => {
                li.style.cssText = 'font-size: 14px; line-height: 1.6; margin: 5px 0; color: #333;';
            });
            
            // 处理引用
            const blockquotes = clonedContent.querySelectorAll('blockquote');
            blockquotes.forEach(bq => {
                bq.style.cssText = 'border-left: 3px solid #ddd; padding-left: 15px; margin: 15px 0; color: #666; font-style: italic;';
            });
            
            // 处理代码块
            const codeBlocks = clonedContent.querySelectorAll('pre, code');
            codeBlocks.forEach(code => {
                code.style.cssText = 'font-family: monospace; font-size: 13px; background: #f5f5f5; padding: 2px 5px; border-radius: 3px;';
            });
            
            // 处理图片
            const images = clonedContent.querySelectorAll('img');
            console.log(`🖼️ 找到 ${images.length} 张图片`);
            images.forEach(img => {
                img.style.cssText = 'max-width: 100%; height: auto; display: block; margin: 15px auto;';
            });
            
            renderContainer.appendChild(clonedContent);
            document.body.appendChild(renderContainer);
            console.log('📦 渲染容器已添加到页面');
            
            progressFill.style.width = '40%';
            
            // 等待内容渲染
            console.log('⏳ 等待内容渲染...');
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // 等待图片加载
            console.log('🖼️ 开始加载图片...');
            let loadedCount = 0;
            const imgPromises = Array.from(images).map((img, index) => {
                return new Promise(resolve => {
                    if (img.complete) {
                        loadedCount++;
                        console.log(`✅ 图片 ${index + 1}/${images.length} 已加载`);
                        resolve();
                    } else {
                        img.onload = () => {
                            loadedCount++;
                            console.log(`✅ 图片 ${index + 1}/${images.length} 加载成功:`, img.src.substring(0, 50) + '...');
                            resolve();
                        };
                        img.onerror = () => {
                            console.warn(`⚠️ 图片 ${index + 1}/${images.length} 加载失败:`, img.src);
                            resolve();
                        };
                    }
                });
            });
            await Promise.all(imgPromises);
            console.log(`✅ 所有图片加载完成 (${loadedCount}/${images.length})`);
            
            progressFill.style.width = '60%';
            
            console.log('📸 开始使用html2canvas生成截图...');
            console.log('📐 容器尺寸:', {
                width: renderContainer.offsetWidth,
                height: renderContainer.scrollHeight
            });
            
            // 使用html2canvas转换
            const canvas = await html2canvas(renderContainer, {
                scale: 1.5,
                useCORS: true,
                allowTaint: true,
                backgroundColor: '#ffffff',
                logging: false,
                width: 794,
                height: renderContainer.scrollHeight
            });
            
            console.log('✅ Canvas生成成功:', {
                width: canvas.width,
                height: canvas.height,
                sizeMB: (canvas.toDataURL().length / 1024 / 1024).toFixed(2)
            });
            progressFill.style.width = '80%';
            
            // 计算页面
            const imgWidth = 210;
            const pageHeight = 297;
            const imgHeight = (canvas.height * imgWidth) / canvas.width;
            const totalPages = Math.ceil(imgHeight / pageHeight);
            console.log('📐 PDF尺寸计算:', {
                imgWidth,
                imgHeight: imgHeight.toFixed(2),
                pageHeight,
                totalPages
            });
            
            let heightLeft = imgHeight;
            let position = 0;
            
            // 添加图片到PDF
            const imgData = canvas.toDataURL('image/jpeg', 0.9);
            pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight);
            heightLeft -= pageHeight;
            
            // 分页处理
            let pageCount = 1;
            while (heightLeft >= 0) {
                position = heightLeft - imgHeight;
                pdf.addPage();
                pageCount++;
                console.log(`📄 添加第 ${pageCount} 页`);
                pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight);
                heightLeft -= pageHeight;
            }
            
            progressFill.style.width = '100%';
            
            // 保存PDF
            const fileName = `${title}_${Date.now()}.pdf`;
            console.log('💾 开始保存PDF文件:', fileName);
            pdf.save(fileName);
            console.log('✅ PDF保存成功!');
            console.timeEnd('PDF转换总耗时');
            
            // 清理
            document.body.removeChild(renderContainer);
            console.log('🧹 临时容器已清理');
            
            // 恢复按钮
            console.log('🎉 PDF转换流程完成!');
            setTimeout(() => {
                progressDiv.classList.remove('show');
                progressFill.style.width = '0%';
                button.classList.remove('loading');
                button.textContent = '转换为PDF';
            }, 1000);
            
        } catch (error) {
            console.error('❌ PDF转换失败:', error);
            console.error('错误堆栈:', error.stack);
            console.timeEnd('PDF转换总耗时');
            alert('PDF转换失败: ' + error.message);
            
            // 清理容器
            const container = document.querySelector('[style*="z-index: 10000"]');
            if (container) {
                document.body.removeChild(container);
            }
            
            // 恢复按钮
            progressDiv.classList.remove('show');
            button.classList.remove('loading');
            button.textContent = '转换为PDF';
        }
    }

    // 初始化
    function init() {
        console.log('🎬 初始化PDF转换插件...');
        let checkCount = 0;
        const checkInterval = setInterval(() => {
            checkCount++;
            const hasTitle = document.querySelector('.post-title');
            const hasContent = document.querySelector('.post-content');
            
            console.log(`🔍 第 ${checkCount} 次检查元素:`, {
                hasTitle: !!hasTitle,
                hasContent: !!hasContent
            });
            
            if (hasTitle && hasContent) {
                clearInterval(checkInterval);
                console.log('✅ 找到必要元素，开始创建按钮');
                createButton();
            }
        }, 500);
        
        setTimeout(() => {
            clearInterval(checkInterval);
            console.warn('⏱️ 10秒超时，停止检查元素');
        }, 10000);
    }

    // 启动
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();