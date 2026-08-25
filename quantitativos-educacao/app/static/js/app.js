const form = document.querySelector('#upload-form');
const fileInput = document.querySelector('#file-input');
const fileLabel = document.querySelector('#file-label');
const dropZone = document.querySelector('#drop-zone');
const submitButton = document.querySelector('#submit-button');
const message = document.querySelector('#message');
const results = document.querySelector('#results');
const downloadButton = document.querySelector('#download-button');

const escapeHtml = (value) => String(value).replace(/[&<>'"]/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
}[char]));
const formatNumber = value => new Intl.NumberFormat('pt-BR').format(value);

function showMessage(text, type = 'danger') {
  message.textContent = text;
  message.className = `alert alert-${type} mt-3 mb-0`;
}

function setFile(file) {
  if (!file) return;
  const transfer = new DataTransfer();
  transfer.items.add(file);
  fileInput.files = transfer.files;
  fileLabel.textContent = file.name;
}

['dragenter', 'dragover'].forEach(event => dropZone.addEventListener(event, e => {
  e.preventDefault(); dropZone.classList.add('is-dragging');
}));
['dragleave', 'drop'].forEach(event => dropZone.addEventListener(event, e => {
  e.preventDefault(); dropZone.classList.remove('is-dragging');
}));
dropZone.addEventListener('drop', event => setFile(event.dataTransfer.files[0]));
fileInput.addEventListener('change', () => setFile(fileInput.files[0]));

function render(data) {
  const metrics = [
    ['Alunos', data.resumo.alunos], ['Estabelecimentos', data.resumo.estabelecimentos],
    ['Feminino', data.resumo.total_f], ['Masculino', data.resumo.total_m]
  ];
  document.querySelector('#summary-cards').innerHTML = metrics.map(([label, value]) => `
    <div class="col-6 col-lg-3"><div class="metric-card"><span>${label}</span><strong>${formatNumber(value)}</strong></div></div>
  `).join('');

  const groupHeaders = data.series.map(grade => `<th colspan="3">${escapeHtml(grade)}</th>`).join('');
  const subHeaders = data.series.map(() => '<th>F</th><th>M</th><th>Total</th>').join('');
  const rows = data.estabelecimentos.map(row => {
    const cells = data.series.map(grade => {
      const item = row.series[grade];
      return `<td>${item.F}</td><td>${item.M}</td><td class="total-cell">${item.total}</td>`;
    }).join('');
    return `<tr><td class="establishment">${escapeHtml(row.estabelecimento)}</td>${cells}<td class="total-cell">${row.total_f}</td><td class="total-cell">${row.total_m}</td><td class="total-cell">${row.total_geral}</td></tr>`;
  }).join('');
  document.querySelector('#result-table').innerHTML = `
    <thead><tr><th rowspan="2" class="establishment">Estabelecimento</th>${groupHeaders}<th colspan="3">Totais</th></tr>
    <tr>${subHeaders}<th>F</th><th>M</th><th>Geral</th></tr></thead><tbody>${rows}</tbody>`;
  document.querySelector('#ignored-note').textContent = data.resumo.linhas_ignoradas
    ? `${data.resumo.linhas_ignoradas} linha(s) incompleta(s) ou com sexo inválido foram ignoradas.` : '';
  results.classList.remove('d-none');
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  if (!fileInput.files.length) return showMessage('Selecione uma planilha Excel.');
  message.classList.add('d-none'); results.classList.add('d-none');
  submitButton.disabled = true; submitButton.textContent = 'Processando…';
  const body = new FormData(); body.append('file', fileInput.files[0]);
  try {
    const response = await fetch('/api/processar', { method: 'POST', body });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || 'Não foi possível processar o arquivo.');
    render(payload);
  } catch (error) { showMessage(error.message); }
  finally { submitButton.disabled = false; submitButton.textContent = 'Gerar quantitativos'; }
});

downloadButton.addEventListener('click', async () => {
  if (!fileInput.files.length) return showMessage('Selecione e processe uma planilha primeiro.');
  message.classList.add('d-none');
  downloadButton.disabled = true;
  const originalText = downloadButton.innerHTML;
  downloadButton.textContent = 'Gerando arquivo…';
  const body = new FormData();
  body.append('file', fileInput.files[0]);
  try {
    const response = await fetch('/api/exportar', { method: 'POST', body });
    if (!response.ok) {
      const payload = await response.json();
      throw new Error(payload.detail || 'Não foi possível gerar o arquivo.');
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'quantitativos_educacionais.xlsx';
    document.body.appendChild(link);
    link.click();
    link.remove();
    // Alguns navegadores precisam de um pequeno intervalo antes que o endereço
    // temporário seja descartado para concluir o salvamento do arquivo.
    window.setTimeout(() => URL.revokeObjectURL(url), 5000);
    showMessage('Relatório gerado. Verifique a pasta de Downloads.', 'success');
  } catch (error) { showMessage(error.message); }
  finally { downloadButton.disabled = false; downloadButton.innerHTML = originalText; }
});
