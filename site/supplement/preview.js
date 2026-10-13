(() => {
  'use strict';
  const configNode = document.getElementById('gallery-comment-config');
  if (!configNode) return;
  const config = JSON.parse(configNode.textContent);
  const widgets = new Map();
  let reviewer = null;
  let pending = false;
  let setupRequired = false;

  const imageDialog = document.createElement('dialog');
  imageDialog.className = 'image-dialog';
  imageDialog.setAttribute('aria-labelledby', 'image-title');
  imageDialog.innerHTML = '<div class="image-heading"><h2 id="image-title"></h2><button class="image-close" type="button">Close</button></div><img alt=""><a class="image-original" target="_blank" rel="noopener">Open original image</a>';
  document.body.append(imageDialog);
  let imageFocus;
  function openImage(anchor, img) {
    imageFocus = anchor;
    const reference = anchor.closest('article')?.dataset.galleryReference;
    imageDialog.querySelector('h2').textContent = (reference ? reference + ' — ' : '') + img.alt;
    imageDialog.querySelector('img').src = img.src;
    imageDialog.querySelector('img').alt = img.alt;
    imageDialog.querySelector('a').href = anchor.href;
    imageDialog.showModal();
    imageDialog.querySelector('button').focus();
  }
  imageDialog.querySelector('button').addEventListener('click', () => imageDialog.close());
  imageDialog.addEventListener('click', event => { if (event.target === imageDialog) {
    const rect = imageDialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) imageDialog.close();
  }});
  imageDialog.addEventListener('close', () => {imageDialog.querySelector('img').removeAttribute('src'); imageFocus?.focus();});
  for (const anchor of document.querySelectorAll('.preview a')) {
    const img = anchor.querySelector('img');
    if (!img) continue;
    anchor.setAttribute('aria-haspopup', 'dialog');
    anchor.setAttribute('aria-label', 'Enlarge ' + img.alt);
    anchor.addEventListener('click', event => {
      if (event.button || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault(); openImage(anchor, img);
    });
  }

  // A static publication has no local ratings service. D25 owns shared storage/access.
  if (document.documentElement.dataset.ratingMode === 'deferred') return;

  const access = document.createElement('div');
  access.className = 'review-access';
  access.innerHTML = '<span role="status">Connecting to local ratings…</span><button type="button">Sign in to rate</button>';
  document.querySelector('header').append(access);
  const login = document.createElement('dialog');
  login.className = 'review-login';
  login.setAttribute('aria-labelledby', 'review-login-title');
  login.innerHTML = '<form><h2 id="review-login-title">Local reviewer sign-in</h2><p>Use the reviewer account configured by the preview owner. Ratings are saved on this computer.</p><label>Reviewer<input name="reviewer" autocomplete="username" required maxlength="80"></label><label>Password<input name="password" type="password" autocomplete="current-password" required></label><p role="status"></p><button type="submit">Sign in</button> <button type="button">Cancel</button></form>';
  document.body.append(login);
  login.querySelector('[type=button]').onclick = () => login.close();
  login.addEventListener('close', () => {login.querySelector('[name=password]').value = ''; access.querySelector('button').focus();});
  async function api(path, body) {
    const response = await fetch('/api/' + path, {credentials:'same-origin', cache:'no-store',
      ...(body === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Ratings service unavailable');
    return data;
  }
  function render(data) {
    reviewer = data.reviewer;
    setupRequired = Boolean(data.setup_required);
    access.querySelector('span').textContent = reviewer ? 'Rating as ' + reviewer + ' · saved on this computer' : setupRequired ? 'Local ratings · create your first reviewer account' : 'Local ratings · sign in with a configured reviewer account';
    access.querySelector('button').textContent = reviewer ? 'Sign out' : setupRequired ? 'Set up local reviewer' : 'Sign in to rate';
    for (const [key, widget] of widgets) {
      const rating = data.ratings[key] || {count:0, average:null, mine:null};
      widget.summary.textContent = (rating.count ? rating.average.toFixed(1) + '/5 from ' + rating.count + ' reviewer' + (rating.count === 1 ? '' : 's') : 'No ratings yet') + (rating.mine ? ' · Your rating: ' + rating.mine + '/5' : '');
      for (const button of widget.buttons) {
        button.disabled = !reviewer || pending;
        button.setAttribute('aria-pressed', String(Number(button.dataset.value) === rating.mine));
        button.textContent = Number(button.dataset.value) <= (rating.mine || 0) ? '★' : '☆';
      }
    }
  }
  async function refresh() {render(await api('ratings'));}
  access.querySelector('button').onclick = async () => {
    if (!reviewer) {
      login.querySelector('[role=status]').textContent = '';
      login.querySelector('h2').textContent = setupRequired ? 'Create your local reviewer account' : 'Local reviewer sign-in';
      login.querySelector('form>p').textContent = setupRequired ? 'Choose a reviewer name and password (at least 8 characters). Ratings are saved on this computer. The preview owner can add more reviewers.' : 'Use the reviewer account configured by the preview owner. Ratings are saved on this computer.';
      login.querySelector('[type=submit]').textContent = setupRequired ? 'Create reviewer' : 'Sign in';
      login.querySelector('[name=password]').minLength = setupRequired ? 8 : 0;
      login.showModal(); return;
    }
    try {await api('logout', {}); await refresh();} catch (error) {access.querySelector('span').textContent = error.message;}
  };
  login.querySelector('form').onsubmit = async event => {
    event.preventDefault();
    const form = event.currentTarget;
    try {await api(setupRequired ? 'setup' : 'login', {reviewer:form.elements.reviewer.value, password:form.elements.password.value}); login.close(); await refresh();}
    catch (error) {login.querySelector('[role=status]').textContent = error.message;}
  };
  for (const commentButton of document.querySelectorAll('.figure-comments-button')) {
    const key = commentButton.dataset.commentKey;
    if (!config.figures[key]) continue;
    const block = document.createElement('div');
    block.className = 'figure-rating';
    block.innerHTML = '<div class="rating-stars" role="group"></div><p class="rating-summary"></p><p class="rating-status" role="status"></p>';
    const stars = block.querySelector('.rating-stars');
    stars.setAttribute('aria-label', 'Rate ' + config.figures[key].title);
    const widget = {buttons:[], summary:block.querySelector('.rating-summary'), status:block.querySelector('.rating-status')};
    widgets.set(key, widget);
    for (let value = 1; value <= 5; value++) {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'rating-star'; button.dataset.value = value;
      button.textContent = '★'; button.disabled = true;
      button.setAttribute('aria-label', value + (value === 1 ? ' star' : ' stars'));
      button.setAttribute('aria-pressed', 'false');
      stars.append(button); widget.buttons.push(button);
      button.onclick = async () => {
        if (pending) return;
        pending = true;
        for (const entry of widgets.values()) for (const star of entry.buttons) star.disabled = true;
        widget.status.textContent = 'Saving…';
        try {
          const data = await api('rate', {key, value});
          pending = false; render(data);
          widget.status.textContent = 'Saved. Choosing another star replaces your previous rating.';
        } catch (error) {
          pending = false; widget.status.textContent = error.message;
          try {await refresh();} catch (_) {access.querySelector('span').textContent = 'Local ratings service unavailable. Start the preview server.';}
        }
      };
    }
    commentButton.before(block);
  }
  refresh().catch(() => {
    access.querySelector('span').textContent = 'Start the local preview server to save ratings.';
    access.querySelector('button').disabled = true;
    for (const widget of widgets.values()) widget.summary.textContent = 'Ratings unavailable until the local server starts.';
  });
})();
