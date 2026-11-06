/**
 * StegoLab - Interactive Frontend Logic
 * Supports 3 Algorithms: Basic LSB, Randomized LSB, Edge-Adaptive
 */

// ── State ──
let currentAlgo = 'lsb';
let currentMode = 'encode';
let activeImageFile = null;
let currentResultId = null;
let activeImageMetrics = { width: 0, height: 0, totalPixels: 0 };

const ALGO_DEFINITIONS = {
  lsb: {
    title: 'Basic LSB (Least Significant Bit)',
    desc: 'Sequentially replaces the least significant bit in each color channel. Fast to process, but the sequential pattern may be detectable by statistical analysis.',
    needsKey: false,
    depthLabel: '1 bit / channel (fixed)'
  },
  rlsb: {
    title: 'Randomized LSB (Cryptographic Seed)',
    desc: 'Uses a key-derived seed to shuffle channel positions with the Fisher-Yates algorithm. Use the same key when extracting the message.',
    needsKey: true,
    depthLabel: '1 bit / channel (shuffled)'
  },
  edge: {
    title: 'Edge-Adaptive Steganography',
    desc: 'Calculates local luminance variance in a 3 by 3 neighborhood and assigns 1 to 3 bits per channel based on image texture.',
    needsKey: false,
    depthLabel: '1 to 3 bits / channel (adaptive)'
  }
};

// ── Algorithm Switching ──
function setAlgo(algoKey, element) {
  currentAlgo = algoKey;
  
  document.querySelectorAll('.algo-card').forEach(c => c.classList.remove('active'));
  if (element) element.classList.add('active');

  const info = ALGO_DEFINITIONS[algoKey] || ALGO_DEFINITIONS.lsb;
  document.getElementById('activeAlgoTitle').textContent = info.title;
  document.getElementById('activeAlgoDesc').textContent = info.desc;

  // Key field visibility
  const keyGroupEnc = document.getElementById('keyGroupEncode');
  const keyGroupDec = document.getElementById('keyGroupDecode');
  if (keyGroupEnc) keyGroupEnc.style.display = info.needsKey ? 'flex' : 'none';
  if (keyGroupDec) keyGroupDec.style.display = info.needsKey ? 'flex' : 'none';

  updateCapacityGauge();
}

// ── Mode Switching (Encode / Decode) ──
function setMode(modeKey) {
  currentMode = modeKey;
  
  document.getElementById('btnModeEncode').classList.toggle('active', modeKey === 'encode');
  document.getElementById('btnModeDecode').classList.toggle('active', modeKey === 'decode');
  
  document.getElementById('encodeFields').style.display = modeKey === 'encode' ? 'block' : 'none';
  document.getElementById('decodeFields').style.display = modeKey === 'decode' ? 'block' : 'none';

  updateActionButtons();
}

// ── Tab Switching ──
function switchTab(tabId, element) {
  document.querySelectorAll('.viz-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.viz-pane').forEach(p => p.classList.remove('active'));

  if (element) element.classList.add('active');
  const targetPane = document.getElementById('pane-' + tabId);
  if (targetPane) targetPane.classList.add('active');
}

// ── Image Handling ──
function onFileSelected(event) {
  const file = event.target.files[0];
  if (!file) return;
  loadImageFromFile(file);
}

function loadImageFromFile(file) {
  activeImageFile = file;
  const reader = new FileReader();
  reader.onload = e => {
    displayImagePreview(e.target.result, file.name);
  };
  reader.readAsDataURL(file);
}

async function loadSample(sampleName) {
  showSpinner('Fetching sample image');
  try {
    const res = await fetch(`/api/sample/${sampleName}`);
    if (!res.ok) throw new Error('Sample not found');
    const blob = await res.blob();
    activeImageFile = new File([blob], `${sampleName}.png`, { type: 'image/png' });
    
    const reader = new FileReader();
    reader.onload = e => {
      displayImagePreview(e.target.result, `${sampleName}.png`);
      hideSpinner();
      showToast(`Loaded sample "${sampleName}"`);
    };
    reader.readAsDataURL(blob);
  } catch (err) {
    hideSpinner();
    showToast('Failed to load sample: ' + err.message, true);
  }
}

function displayImagePreview(srcData, filename) {
  const img = new Image();
  img.onload = () => {
    activeImageMetrics.width = img.width;
    activeImageMetrics.height = img.height;
    activeImageMetrics.totalPixels = img.width * img.height;

    document.getElementById('imagePreview').src = srcData;
    document.getElementById('previewBox').style.display = 'flex';
    document.getElementById('dropzoneContent').style.display = 'none';

    document.getElementById('metaDim').textContent = `${img.width} × ${img.height}`;
    document.getElementById('metaPx').textContent = activeImageMetrics.totalPixels.toLocaleString();
    document.getElementById('metaFmt').textContent = (filename.split('.').pop() || 'PNG').toUpperCase();
    document.getElementById('imageMetaBar').style.display = 'flex';

    document.getElementById('stat-res').textContent = `${img.width}×${img.height}`;

    updateActionButtons();
    updateCapacityGauge();
  };
  img.src = srcData;
}

function removeImage(event) {
  if (event) event.stopPropagation();
  activeImageFile = null;
  activeImageMetrics = { width: 0, height: 0, totalPixels: 0 };
  
  document.getElementById('fileInput').value = '';
  document.getElementById('previewBox').style.display = 'none';
  document.getElementById('dropzoneContent').style.display = 'block';
  document.getElementById('imageMetaBar').style.display = 'none';
  document.getElementById('stat-res').textContent = 'Not calculated';

  updateActionButtons();
  updateCapacityGauge();
}

function updateActionButtons() {
  const hasImage = !!activeImageFile;
  document.getElementById('btnExecuteEncode').disabled = !hasImage;
  document.getElementById('btnExecuteDecode').disabled = !hasImage;
}

// ── Capacity Gauge ──
function updateCapacityGauge() {
  const msg = (document.getElementById('inputMessage') || {}).value || '';
  const totalPx = activeImageMetrics.totalPixels;
  
  if (!totalPx) {
    document.getElementById('capacityFill').style.width = '0%';
    document.getElementById('capacityLabel').textContent = 'Upload an image to compute capacity';
    document.getElementById('capacityPct').textContent = '0%';
    return;
  }

  const bitsPerChannel = (currentAlgo === 'edge') ? 1.4 : 1.0;
  const maxCapacityChars = Math.floor((totalPx * 3 * bitsPerChannel) / 8) - 5;
  const usedChars = msg.length + 4;

  const pct = Math.min(100, Math.max(0, (usedChars / maxCapacityChars) * 100));
  const fill = document.getElementById('capacityFill');
  fill.style.width = `${pct.toFixed(1)}%`;
  fill.className = 'capacity-bar-fill' + (pct > 85 ? ' danger' : pct > 60 ? ' warning' : '');

  document.getElementById('capacityLabel').textContent = `${usedChars} / ~${maxCapacityChars.toLocaleString()} chars`;
  document.getElementById('capacityPct').textContent = `${Math.round(pct)}%`;
}

// ── Execute Encode ──
async function runEncode() {
  if (!activeImageFile) return;
  const msg = document.getElementById('inputMessage').value.trim();
  const key = document.getElementById('inputKey').value.trim() || 'stego2024';

  if (!msg) {
    showToast('Please type a secret message to hide.', true);
    document.getElementById('inputMessage').focus();
    return;
  }

  showSpinner('Encoding message into image channels');
  clearVisualization();

  const formData = new FormData();
  formData.append('image', activeImageFile);
  formData.append('message', msg);
  formData.append('algo', currentAlgo);
  formData.append('key', key);

  try {
    const res = await fetch('/api/encode', { method: 'POST', body: formData });
    const data = await res.json();
    hideSpinner();

    if (!res.ok || data.error) {
      renderErrorLog(data.error || 'Encoding failed');
      showToast(data.error || 'Encoding error', true);
      return;
    }

    currentResultId = data.result_id;
    renderEncodeResults(data);
    showToast('Steganography Encoding Complete!');
  } catch (err) {
    hideSpinner();
    renderErrorLog(err.message);
    showToast('Network error: ' + err.message, true);
  }
}

// ── Execute Decode ──
async function runDecode() {
  if (!activeImageFile) return;
  const key = document.getElementById('inputKeyDecode').value.trim() || 'stego2024';

  showSpinner('Scanning bit planes and extracting message');
  clearVisualization();

  const formData = new FormData();
  formData.append('image', activeImageFile);
  formData.append('algo', currentAlgo);
  formData.append('key', key);

  try {
    const res = await fetch('/api/decode', { method: 'POST', body: formData });
    const data = await res.json();
    hideSpinner();

    if (!res.ok || data.error) {
      renderErrorLog(data.error || 'Decoding failed');
      showToast(data.error || 'Decoding error', true);
      return;
    }

    renderDecodeResults(data);
    if (data.delimiter_found) {
      showToast('Hidden payload successfully extracted!');
    } else {
      showToast('Extraction warning: Delimiter not found.', true);
    }
  } catch (err) {
    hideSpinner();
    renderErrorLog(err.message);
    showToast('Network error: ' + err.message, true);
  }
}

// ── Render Encode Results ──
function renderEncodeResults(data) {
  const s = data.stats;

  document.getElementById('stat-msg').textContent = `${s.msg_length} chars`;
  document.getElementById('stat-bits').textContent = s.bits_embedded.toLocaleString();
  document.getElementById('stat-changes').textContent = s.channels_changed.toLocaleString();
  document.getElementById('stat-use').textContent = `${s.usage_pct}%`;
  const psnrValue = s.psnr_db != null ? `${s.psnr_db} dB` : 'Not available';
  document.getElementById('stat-psnr').textContent = psnrValue;

  const logEntries = [
    { n: '01', t: `Algorithm: <span class="hl-cyan">${s.algo}</span>` },
    { n: '02', t: `Carrier dimensions: <span class="hl">${s.width} x ${s.height}</span> (${s.total_pixels.toLocaleString()} pixels)` },
    { n: '03', t: `Total channel bytes: <span class="hl">${s.total_channels.toLocaleString()}</span>` },
    { n: '04', t: `Payload: <span class="hl">${s.msg_length} characters</span> + 4-byte delimiter (<span class="hl">${s.bits_embedded} bits</span>)` },
    { n: '05', t: `Modified channels: <span class="hl-rose">${s.channels_changed.toLocaleString()}</span> channel bytes` },
    { n: '06', t: `Modified pixels: <span class="hl-amber">${s.pixels_changed.toLocaleString()}</span> pixels (${((s.pixels_changed/s.total_pixels)*100).toFixed(2)}%)` },
    { n: '07', t: `Measured PSNR: <span class="hl-green">${psnrValue}</span>` },
    { n: '08', t: `Capacity utilization: <span class="hl-cyan">${s.usage_pct}%</span>` },
  ];
  if (s.key_used) {
    logEntries.push({ n: '09', t: `Secret key: <span class="hl-amber">"${s.key_used}"</span>` });
  }
  logEntries.push({ n: 'DONE', t: '<span class="hl-green">Encoding finished. Lossless PNG is ready for download.</span>' });
  renderLogEntries(logEntries);

  renderTextTable(data.text_table);
  renderPixelMatrix(data.pixel_matrix, s.total_pixels);
  renderChangesTable(data.change_log, s.channels_changed);

  const outImg = document.getElementById('resultImagePreview');
  outImg.src = `/api/download/${data.result_id}`;
  document.getElementById('stegoImgCard').style.display = 'block';
  document.getElementById('decodedMsgCard').style.display = 'none';
  document.getElementById('outputStudio').style.display = 'flex';
  document.getElementById('outputEmptyState').style.display = 'none';
  document.getElementById('btnDownloadResult').style.display = 'flex';

  switchTab('log', document.querySelectorAll('.viz-tab')[0]);
}

// ── Render Decode Results ──
function renderDecodeResults(data) {
  document.getElementById('stat-msg').textContent = `${data.msg_length} chars`;
  document.getElementById('stat-bits').textContent = data.bits_read.toLocaleString();
  document.getElementById('stat-changes').textContent = 'Not calculated';
  document.getElementById('stat-use').textContent = 'Not calculated';
  document.getElementById('stat-psnr').textContent = 'Not calculated';

  const logEntries = [
    { n: '01', t: `Extraction mode: <span class="hl-cyan">${data.algo_label}</span>` },
    { n: '02', t: `Total bits read: <span class="hl">${data.bits_read.toLocaleString()}</span>` },
    { n: '03', t: `Delimiter check: ${data.delimiter_found ? '<span class="hl-green">Found (valid payload)</span>' : '<span class="hl-rose">Not found (check the key or source image)</span>'}` },
    { n: '04', t: `Recovered length: <span class="hl">${data.msg_length} characters</span>` },
    { n: 'DONE', t: `Decoded payload: <span class="hl-green">"${escapeHtml(data.message)}"</span>` }
  ];
  renderLogEntries(logEntries);

  renderTextTable(data.text_table);
  renderExtractionTable(data.extraction_log);

  document.getElementById('decodedMessageBox').textContent = data.message || '(Empty message)';
  document.getElementById('decodedMetaStats').textContent = `${data.bits_read.toLocaleString()} bits read - ${data.msg_length} characters recovered - Delimiter: ${data.delimiter_found ? 'Valid' : 'Unmatched'}`;
  document.getElementById('decodedMsgCard').style.display = 'block';
  document.getElementById('stegoImgCard').style.display = 'none';
  document.getElementById('outputStudio').style.display = 'flex';
  document.getElementById('outputEmptyState').style.display = 'none';

  switchTab('output', document.querySelectorAll('.viz-tab')[4]);
}

// ── Sub-Tab Renderers ──
function renderLogEntries(entries) {
  document.getElementById('logEmptyState').style.display = 'none';
  const stream = document.getElementById('logStream');
  stream.style.display = 'block';
  stream.innerHTML = entries.map(e => `
    <div class="log-entry">
      <span class="log-bullet">${e.n}</span>
      <div class="log-text">${e.t}</div>
    </div>
  `).join('');
}

function renderErrorLog(errMsg) {
  document.getElementById('logEmptyState').style.display = 'none';
  const stream = document.getElementById('logStream');
  stream.style.display = 'block';
  stream.innerHTML = `
    <div class="log-entry">
      <span class="log-bullet">ERROR</span>
      <div class="log-text"><span class="hl-rose">Execution Error: ${escapeHtml(errMsg)}</span></div>
    </div>
  `;
  switchTab('log', document.querySelectorAll('.viz-tab')[0]);
}

function renderTextTable(rows) {
  if (!rows || !rows.length) return;
  document.getElementById('textEmptyState').style.display = 'none';
  const container = document.getElementById('textTableContainer');
  container.style.display = 'block';

  const tbody = document.getElementById('textTableBody');
  tbody.innerHTML = rows.map((r, i) => {
    const bitCells = r.bits.map(b => `<span class="bit-cell ${b ? 'on' : ''}">${b}</span>`).join('');
    return `
      <tr>
        <td>${i + 1}</td>
        <td><code>${escapeHtml(r.char)}</code></td>
        <td>${r.ascii}</td>
        <td><code>${r.binary}</code></td>
        <td><div style="display:flex;">${bitCells}</div></td>
      </tr>
    `;
  }).join('');
}

function renderPixelMatrix(pixels, total) {
  if (!pixels || !pixels.length) return;
  document.getElementById('matrixEmptyState').style.display = 'none';
  const container = document.getElementById('matrixTableContainer');
  container.style.display = 'block';

  document.getElementById('matrixCaption').textContent = 
    `Previewing ${pixels.length} of ${total.toLocaleString()} pixels (Modified rows highlighted in red).`;

  const tbody = document.getElementById('matrixTableBody');
  tbody.innerHTML = pixels.map(p => {
    const rBin = makeBitDiff(p.orig_bin[0], p.steg_bin[0]);
    const gBin = makeBitDiff(p.orig_bin[1], p.steg_bin[1]);
    const bBin = makeBitDiff(p.orig_bin[2], p.steg_bin[2]);

    return `
      <tr class="${p.changed ? 'row-modified' : ''}">
        <td>#${p.idx}</td>
        <td>${p.row}</td>
        <td>${p.col}</td>
        <td>[${p.orig.join(', ')}]</td>
        <td>[${p.stego.join(', ')}]</td>
        <td>${rBin}</td>
        <td>${gBin}</td>
        <td>${bBin}</td>
        <td><span class="${p.changed ? 'hl-rose' : 'diff-zero'}">${p.changed ? 'MODIFIED' : 'UNCHANGED'}</span></td>
      </tr>
    `;
  }).join('');
}

function makeBitDiff(origBin, stegBin) {
  let html = '<div style="display:flex;">';
  for (let i = 0; i < 8; i++) {
    const isChanged = origBin[i] !== stegBin[i];
    const isOne = stegBin[i] === '1';
    html += `<span class="bit-cell ${isChanged ? 'chg' : (isOne ? 'on' : '')}">${stegBin[i]}</span>`;
  }
  return html + '</div>';
}

function renderChangesTable(changes, totalChanges) {
  if (!changes || !changes.length) return;
  document.getElementById('changesEmptyState').style.display = 'none';
  const container = document.getElementById('changesTableContainer');
  container.style.display = 'block';

  document.getElementById('changesCaption').textContent = 
    `Showing first ${changes.length} of ${totalChanges.toLocaleString()} modified channel bytes (Old vs New binary registers).`;

  document.getElementById('changesTableHead').innerHTML = `
    <tr>
      <th>Pixel #</th>
      <th>Row</th>
      <th>Col</th>
      <th>Channel</th>
      <th>Old Val</th>
      <th>New Val</th>
      <th>Diff</th>
      <th>Old Binary</th>
      <th>New Binary</th>
      <th>Embedded</th>
    </tr>
  `;

  const tbody = document.getElementById('changesTableBody');
  tbody.innerHTML = changes.map(c => {
    const diffClass = c.diff > 0 ? 'diff-pos' : (c.diff < 0 ? 'diff-neg' : 'diff-zero');
    const diffSign = c.diff > 0 ? `+${c.diff}` : `${c.diff}`;
    const oldBits = makeBitCells(c.old_bin);
    const newBits = makeBitCells(c.new_bin, c.old_bin);

    return `
      <tr>
        <td>#${c.pixel_idx}</td>
        <td>${c.row}</td>
        <td>${c.col}</td>
        <td><span class="ch-badge ch-${c.channel}">${c.channel}</span></td>
        <td>${c.old_val}</td>
        <td>${c.new_val}</td>
        <td class="${diffClass}">${diffSign}</td>
        <td>${oldBits}</td>
        <td>${newBits}</td>
        <td><span class="bit-cell on">${c.bit_embedded}</span></td>
      </tr>
    `;
  }).join('');
}

function renderExtractionTable(extractions) {
  if (!extractions || !extractions.length) return;
  document.getElementById('changesEmptyState').style.display = 'none';
  const container = document.getElementById('changesTableContainer');
  container.style.display = 'block';

  document.getElementById('changesCaption').textContent = 
    `Extraction Log: Showing first ${extractions.length} channel bit reads.`;

  document.getElementById('changesTableHead').innerHTML = `
    <tr>
      <th>Bit #</th>
      <th>Pixel #</th>
      <th>Row</th>
      <th>Col</th>
      <th>Channel</th>
      <th>Byte Val</th>
      <th>Binary Representation</th>
      <th>Extracted Bit(s)</th>
    </tr>
  `;

  const tbody = document.getElementById('changesTableBody');
  tbody.innerHTML = extractions.map(e => `
    <tr>
      <td>${e.bit_index}</td>
      <td>#${e.pixel_idx}</td>
      <td>${e.row}</td>
      <td>${e.col}</td>
      <td><span class="ch-badge ch-${e.channel}">${e.channel}</span></td>
      <td>${e.byte_val}</td>
      <td>${makeBitCells(e.binary)}</td>
      <td><span class="bit-cell chg">${e.lsb}</span></td>
    </tr>
  `).join('');
}

function makeBitCells(binStr, compareBinStr) {
  let html = '<div style="display:flex;">';
  for (let i = 0; i < binStr.length; i++) {
    const isChanged = compareBinStr && (binStr[i] !== compareBinStr[i]);
    const isOne = binStr[i] === '1';
    html += `<span class="bit-cell ${isChanged ? 'chg' : (isOne ? 'on' : '')}">${binStr[i]}</span>`;
  }
  return html + '</div>';
}

// ── Actions & Helpers ──
function clearVisualization() {
  currentResultId = null;
  document.getElementById('logEmptyState').style.display = 'flex';
  document.getElementById('logStream').style.display = 'none';
  document.getElementById('textEmptyState').style.display = 'flex';
  document.getElementById('textTableContainer').style.display = 'none';
  document.getElementById('matrixEmptyState').style.display = 'flex';
  document.getElementById('matrixTableContainer').style.display = 'none';
  document.getElementById('changesEmptyState').style.display = 'flex';
  document.getElementById('changesTableContainer').style.display = 'none';
  document.getElementById('outputEmptyState').style.display = 'flex';
  document.getElementById('outputStudio').style.display = 'none';
  document.getElementById('btnDownloadResult').style.display = 'none';

  ['stat-msg', 'stat-bits', 'stat-changes', 'stat-use', 'stat-psnr'].forEach(id => {
    document.getElementById(id).textContent = 'Not calculated';
  });
}

function downloadResultImage() {
  if (!currentResultId) return;
  window.location.href = `/api/download/${currentResultId}`;
}

function useResultAsInput() {
  if (!currentResultId) return;
  setMode('decode');
  loadSample(`../images/results/${currentResultId}`);
  showToast('Stego result loaded into input controls.');
}

function copyDecodedMessage() {
  const text = document.getElementById('decodedMessageBox').textContent;
  if (!text) return;
  navigator.clipboard.writeText(text).then(() => {
    showToast('Decoded message copied to clipboard!');
  }).catch(() => {
    showToast('Failed to copy to clipboard', true);
  });
}

function showSpinner(message) {
  document.getElementById('loadingMsg').textContent = message || 'Processing image';
  document.getElementById('loadingOverlay').style.display = 'flex';
  document.getElementById('btnExecuteEncode').disabled = true;
  document.getElementById('btnExecuteDecode').disabled = true;
}

function hideSpinner() {
  document.getElementById('loadingOverlay').style.display = 'none';
  updateActionButtons();
}

function showToast(message, isError = false) {
  const toast = document.getElementById('appToast');
  toast.textContent = message;
  toast.style.borderColor = isError ? 'var(--accent-rose)' : 'var(--accent-emerald)';
  toast.style.display = 'block';
  setTimeout(() => {
    toast.style.display = 'none';
  }, 3500);
}

function toggleHelpModal(show) {
  document.getElementById('helpModal').style.display = show ? 'flex' : 'none';
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ── Drag & Drop Listeners ──
document.addEventListener('DOMContentLoaded', () => {
  setAlgo('lsb');

  const zone = document.getElementById('dropZone');
  if (zone) {
    zone.addEventListener('dragover', e => {
      e.preventDefault();
      zone.classList.add('dragover');
    });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', e => {
      e.preventDefault();
      zone.classList.remove('dragover');
      const files = e.dataTransfer.files;
      if (files && files.length) loadImageFromFile(files[0]);
    });
  }
});
