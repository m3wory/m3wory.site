const fileInput = document.getElementById('file-input');
const dropZone = document.getElementById('drop-zone');
const btnUpload = document.getElementById('btn-upload');
const uploadCard = document.getElementById('upload-card');
const resultCard = document.getElementById('result-card');
const errorBox = document.getElementById('error-box');
let selectedFile = null;

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  if (e.dataTransfer.files[0]) selectFile(e.dataTransfer.files[0]);
});

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) selectFile(fileInput.files[0]);
});

function selectFile(file) {
  selectedFile = file;
  document.getElementById('sel-name').textContent = file.name;
  document.getElementById('sel-size').textContent = formatSize(file.size);
  document.getElementById('file-selected').style.display = 'flex';
  dropZone.style.display = 'none';
  btnUpload.disabled = false;
  hideError();
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1024 / 1024).toFixed(2) + ' MB';
}

function showError(msg) {
  errorBox.textContent = msg;
  errorBox.classList.remove('d-none');
}

function hideError() {
  errorBox.classList.add('d-none');
}

btnUpload.addEventListener('click', async () => {
  if (!selectedFile) return;
  hideError();

  const formData = new FormData();
  formData.append('file', selectedFile);
  formData.append('expires_hours', document.getElementById('expires-hours').value);
  formData.append('max_downloads', document.getElementById('max-downloads').value);

  btnUpload.disabled = true;
  btnUpload.textContent = 'Загрузка...';

  const progressWrap = document.getElementById('progress-wrap');
  const progressBar = document.getElementById('progress-bar');
  progressWrap.classList.remove('d-none');
  progressBar.style.width = '0%';

  try {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/upload');

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const pct = Math.round((e.loaded / e.total) * 100);
        progressBar.style.width = pct + '%';
      }
    };

    xhr.onload = () => {
      progressWrap.classList.add('d-none');
      if (xhr.status === 200) {
        const data = JSON.parse(xhr.responseText);
        showResult(data);
      } else if (xhr.status === 413) {
        showError('Файл слишком большой');
        resetBtn();
      } else {
        let msg = 'Ошибка при загрузке';
        try {
          msg = JSON.parse(xhr.responseText).detail || msg;
        } catch {
          // ignore
        }
        showError(msg);
        resetBtn();
      }
    };

    xhr.onerror = () => {
      progressWrap.classList.add('d-none');
      showError('Ошибка сети. Попробуйте ещё раз.');
      resetBtn();
    };

    xhr.send(formData);
  } catch (e) {
    showError('Неизвестная ошибка: ' + e.message);
    resetBtn();
  }
});

function resetBtn() {
  btnUpload.disabled = false;
  btnUpload.textContent = 'Загрузить файл';
}

function showResult(data) {
  const link = window.location.origin + '/d/' + data.short_code;
  document.getElementById('result-link').textContent = link;

  const badges = document.getElementById('result-badges');
  badges.innerHTML = '';

  const addBadge = (icon, text) => {
    badges.innerHTML += `<span class="badge-info"><i data-lucide="${icon}" style="width:16px; height:16px;"></i> ${text}</span>`;
  };

  addBadge(
    'file',
    data.original_name.length > 30
      ? data.original_name.substring(0, 30) + '…'
      : data.original_name,
  );
  addBadge('database', formatSize(data.file_size));
  if (data.expires_at) {
    const d = new Date(data.expires_at);
    addBadge('clock', 'до ' + d.toLocaleString('ru'));
  } else {
    addBadge('clock', 'без срока');
  }
  if (data.max_downloads) {
    addBadge('download', 'макс. ' + data.max_downloads + ' скач.');
  } else {
    addBadge('download', 'неогр. скачиваний');
  }

  if (typeof lucide !== 'undefined') lucide.createIcons();

  uploadCard.style.display = 'none';
  resultCard.style.display = 'block';

  // Генерируем QR-код
  const qrContainer = document.getElementById('qr-code');
  qrContainer.innerHTML = '';
  new QRCode(qrContainer, {
    text: link,
    width: 200,
    height: 200,
    colorDark: "#1e293b",
    colorLight: "#ffffff",
    correctLevel: QRCode.CorrectLevel.H
  });
  document.getElementById('qr-wrap').style.display = 'flex';
}

function downloadQR() {
  const qrImg = document.querySelector('#qr-code img');
  if (!qrImg) return;

  const a = document.createElement('a');
  a.href = qrImg.src;
  a.download = 'qr-code.png';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

function copyLink() {
  const link = document.getElementById('result-link').textContent;
  navigator.clipboard.writeText(link).then(() => {
    const btn = document.getElementById('btn-copy');
    btn.textContent = 'Скопировано!';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.textContent = 'Копировать';
      btn.classList.remove('copied');
    }, 2000);
  });
}

function resetForm() {
  selectedFile = null;
  fileInput.value = '';
  document.getElementById('file-selected').style.display = 'none';
  dropZone.style.display = 'block';
  btnUpload.disabled = true;
  btnUpload.textContent = 'Загрузить файл';
  hideError();
  uploadCard.style.display = 'block';
  resultCard.style.display = 'none';
}

