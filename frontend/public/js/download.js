const shortCode = window.location.pathname.replace('/d/', '').replace('/', '');

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1024 / 1024).toFixed(2) + ' MB';
}

function formatDate(iso) {
  if (!iso) return null;
  return new Date(iso).toLocaleString('ru', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

async function loadInfo() {
  try {
    const res = await fetch('/api/info/' + shortCode);
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      showError(
        res.status === 404 ? '🔍' : '⏰',
        res.status === 404 ? 'Файл не найден' : 'Файл недоступен',
        data.detail || 'Срок хранения истёк или лимит скачиваний исчерпан.',
      );
      return;
    }
    const data = await res.json();
    showFile(data);
  } catch (e) {
    showError('⚠️', 'Ошибка сети', 'Не удалось загрузить информацию о файле.');
  }
}

function showFile(data) {
  document.getElementById('state-loading').style.display = 'none';
  document.getElementById('state-file').style.display = 'block';
  document.getElementById('file-name').textContent = data.original_name;

  const meta = document.getElementById('meta-row');
  const pill = (icon, val, label) =>
    `<div class="meta-pill d-flex align-items-center justify-content-between">
      <div class="d-flex align-items-center gap-2 text-muted small fw-bold">
        <i data-lucide="${icon}" style="width:16px; height:16px;"></i>
        ${label}
      </div>
      <span class="highlight">${val}</span>
    </div>`;

  meta.innerHTML =
    pill('database', formatSize(data.file_size), 'РАЗМЕР') +
    (data.expires_at
      ? pill('clock', formatDate(data.expires_at), 'ДОСТУПЕН ДО')
      : pill('clock', 'без срока', 'ДОСТУПЕН ДО')) +
    (data.max_downloads
      ? pill('download', data.download_count + ' / ' + data.max_downloads, 'СКАЧИВАНИЙ')
      : pill('download', data.download_count, 'СКАЧИВАНИЙ'));

  if (data.max_downloads) {
    const left = data.max_downloads - data.download_count;
    if (left <= 2 && left > 0) {
      const wb = document.getElementById('warning-box');
      document.getElementById('warning-text').textContent = `Осталось скачиваний: ${left}`;
      wb.classList.remove('d-none');
    }
  }

  if (typeof lucide !== 'undefined') lucide.createIcons();

  document.getElementById('btn-download').addEventListener('click', () => {
    window.location.href = '/api/download/' + shortCode;
  });
}

function showError(icon, title, sub) {
  document.getElementById('state-loading').style.display = 'none';
  document.getElementById('state-error').style.display = 'block';
  
  const iconMap = {
    '🔍': 'search',
    '⏰': 'clock',
    '⚠️': 'alert-triangle'
  };
  
  const lucideIcon = iconMap[icon] || 'x-circle';
  document.getElementById('err-icon-wrap').innerHTML = `<i data-lucide="${lucideIcon}" style="width: 64px; height: 64px;"></i>`;
  document.getElementById('err-title').textContent = title;
  document.getElementById('err-sub').textContent = sub;
  
  if (typeof lucide !== 'undefined') lucide.createIcons();
}

loadInfo();

