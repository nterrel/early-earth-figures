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
  const resolvedHosts = new Map();
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
  const prepared = document.createElement('div');
  prepared.className = 'comment-prepared'; prepared.hidden = true;
  prepared.innerHTML = '<p>Copy this text, paste it into the comment box below, then post with GitHub. The shared gallery view updates after publication.</p><textarea readonly aria-label="Prepared review comment" rows="3" style="box-sizing:border-box;width:100%"></textarea><button type="button">Copy text</button><p role="status"></p>';
  frameContainer.before(prepared);
  prepared.querySelector('button').onclick = async () => {
    try {await navigator.clipboard.writeText(prepared.querySelector('textarea').value); prepared.querySelector('[role=status]').textContent = 'Copied. Paste into the comment box below and post.';}
    catch (_) {prepared.querySelector('textarea').select(); prepared.querySelector('[role=status]').textContent = 'Select and copy the text, then paste into the comment box below.';}
  };

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
      categoryId: config.category_id, term: review.identity_term || review.term,
      description: 'Figure: ' + review.title + '\nReviewed artwork SHA-256: ' + review.version +
        '\nFiles: ' + review.assets.map(asset => asset.path).join(', ') +
        (review.identity_term ? '\n<!-- early-earth-review: ' + review.identity_term + ' -->\n<!-- sha1: ' + review.identity_sha1 + ' -->' : ''),
      backLink: cleanUrl(key).href, strict: '1', reactionsEnabled: '0',
      emitMetadata: '1', inputPosition: 'top', theme: 'light',
    });
    iframe.src = provider + '/en/widget?' + params;
    host.append(iframe);
    frameContainer.append(host);
    const entry = {host, iframe, status, timer:null, review, readableLookup:false};
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

  async function openComments(key, button, draft = '') {
    const review = config.figures[key];
    if (!review) return;
    activeKey = key;
    prepared.hidden = !draft;
    prepared.querySelector('textarea').value = draft;
    prepared.querySelector('[role=status]').textContent = '';
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
    for (const host of resolvedHosts.values()) host.hidden = true;
    history.replaceState(null, '', cleanUrl(key));
    if (!dialog.open) dialog.showModal();
    dialog.scrollTop = 0;
    let resolved = null;
    if (config.feedback_status_url) {
      try {
        const response = await fetch(config.feedback_status_url, {cache: 'no-store', signal: AbortSignal.timeout(3000)});
        if (response.ok) {
          const state = await response.json();
          if (state.repository === config.repository) resolved = state.threads?.[review.identity_term || review.term] || state.threads?.[review.term];
        }
      } catch (_) { /* Keep feedback available when the status snapshot cannot load. */ }
    }
    if (activeKey !== key || !dialog.open) return;
    if (resolved?.closed === true && /^https:\/\/github\.com\/nterrel\/early-earth-figures\/discussions\/\d+$/.test(resolved.url)) {
      let host = resolvedHosts.get(key);
      if (!host) {
        host = document.createElement('p');
        host.className = 'comment-resolved';
        host.textContent = 'Resolved feedback is hidden. ';
        const archive = document.createElement('a');
        archive.href = resolved.url;
        archive.target = '_blank';
        archive.rel = 'noopener';
        archive.textContent = 'View discussion history on GitHub';
        host.append(archive);
        frameContainer.append(host);
        resolvedHosts.set(key, host);
      }
      host.hidden = false;
      return;
    }
    const entry = frames.get(key) || createFrame(key, review);
    entry.host.hidden = false;
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
        entry.status.hidden = true;
        // First find legacy feedback, including readable threads carrying the
        // original hidden strict-match marker. Only a confirmed absence permits
        // the readable creation term. Other provider errors never switch identity.
        if (entry.review.identity_term && !entry.readableLookup) {
          entry.readableLookup = true;
          const url = new URL(entry.iframe.src);
          url.searchParams.set('term', entry.review.term);
          entry.iframe.src = url.href;
        }
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
  window.addEventListener('gallery-open-comments', event => {
    const {key, draft} = event.detail || {};
    if (buttons.has(key) && typeof draft === 'string') openComments(key, buttons.get(key), draft);
  });
  if (buttons.has(initialKey)) openComments(initialKey, buttons.get(initialKey));
  window.addEventListener('hashchange', () => {
    const key = location.hash.startsWith('#comments-') ? location.hash.slice(10) : '';
    if (buttons.has(key)) openComments(key, buttons.get(key));
  });
})();
