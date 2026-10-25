(() => {
  'use strict';
  const publicMode = document.documentElement.dataset.meetingMode === 'discussions';
  if (document.documentElement.dataset.ratingMode === 'deferred' && !publicMode) return;
  const config = JSON.parse(document.getElementById('gallery-comment-config').textContent);
  const cards = [...document.querySelectorAll('article')];
  const items = cards.map(card => ({card, key: card.querySelector('[data-comment-key]')?.dataset.commentKey,
    home: card.parentElement})).filter(item => item.key);
  const controls = new Map();
  let snapshot = null, busy = false, signedIn = false;
  const labels = {unreviewed: 'Not reviewed', priority: 'Priority', discuss: 'Discuss', later: 'Later', hidden: 'Hidden'};
  const panel = document.createElement('section');
  panel.className = 'meeting-panel';
  panel.setAttribute('aria-label', 'Figure meeting workspace');
  panel.innerHTML = '<h2>Figure meeting</h2><p>Work toward about 20–30 high-value figures, with a smaller priority set; these are goals, not enforced limits. Selections and notes are saved on this computer for the configured reviewers.</p><div class="meeting-toolbar"><label>View <select class="meeting-view"><option value="meeting">Discussion set</option><option value="priority">Priorities only</option><option value="library">Browse library</option><option value="unreviewed">Not reviewed</option><option value="later">Later</option><option value="hidden">Hidden / restore</option></select></label><button type="button" class="meeting-refresh">Refresh saved review</button><button type="button" class="meeting-json">Export JSON</button><button type="button" class="meeting-markdown">Export notes</button></div><p class="meeting-summary"></p><p class="meeting-status" role="status">Sign in above to save a meeting selection or note.</p><p class="meeting-empty"></p>';
  const main = document.querySelector('main');
  main.insertBefore(panel, main.querySelector('section'));
  const view = panel.querySelector('select');
  const status = panel.querySelector('[role=status]');
  const rejected = document.createElement('ul'); rejected.className = 'meeting-rejections'; rejected.hidden = true; panel.append(rejected);
  if (publicMode) {
    panel.querySelector('h2').textContent = 'Shared figure review';
    panel.querySelector('h2 + p').textContent = 'Rate how useful each figure is for discussion: 1 = not useful, 2 = needs work, 3 = useful, 4 = strong, 5 = essential. Ratings are separate from the discussion set and manuscript approval. Nick and Adrian curate the shared set.';
    const instructions = document.createElement('details'); instructions.className = 'review-instructions';
    instructions.innerHTML = '<summary>How to save a rating or selection</summary><ol><li>Choose a score or meeting selection on a figure. This prepares a comment; it does not save yet.</li><li>In the dialog, choose <strong>Copy rating text</strong> (or Copy text), paste it into the GitHub comment box, sign in if prompted, and post.</li><li>Your comment is saved on GitHub immediately. The shared score updates after the website rebuilds; choose <strong>Refresh saved review</strong> to load it.</li></ol><p>Each reviewer has one score per artwork version; their latest posted score replaces their earlier one. The summary shows the average and reviewer count. Preparing or copying text alone never changes a score.</p>';
    panel.querySelector('h2 + p').after(instructions);
    status.textContent = 'Loading saved GitHub review…';
  }
  const groups = {};
  for (const [name, title] of [['priority', 'Priorities'], ['discuss', 'Discussion figures']]) {
    const section = document.createElement('section');
    section.className = 'meeting-selection';
    const heading = document.createElement('h2'); heading.textContent = title;
    const grid = document.createElement('div'); grid.className = 'grid';
    section.append(heading, grid); panel.after(section);
    groups[name] = {section, grid};
  }
  // Keep the two meeting sections in their presentation order.
  groups.priority.section.after(groups.discuss.section);
  function entry(key) {return snapshot?.figures[key] || {state: 'unreviewed', position: 0, notes: []};}
  function selected(state) {return state === 'priority' || state === 'discuss';}
  function apply() {
    // Reuse the existing exact Figure/Gallery reference and topic search.
    window.filter();
    panel.hidden = false;
    const mode = view.value;
    let matching = items.filter(({card, key}) => {
      const state = entry(key).state;
      return !card.hidden && (mode === 'meeting' ? selected(state) : mode === 'priority' ? state === 'priority' :
        mode === 'library' ? state !== 'hidden' : state === mode);
    });
    if (mode === 'meeting' || mode === 'priority') {
      matching.sort((a, b) => (entry(a.key).state === 'priority' ? 0 : 1) - (entry(b.key).state === 'priority' ? 0 : 1) ||
        entry(a.key).position - entry(b.key).position);
    }
    const visible = new Set(matching);
    for (const item of items) item.card.hidden = !visible.has(item);
    // Move only cards whose presentation order changed. Notes and ratings do
    // not detach a playing video from its existing card.
    const parents = new Map();
    for (const item of items) {
      const parent = (mode === 'meeting' || mode === 'priority') && matching.includes(item) ? groups[entry(item.key).state].grid : item.home;
      if (!parents.has(parent)) parents.set(parent, []);
      parents.get(parent).push(item);
    }
    for (const [parent, children] of parents) {
      if (parent === groups.priority.grid || parent === groups.discuss.grid) children.sort((a, b) => entry(a.key).position - entry(b.key).position);
      children.forEach((item, index) => {if (parent.children[index] !== item.card) parent.insertBefore(item.card, parent.children[index] || null);});
    }
    for (const section of main.querySelectorAll(':scope > section')) {
      if (section !== panel) section.hidden = section.hasAttribute('data-reading-entry') ? false : ![...section.querySelectorAll('article')].some(card => !card.hidden);
    }
    const all = Object.values(snapshot?.figures || {});
    panel.querySelector('.meeting-summary').textContent = all.filter(e => e.state === 'priority').length + ' priorities · ' +
      all.filter(e => selected(e.state)).length + ' discussion figures · ' + all.filter(e => e.state === 'hidden').length + ' hidden';
    if (publicMode) {
      rejected.replaceChildren();
      for (const issue of snapshot?.ignored || []) {
        const item = document.createElement('li'); const link = document.createElement('a');
        link.href = issue.url; link.target = '_blank'; link.rel = 'noopener';
        link.textContent = (snapshot.metadata[issue.key]?.reference || 'Figure review') + ': ' + issue.reason;
        item.append(link); rejected.append(item);
      }
      rejected.hidden = !rejected.children.length;
    }
    panel.querySelector('.meeting-empty').textContent = matching.length ? '' :
      mode === 'meeting' ? 'No discussion figures yet. Choose Browse library and select Priority or Discuss on a card.' : 'No matching figures.';
    document.querySelector('#count').textContent = `${visible.size} shown · ${matching.length} match this view`;
    for (const button of panel.querySelectorAll('.meeting-refresh,.meeting-json,.meeting-markdown')) button.disabled = !signedIn || busy;
    for (const [key, control] of controls) {
      const data = entry(key);
      control.select.value = data.state;
      control.select.disabled = !signedIn || busy;
      for (const button of control.block.querySelectorAll('button')) button.disabled = !signedIn || busy;
      control.up.disabled ||= !selected(data.state);
      control.down.disabled ||= !selected(data.state);
      control.text.disabled = !signedIn;
      control.notes.replaceChildren();
      for (const note of data.notes) {
        const p = document.createElement('p');
        const author = document.createElement('strong'); author.textContent = note.reviewer + ' · ' + new Date(note.created * 1000).toLocaleString();
        const body = document.createElement('span'); body.textContent = note.body;
        p.append(author, document.createElement('br'), body);
        if (publicMode && note.url) {
          const link = document.createElement('a'); link.href = note.url; link.textContent = note.truncated ? 'Read full note on GitHub' : 'View on GitHub';
          link.target = '_blank'; link.rel = 'noopener'; p.append(document.createElement('br'), link);
        }
        control.notes.append(p);
      }
      control.count.textContent = `Meeting notes (${data.notes.length})`;
      if (control.rating) {
        const rating = data.rating || {count: 0, average: null};
        control.rating.textContent = rating.count ? `${rating.average.toFixed(1)}/5 from ${rating.count} reviewer${rating.count === 1 ? '' : 's'}` : 'No shared ratings yet';
        control.ratingHelp.textContent = control.pendingRating ? `Prepared: ${control.pendingRating}/5. Posting is not confirmed here. Paste and post it in Comments, refresh after the website updates, then clear this prepared score.` : 'Choose a score to prepare a GitHub comment. It is saved only after you post.';
        for (const star of control.stars.children) star.setAttribute('aria-pressed', String(Number(star.dataset.value) === control.pendingRating));
      }
    }
  }
  async function api(path, body) {
    if (publicMode) {
      if (body !== undefined) throw new Error('Post shared feedback through GitHub Comments.');
      const response = await fetch(document.documentElement.dataset.meetingUrl, {cache: 'no-store'});
      if (!response.ok) throw new Error('The shared review snapshot could not load. Try Refresh again.');
      const data = await response.json();
      if (data.repository !== config.repository || data.schema_version !== 1 || !data.figures) throw new Error('Unexpected shared review snapshot');
      if (path === 'meeting/export') return {schema_version: 1, scope: 'Public GitHub review; provisional selections, not manuscript approval',
        revision: data.revision, generated_utc: data.generated_utc,
        figures: Object.entries(data.figures).filter(([, entry]) => entry.state !== 'unreviewed' || entry.notes.length || entry.rating?.count).map(([key, entry]) => ({key, ...data.metadata[key], ...entry}))};
      return data;
    }
    const response = await fetch('/api/' + path, {credentials: 'same-origin', cache: 'no-store',
      ...(body === undefined ? {} : {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Meeting service unavailable');
    return data;
  }
  async function refresh() {
    try {
      snapshot = await api('meeting'); signedIn = true;
      status.textContent = publicMode ? 'GitHub review synced ' + new Date(snapshot.generated_utc).toLocaleString() + '. New comments appear here after the site updates.' +
        (snapshot.ignored.length ? ' ' + snapshot.ignored.length + ' selection command(s) were not applied; see the notes below.' : '') : 'Saved meeting review loaded. Refresh to see edits from another open page.';
    } catch (error) {
      snapshot = null; signedIn = false; status.textContent = error.message;
    }
    apply();
  }
  async function save(key, changes, control) {
    if (publicMode) {
      const draft = changes.action === 'note' ? changes.body : changes.action === 'rating' ? 'Rating: ' + changes.value :
        'Meeting: ' + (changes.action === 'move' ? changes.direction : changes.state);
      if (changes.action === 'rating') control.pendingRating = changes.value;
      window.dispatchEvent(new CustomEvent('gallery-open-comments', {detail: {key, draft}}));
      status.textContent = 'Prepared for Comments. Paste and post with GitHub to save; Refresh this view after the site updates.';
      apply(); return;
    }
    if (busy || !signedIn) return;
    busy = true; status.textContent = 'Saving…'; apply();
    try {
      snapshot = await api('meeting', {key, revision: snapshot.revision, ...changes});
      if (changes.action === 'note') control.text.value = '';
      status.textContent = 'Saved on this computer.';
    } catch (error) {status.textContent = error.message;}
    finally {busy = false; apply();}
    if (!control.block.closest('article').hidden) control.select.focus();
    else view.focus();
  }
  for (const {card, key} of items) {
    const block = document.createElement('div'); block.className = 'meeting-card';
    const label = document.createElement('label'); label.textContent = 'Meeting selection ';
    const select = document.createElement('select');
    select.setAttribute('aria-label', 'Meeting selection for ' + config.figures[key].title);
    for (const [state, title] of Object.entries(labels)) {const option = document.createElement('option'); option.value = state; option.textContent = title; select.append(option);}
    label.append(select);
    const order = document.createElement('div'); order.className = 'meeting-order';
    const up = document.createElement('button'); up.type = 'button'; up.textContent = 'Move earlier';
    const down = document.createElement('button'); down.type = 'button'; down.textContent = 'Move later'; order.append(up, down);
    const details = document.createElement('details');
    const count = document.createElement('summary'); count.textContent = 'Meeting notes (0)';
    const notes = document.createElement('div'); notes.className = 'meeting-notes';
    const noteLabel = document.createElement('label'); noteLabel.textContent = 'Add a note';
    const text = document.createElement('textarea'); text.maxLength = 4000; text.rows = 3;
    text.setAttribute('aria-label', 'Meeting note for ' + config.figures[key].title); noteLabel.append(text);
    const saveButton = document.createElement('button'); saveButton.type = 'button'; saveButton.textContent = publicMode ? 'Post note in Comments' : 'Save note';
    const noteStatus = document.createElement('p'); noteStatus.className = 'meeting-note-status'; noteStatus.setAttribute('role', 'status');
    text.addEventListener('input', () => {noteStatus.textContent = text.value ? (publicMode ? 'Draft — choose Post note in Comments, then paste and post with GitHub.' : 'Draft — choose Save note to keep it.') : '';});
    details.append(count, notes, noteLabel, saveButton, noteStatus); block.append(label, order, details);
    const control = {block, select, up, down, notes, text, count}; controls.set(key, control);
    if (publicMode) {
      const ratingBlock = document.createElement('div'); ratingBlock.className = 'figure-rating';
      const rating = document.createElement('p'); rating.className = 'rating-summary'; control.rating = rating;
      const stars = document.createElement('div'); stars.className = 'rating-stars';
      stars.setAttribute('role', 'group'); stars.setAttribute('aria-label', 'Prepare a usefulness rating'); control.stars = stars;
      const meanings = ['Not useful', 'Needs work', 'Useful', 'Strong', 'Essential'];
      for (let value = 1; value <= 5; value++) {
        const star = document.createElement('button'); star.type = 'button'; star.className = 'rating-star'; star.textContent = value + ' · ' + meanings[value - 1]; star.dataset.value = value;
        star.setAttribute('aria-label', `Prepare ${value} of 5: ${meanings[value - 1]} for ${config.figures[key].title}`);
        star.setAttribute('aria-pressed', 'false');
        star.onclick = () => save(key, {action: 'rating', value}, control); stars.append(star);
      }
      const help = document.createElement('p'); help.className = 'rating-status'; help.setAttribute('role', 'status'); control.ratingHelp = help;
      const clearScore = document.createElement('button'); clearScore.type = 'button'; clearScore.textContent = 'Clear prepared score';
      clearScore.onclick = () => {control.pendingRating = null; apply();};
      ratingBlock.append(rating, stars, help, clearScore); block.prepend(ratingBlock);
      const clear = document.createElement('button'); clear.type = 'button'; clear.textContent = 'Clear draft';
      clear.onclick = () => {text.value = ''; noteStatus.textContent = '';}; details.append(clear);
    }
    select.onchange = () => save(key, {action: 'state', state: select.value}, control);
    up.onclick = () => save(key, {action: 'move', direction: 'up'}, control);
    down.onclick = () => save(key, {action: 'move', direction: 'down'}, control);
    saveButton.onclick = async () => {
      if (!text.value.trim()) {noteStatus.textContent = 'Write a note before saving.'; return;}
      await save(key, {action: 'note', body: text.value}, control);
      noteStatus.textContent = publicMode ? 'Draft retained. Post in Comments to save it; clear this draft when finished.' : text.value ? 'Draft retained. Check the workspace status above.' : 'Note saved.';
    };
    card.querySelector('.figure-comments-button').before(block);
  }
  view.onchange = apply;
  for (const selector of ['#search', '#theme']) document.querySelector(selector).addEventListener(selector === '#search' ? 'input' : 'change', apply);
  panel.querySelector('.meeting-refresh').onclick = refresh;
  async function download(markdown) {
    try {
      const data = await api('meeting/export');
      let content = JSON.stringify(data, null, 2) + '\n';
      if (markdown) {
        const lines = ['# Early Earth figure meeting', '', data.scope, ''];
        for (const state of ['priority', 'discuss', 'later', 'hidden', 'unreviewed']) {
          const figures = data.figures.filter(f => f.state === state).sort((a, b) => a.position - b.position);
          if (!figures.length) continue;
          lines.push('## ' + labels[state], '');
          for (const figure of figures) {
            lines.push('### ' + figure.reference, '', 'Source: ' + figure.source_group, 'Artwork SHA-256: ' + figure.artwork_sha256, '');
            for (const note of figure.notes) lines.push(note.reviewer + ' · ' + new Date(note.created * 1000).toISOString(), '', note.body, '');
          }
        }
        content = lines.join('\n');
      }
      const url = URL.createObjectURL(new Blob([content], {type: markdown ? 'text/markdown' : 'application/json'}));
      const link = document.createElement('a'); link.href = url; link.download = 'early-earth-meeting.' + (markdown ? 'md' : 'json'); link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      status.textContent = publicMode ? 'Shared GitHub review exported.' : 'Meeting review exported. The saved workspace remains on this computer.';
    } catch (error) {status.textContent = error.message;}
  }
  panel.querySelector('.meeting-json').onclick = () => download(false);
  panel.querySelector('.meeting-markdown').onclick = () => download(true);
  window.addEventListener('gallery-reviewer', event => {
    if (event.detail.reviewer) refresh();
    else {signedIn = false; snapshot = null; status.textContent = 'Sign in above to open the saved meeting review.'; apply();}
  });
  window.addEventListener('beforeunload', event => {
    if ([...controls.values()].some(c => c.text.value.trim())) {event.preventDefault(); event.returnValue = '';}
  });
  // Direct figure anchors open in the library so links also find set-aside cards.
  view.value = location.hash ? 'library' : 'meeting';
  refresh().then(() => {
    if (location.hash) {
      const target = items.find(item => '#' + item.card.id === location.hash);
      if (target) {view.value = entry(target.key).state === 'hidden' ? 'hidden' : 'library';
        apply(); target.card.scrollIntoView();}
    } else if (!snapshot || !Object.values(snapshot.figures).some(e => selected(e.state))) {view.value = 'library'; apply();}
  });
})();
