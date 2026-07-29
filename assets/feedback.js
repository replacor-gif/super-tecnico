'use strict';

const form = document.getElementById('feedbackForm');
const pageField = document.getElementById('feedbackPage');
const queryPage = new URLSearchParams(window.location.search).get('page');
pageField.value = queryPage || document.referrer || '';

form.addEventListener('submit', event => {
  event.preventDefault();
  const type = document.getElementById('feedbackType').value;
  const tool = document.getElementById('feedbackTool').value;
  const reference = document.getElementById('feedbackReference').value.trim();
  const message = document.getElementById('feedbackMessage').value.trim();
  const name = document.getElementById('feedbackName').value.trim();
  const replyEmail = document.getElementById('feedbackEmail').value.trim();
  const page = pageField.value.trim();
  const language = window.ST_I18N?.language || 'es';
  const subject = `[Super Técnico BETA] ${type}${reference ? ` · ${reference}` : ''}`;
  const body = [
    `Tipo: ${type}`,
    `Apartado: ${tool}`,
    `Marca / código / componente: ${reference || 'No indicado'}`,
    `Idioma de la interfaz: ${language}`,
    `Página: ${page || 'No indicada'}`,
    `Nombre: ${name || 'No indicado'}`,
    `Correo de respuesta: ${replyEmail || 'No indicado'}`,
    '',
    'Comentario:',
    message,
  ].join('\n');
  window.location.href = `mailto:info@replacor.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
});
