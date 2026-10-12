/* Giscus's documented widget protocol; GitHub credentials never enter this page.
 * One frame per visited figure stays mounted so unsent drafts survive switching.
 */
(() => {
  'use strict';
  const configElement = document.getElementById('gallery-comment-config');
  if (!configElement) return;
  const config = JSON.parse(configElement.textContent);
  const provider = 'https://giscus.app';
  const frames = new Map();
  const buttons = new Map();
  let activeKey = null;
  let returnFocus = null;
  let session = '';

  // Same OAuth return/session convention as the official giscus client.
  const returnUrl = new URL(location.href);
  const returnedSession = returnUrl.searchParams.get('giscus');
  try {
    session = returnedSession || JSON.parse(localStorage.getItem('giscus-session') || '""');
    if (returnedSession) localStorage.setItem('giscus-session', JSON.stringify(returnedSession));
  } catch (_) { session = returnedSession || ''; }
  if (typeof session !== 'string') session = '';
  if (returnedSession) {
    returnUrl.searchParams.delete('giscus');
    history.replaceState(null, '', returnUrl);
  }

  const dialog = document.createElement('dialog');
  dialog.className = 'comment-dialog';
  dialog.setAttribute('aria-labelledby', 'comment-dialog-title');
  dialog.innerHTML = '<div class="comment-heading"><h2 id="comment-dialog-title"></h2>' +
    '<button type="button" class="comment-close" aria-label="Close comments">Close</button></div>' +
    '<p class="comment-help">Sign in with GitHub to leave feedback or reply. Comments are public and saved immediately.</p>' +
    '<p class="comment-version"></p><div class="comment-frames"></div>';
  document.body.append(dialog);
  const title = dialog.querySelector('h2');
  const version = dialog.querySelector('.comment-version');
  const frameContainer = dialog.querySelector('.comment-frames');

  function cleanUrl(key) {
    const url = new URL(location.href);
    url.searchParams.delete('giscus');
    url.hash = 'comments-' + key;
    return url;
  }

  function createFrame(key, review) {
    const host = document.createElement('div');
    host.className = 'comment-host';
    const status = document.createElement('p');
    status.className = 'comment-status';
    status.setAttribute('role', 'status');
    status.textContent = 'Loading comments…';
    host.append(status);
    const iframe = document.createElement('iframe');
    iframe.title = 'Comments on ' + review.title;
    iframe.setAttribute('allow', 'clipboard-write');
    iframe.referrerPolicy = 'strict-origin-when-cross-origin';
    const params = new URLSearchParams({
      origin: cleanUrl(key).href, session, repo: config.repository,
      repoId: config.repository_id, category: config.category,
      categoryId: config.category_id, term: review.term,
      description: 'Figure: ' + review.title + '\nReviewed artwork SHA-256: ' + review.version +
        '\nFiles: ' + review.assets.map(asset => asset.path).join(', '),
      backLink: cleanUrl(key).href, strict: '1', reactionsEnabled: '0',
      emitMetadata: '1', inputPosition: 'top', theme: 'light',
    });
    iframe.src = provider + '/en/widget?' + params;
    host.append(iframe);
    frameContainer.append(host);
    const entry = {host, iframe, status, timer:null};
    entry.timer = setTimeout(() => {
      status.hidden = false;
      status.textContent = 'Comments are taking longer to load. Check your connection and try again.';
      const retry = document.createElement('button');
      retry.type = 'button';
      retry.className = 'comment-retry';
      retry.textContent = 'Retry';
      retry.addEventListener('click', () => {
        host.remove();
        clearTimeout(entry.timer);
        frames.delete(key);
        openComments(key, returnFocus);
      });
      status.append(' ', retry);
    }, 20000);
    frames.set(key, entry);
    return entry;
  }

  function openComments(key, button) {
    const review = config.figures[key];
    if (!review) return;
    activeKey = key;
    returnFocus = button || returnFocus;
    title.textContent = review.title;
    version.replaceChildren(document.createTextNode('Feedback on this figure version · '));
    const link = document.createElement('a');
    link.href = review.assets[0].path;
    link.textContent = 'View figure';
    link.target = '_blank';
    link.rel = 'noopener';
    version.append(link);
    for (const entry of frames.values()) entry.host.hidden = true;
    const entry = frames.get(key) || createFrame(key, review);
    entry.host.hidden = false;
    history.replaceState(null, '', cleanUrl(key));
    if (!dialog.open) dialog.showModal();
    dialog.scrollTop = 0;
  }

  window.addEventListener('message', event => {
    if (event.origin !== provider || !event.data || typeof event.data !== 'object') return;
    const data = event.data.giscus;
    if (!data || typeof data !== 'object') return;
    const match = [...frames].find(([,entry]) => entry.iframe.contentWindow === event.source);
    if (!match) return;
    const [,entry] = match;
    if (Number.isFinite(data.resizeHeight) && data.resizeHeight > 0) {
      entry.iframe.style.height = Math.min(data.resizeHeight, 100000) + 'px';
      clearTimeout(entry.timer);
      entry.status.hidden = true;
    }
    if (data.discussion || typeof data.error === 'string') clearTimeout(entry.timer);
    if (typeof data.error === 'string') {
      if (data.error.includes('Discussion not found')) {
        entry.status.hidden = true; // A new thread is created on the first submission.
      } else {
        entry.status.hidden = false;
        entry.status.textContent = 'Comments could not load. Please try again later.';
      }
    }
    if (data.signOut || (typeof data.error === 'string' &&
        /Bad credentials|Invalid state value|State has expired/.test(data.error))) {
      session = '';
      try { localStorage.removeItem('giscus-session'); } catch (_) {}
      for (const cached of frames.values()) {
        const url = new URL(cached.iframe.src);
        url.searchParams.delete('session');
        cached.iframe.src = url.href;
      }
    }
  });

  dialog.querySelector('.comment-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => {
    const url = new URL(location.href);
    if (url.hash === '#comments-' + activeKey) {
      url.hash = '';
      history.replaceState(null, '', url);
    }
    returnFocus?.focus();
  });

  for (const button of document.querySelectorAll('.figure-comments-button')) {
    const key = button.dataset.commentKey;
    buttons.set(key, button);
    button.addEventListener('click', () => openComments(key, button));
  }
  const initialKey = location.hash.startsWith('#comments-') ? location.hash.slice(10) : '';
  if (buttons.has(initialKey)) openComments(initialKey, buttons.get(initialKey));
  window.addEventListener('hashchange', () => {
    const key = location.hash.startsWith('#comments-') ? location.hash.slice(10) : '';
    if (buttons.has(key)) openComments(key, buttons.get(key));
  });
})();
