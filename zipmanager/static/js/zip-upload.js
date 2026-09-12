(function () {
  'use strict';

  const MAX_ZIP_BYTES = 1024 * 1024 * 1024; // 1 GB
  const fmtMB = b => (b / 1024 / 1024).toFixed(2) + ' MB';

  function initButton(btn) {
    const folderInput = btn.querySelector('.zip-folder-input');
    const progressEl  = btn.querySelector('.zip-progress');

    function setState(state, text) {
      btn.classList.remove('is-success', 'is-error');
      if (state === 'success') btn.classList.add('is-success');
      if (state === 'error')   btn.classList.add('is-error');
      if (text !== undefined) progressEl.textContent = text;
    }

    function reset() {
      btn.disabled = false;
      progressEl.hidden = true;
      setState('idle', '0%');
    }

    // 1. Click icon → open folder picker
    btn.addEventListener('click', (e) => {
      if (e.target === folderInput) return;
      folderInput.value = '';
      folderInput.click();
    });

    // 2. Folder selected → auto-zip → auto-upload
    folderInput.addEventListener('change', async () => {
      const files = [...folderInput.files];
      if (!files.length) return;

      btn.disabled = true;
      progressEl.hidden = false;
      setState('working', '0%');

      try {
        const zip = new JSZip();
        for (const f of files) {
          const path = (f.webkitRelativePath || f.name).replace(/\\/g, '/');
          zip.file(path, f);
        }

        const blob = await zip.generateAsync(
          { type: 'blob', compression: 'DEFLATE', compressionOptions: { level: 6 } },
          (meta) => setState('working', meta.percent.toFixed(0) + '%')
        );

        if (blob.size > MAX_ZIP_BYTES) {
          alert(`Zip is ${fmtMB(blob.size)} — exceeds 1 GB limit.`);
          reset();
          return;
        }

        const topFolder = (files[0].webkitRelativePath || files[0].name).split('/')[0] || 'folder';
        const fd = new FormData();
        fd.append('zip_file', blob, topFolder + '.zip');
        fd.append('source', btn.dataset.source || 'store');
        fd.append('source_id', btn.dataset.sourceId || '');

        setState('working', '↑');
        const res = await fetch(btn.dataset.zipUrl, {
          method: 'POST',
          headers: { 'X-CSRFToken': btn.dataset.csrf },
          body: fd,
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Upload failed');

        setState('success', '✓');
        setTimeout(() => window.location.reload(), 600);

      } catch (err) {
        alert('ZIP upload failed: ' + err.message);
        setState('error', '✗');
        setTimeout(reset, 1500);
      }
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.zip-icon-btn').forEach(initButton);
  });
})();