// 取得 DOM 元素
const userPhotoInput = document.getElementById('userPhoto');
const templateInput = document.getElementById('template');
const workspace = document.getElementById('workspace');
const displayUserPhoto = document.getElementById('displayUserPhoto');
const displayTemplate = document.getElementById('displayTemplate');
const generateBtn = document.getElementById('generateBtn');
const resultContainer = document.getElementById('resultContainer');
const resultImage = document.getElementById('resultImage');
const downloadBtn = document.getElementById('downloadBtn');

// 記錄模板目前的 X, Y 偏移量 (相對於網頁顯示大小)
let currentX = 0;
let currentY = 0;

// --- 1. 圖片上傳預覽 ---
function handleImagePreview(input, displayElement, isTemplate = false) {
    input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            displayElement.src = URL.createObjectURL(file);
            displayElement.onload = () => {
                // 如果是模板，預設寬度跟底圖一樣，並重置位置
                if (isTemplate) {
                    currentX = 0;
                    currentY = 0;
                    displayTemplate.style.left = '0px';
                    displayTemplate.style.top = '0px';
                }
                checkWorkspaceReady();
            };
        }
    });
}

handleImagePreview(userPhotoInput, displayUserPhoto, false);
handleImagePreview(templateInput, displayTemplate, true);

function checkWorkspaceReady() {
    if (displayUserPhoto.src && displayTemplate.src) {
        workspace.classList.remove('hidden');
    }
}

// --- 2. 滑鼠拖曳邏輯 ---
let isDragging = false;
let startPointerX, startPointerY;
let initialX, initialY;

// 避免圖片預設的拖曳行為干擾
displayTemplate.addEventListener('dragstart', (e) => e.preventDefault());

// 【小幫手】自動判斷是滑鼠還是觸控，並回傳正確的 X, Y 座標
function getPointerPos(e) {
    if (e.touches && e.touches.length > 0) {
        return { x: e.touches[0].clientX, y: e.touches[0].clientY };
    }
    return { x: e.clientX, y: e.clientY };
}

// 統一的「開始拖曳」邏輯
function startDrag(e) {
    isDragging = true;
    const pos = getPointerPos(e);
    startPointerX = pos.x;
    startPointerY = pos.y;
    initialX = currentX;
    initialY = currentY;
}

// 統一的「拖曳中」邏輯
function drag(e) {
    if (!isDragging) return;
    e.preventDefault(); // 防止選取到網頁文字或觸發其他滑動
    
    const pos = getPointerPos(e);
    const dx = pos.x - startPointerX;
    const dy = pos.y - startPointerY;
    
    currentX = initialX + dx;
    currentY = initialY + dy;
    
    displayTemplate.style.left = `${currentX}px`;
    displayTemplate.style.top = `${currentY}px`;
}

// 統一的「結束拖曳」邏輯
function endDrag() {
    isDragging = false;
}

// 綁定滑鼠事件 (Desktop)
displayTemplate.addEventListener('mousedown', startDrag);
window.addEventListener('mousemove', drag, { passive: false });
window.addEventListener('mouseup', endDrag);

// 綁定觸控事件 (Mobile)
displayTemplate.addEventListener('touchstart', startDrag, { passive: false });
window.addEventListener('touchmove', drag, { passive: false });
window.addEventListener('touchend', endDrag);

// --- 3. 生成按鈕與 API 請求 ---
generateBtn.addEventListener('click', async () => {
    const userPhoto = userPhotoInput.files[0];
    const template = templateInput.files[0];

    if (!userPhoto || !template) {
        alert('請先上傳照片與模板！');
        return;
    }

    generateBtn.textContent = 'Processing...';
    generateBtn.disabled = true;

    // 【關鍵數學】計算真實的像素偏移量
    // ratio = 真實照片寬度 / 網頁顯示寬度
    const scaleRatio = displayUserPhoto.naturalWidth / displayUserPhoto.clientWidth;
    const realOffsetX = Math.round(currentX * scaleRatio);
    const realOffsetY = Math.round(currentY * scaleRatio);
    
    // 計算模板在真實照片中應該被縮放到的寬度
    const realTemplateWidth = Math.round(displayTemplate.clientWidth * scaleRatio);

    const formData = new FormData();
    formData.append('user_photo', userPhoto);
    formData.append('template', template);
    formData.append('offset_x', realOffsetX);
    formData.append('offset_y', realOffsetY);
    formData.append('target_width', realTemplateWidth);

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Generation failed');

        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
        
        resultImage.src = imageUrl;
        downloadBtn.href = imageUrl;
        resultContainer.classList.remove('hidden');
        
        // 畫面滾動到結果區
        resultContainer.scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        alert('發生錯誤，請檢查後端終端機。');
        console.error(error);
    } finally {
        generateBtn.textContent = 'Generate';
        generateBtn.disabled = false;
    }
});


document.getElementById('emailContact').addEventListener('click', (e) => {
    e.preventDefault(); // 防止任何預設點擊行為
    
    const email = 'anguszheng11@gmail.com';
    const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=${email}`;

    navigator.clipboard.writeText(email).then(() => {
        // 程式會在這裡停住，等待使用者點擊「確定」
        alert(`信箱已複製到剪貼簿：${email}\n\n按下「確定」後，將為您開啟 Gmail 寫信頁面！`);
        
        // 下確定後，才透過 JS 開啟新分頁
        window.open(gmailUrl, '_blank');
    }).catch(err => {
        console.error('複製失敗:', err);
        // 如果複製失敗，還是可以幫他開分頁
        window.open(gmailUrl, '_blank');
    });
});