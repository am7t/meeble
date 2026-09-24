const STORAGE_KEY = 'meeble.showcase.v1';

const initialState = {
  posts: [
    { id: 'p1', author: 'jules parker', handle: '@jules.jpg', avatar: 'J', avatarClass: 'avatar-jules', time: '12 min ago', caption: 'Found the tiniest coffee shop tucked away on Bleecker and I think I live here now ☕', art: 'cafe', artLabel: 'slow mornings ♡', likes: 28, liked: false, comments: [{ name: 'amelia rose', text: 'adding this to our list immediately' }, { name: 'nina james', text: 'the coffee is SO good here' }] },
    { id: 'p2', author: 'lila chen', handle: '@lilachen', avatar: 'L', avatarClass: 'avatar-lila', time: '1 hr ago', caption: 'sunday looked a little something like this 🌞', art: 'sunday', artLabel: 'soft days, soft light', likes: 42, liked: false, comments: [{ name: 'maya flowers', text: 'this light!!!' }] },
    { id: 'p3', author: 'nina james', handle: '@nina.j', avatar: 'N', avatarClass: 'avatar-nina', time: '3 hrs ago', caption: 'a little reminder that the flowers you buy yourself count the most 💐', art: 'flowers', artLabel: 'little joys', likes: 36, liked: false, comments: [] }
  ],
  hidden: []
};

function loadState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (saved && Array.isArray(saved.posts)) {
      const posts = saved.posts.filter((post) => post && typeof post === 'object' && typeof post.id === 'string')
        .map((post) => ({
          id: post.id.slice(0, 80),
          author: typeof post.author === 'string' ? post.author.slice(0, 80) : 'a meeble friend',
          handle: typeof post.handle === 'string' ? post.handle.slice(0, 80) : '@friend',
          avatar: typeof post.avatar === 'string' ? post.avatar.slice(0, 2) : 'M',
          avatarClass: ['avatar-self', 'avatar-jules', 'avatar-lila', 'avatar-nina', 'avatar-maya'].includes(post.avatarClass) ? post.avatarClass : 'avatar-self',
          time: typeof post.time === 'string' ? post.time.slice(0, 40) : 'a little while ago',
          caption: typeof post.caption === 'string' ? post.caption.slice(0, 500) : '',
          art: ['cafe', 'sunday', 'flowers', 'custom'].includes(post.art) ? post.art : 'custom',
          artLabel: typeof post.artLabel === 'string' ? post.artLabel.slice(0, 80) : '',
          likes: Number.isSafeInteger(post.likes) ? Math.max(0, Math.min(post.likes, 1000000)) : 0,
          liked: post.liked === true,
          comments: Array.isArray(post.comments) ? post.comments.filter((comment) => comment && typeof comment.name === 'string' && typeof comment.text === 'string').slice(-200).map((comment) => ({ name: comment.name.slice(0, 80), text: comment.text.slice(0, 240) })) : []
        }));
      const hidden = Array.isArray(saved.hidden) ? saved.hidden.filter((id) => typeof id === 'string').slice(0, 500) : [];
      return { posts, hidden };
    }
  } catch (error) { console.warn('Meeble could not read saved demo data; starting with the sample feed.', error); }
  return structuredClone(initialState);
}

let state = loadState();
const feed = document.querySelector('#feed');

function saveState() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
  catch (error) { showToast('Your browser could not save this change. Check available site storage and try again.'); }
}

function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
}

function postTemplate(post) {
  const art = post.art === 'custom' ? 'custom' : post.art;
  const caption = escapeHTML(post.caption).replace(/(^|\s)(#[\p{L}\p{N}_]+)/gu, '$1<span class="hashtag">$2</span>');
  return `<article class="post-card" data-id="${escapeHTML(post.id)}">
    <div class="post-top"><span class="avatar ${escapeHTML(post.avatarClass || 'avatar-self')}">${escapeHTML(post.avatar || 'M')}</span><div class="post-author"><strong>${escapeHTML(post.author)}</strong><small>${escapeHTML(post.handle)} · ${escapeHTML(post.time)}</small></div><button class="post-menu" aria-label="Post options" data-action="menu">···</button></div>
    <p class="post-caption"><strong>${escapeHTML(post.author.split(' ')[0])}</strong> ${caption}</p>
    <div class="post-art ${art}" role="img" aria-label="Decorative illustration for ${escapeHTML(post.author)}'s post">${art === 'cafe' ? `<span class="coffee-cup"></span>` : ''}<span class="art-label">${escapeHTML(post.artLabel || '')}</span></div>
    <div class="post-actions"><button class="action-btn ${post.liked ? 'liked' : ''}" data-action="like" aria-label="${post.liked ? 'Unlike' : 'Like'} post"><span>${post.liked ? '♥' : '♡'}</span> ${post.likes}</button><button class="action-btn" data-action="focus-comment"><span>◯</span> ${post.comments.length || ''}</button><span class="action-spacer"></span><span class="post-time">a little moment ago</span></div>
    <div class="comments-area">${post.comments.map((comment) => `<div class="comment"><strong>${escapeHTML(comment.name)}</strong>${escapeHTML(comment.text)}</div>`).join('')}<form class="comment-form"><input name="comment" maxlength="240" aria-label="Write a comment" placeholder="Leave a little love…" required><button type="submit">Post</button></form></div>
  </article>`;
}

function render() {
  const visiblePosts = state.posts.filter((post) => !state.hidden.includes(post.id));
  feed.innerHTML = visiblePosts.map(postTemplate).join('') || '<div class="empty-feed"><span>♡</span><h3>Your feed is waiting for a little love.</h3><p>Create a post to get things started.</p></div>';
}

const stories = [
  { name: 'Your story', avatar: 'A', cls: 'avatar-self', own: true },
  { name: 'jules', avatar: 'J', cls: 'avatar-jules' },
  { name: 'lila', avatar: 'L', cls: 'avatar-lila' },
  { name: 'maya', avatar: 'M', cls: 'avatar-maya' },
  { name: 'nina', avatar: 'N', cls: 'avatar-nina' },
  { name: 'sophie', avatar: 'S', cls: 'avatar-lila' },
  { name: 'ella', avatar: 'E', cls: 'avatar-jules' }
];

document.querySelector('#storiesRow').innerHTML = stories.map((story) => `<button class="story ${story.own ? 'is-own' : ''}" data-story="${escapeHTML(story.name)}" aria-label="${story.own ? 'Add to your story' : `View ${story.name}'s story`}"><span class="story-ring"><span class="avatar ${story.cls}">${story.avatar}</span>${story.own ? '<span class="story-add">+</span>' : ''}</span><span class="story-name">${escapeHTML(story.name)}</span></button>`).join('');

document.querySelector('#friendsList').innerHTML = [stories[1], stories[2], stories[3]].map((friend, index) => `<div class="friend-row"><span class="avatar ${friend.cls}">${friend.avatar}</span><span class="friend-info"><strong>${friend.name === 'jules' ? 'Jules Parker' : friend.name === 'lila' ? 'Lila Chen' : 'Maya Flowers'}</strong><small>${['probably at a cafe ☕', 'in her soft era ✿', 'sending you a hug ♡'][index]}</small></span><span class="online"></span></div>`).join('');

function showToast(message) {
  const dialog = document.querySelector('#toastDialog');
  document.querySelector('#toastMessage').textContent = message;
  dialog.showModal();
}

feed.addEventListener('click', (event) => {
  const button = event.target.closest('[data-action]');
  if (!button) return;
  const card = button.closest('.post-card');
  const post = state.posts.find((item) => item.id === card?.dataset.id);
  if (!post) return;
  if (button.dataset.action === 'like') {
    post.liked = !post.liked;
    post.likes = Math.max(0, post.likes + (post.liked ? 1 : -1));
    saveState(); render();
  } else if (button.dataset.action === 'focus-comment') card.querySelector('[name="comment"]').focus();
  else if (button.dataset.action === 'menu') {
    const remove = confirm('Hide this post from your local demo feed?');
    if (remove) { state.hidden.push(post.id); saveState(); render(); }
  }
});

feed.addEventListener('submit', (event) => {
  if (!event.target.matches('.comment-form')) return;
  event.preventDefault();
  const card = event.target.closest('.post-card');
  const post = state.posts.find((item) => item.id === card.dataset.id);
  const input = event.target.elements.comment;
  const text = input.value.trim();
  if (!post || !text) return;
  post.comments.push({ name: 'amelia rose', text });
  saveState(); render();
});

const composer = document.querySelector('#composer');
document.querySelector('#openComposer').addEventListener('click', () => composer.showModal());
document.querySelector('#postForm').addEventListener('submit', (event) => {
  event.preventDefault();
  const caption = document.querySelector('#postCaption').value.trim();
  if (!caption) return;
  state.posts.unshift({ id: `p${Date.now()}`, author: 'amelia rose', handle: '@amelia.rose', avatar: 'A', avatarClass: 'avatar-self', time: 'just now', caption, art: 'custom', artLabel: 'a little moment ♡', likes: 0, liked: false, comments: [] });
  saveState(); render(); composer.close(); event.target.reset();
  document.querySelector('#feed').scrollIntoView({ behavior: 'smooth', block: 'start' });
});
document.querySelector('#addPhoto').addEventListener('click', () => showToast('Photo sharing is coming soon. Your demo feed is ready for your words ♡'));
document.querySelector('#toastClose').addEventListener('click', () => document.querySelector('#toastDialog').close());
document.querySelector('#storiesRow').addEventListener('click', (event) => {
  const story = event.target.closest('[data-story]');
  if (story) showToast(story.dataset.story === 'Your story' ? 'Story sharing is coming soon — your little moments will live here.' : `${story.dataset.story}’s story is part of the sample feed. More moments coming soon ♡`);
});
document.querySelectorAll('[data-page]').forEach((button) => button.addEventListener('click', () => {
  const page = button.dataset.page;
  if (page === 'home') return;
  showToast(page === 'profile' ? 'Your profile is being made extra you. Coming soon ♡' : `${page[0].toUpperCase() + page.slice(1)} is coming soon. This is just the beginning ♡`);
}));
document.querySelector('#viewAllStories').addEventListener('click', () => showToast('You’re all caught up on little moments ♡'));
document.querySelectorAll('.filter').forEach((filter) => filter.addEventListener('click', () => {
  document.querySelectorAll('.filter').forEach((item) => item.classList.toggle('active', item === filter));
  if (filter.textContent.trim() === 'Following') showToast('You’re seeing posts from your people ♡');
}));
document.querySelector('.notification-button').addEventListener('click', () => showToast('You’re all caught up. We’ll save the good news for you ♡'));
document.querySelector('.search-button').addEventListener('click', () => showToast('Search is coming soon. Your people are easy to find ♡'));
document.querySelector('.birthday-person button').addEventListener('click', () => showToast('Birthday wishes are on their way ♡'));
document.querySelector('.find-friends').addEventListener('click', () => showToast('Finding your people is coming soon ♡'));
document.querySelector('#loadMore').addEventListener('click', () => showToast('You’re all caught up on the good stuff ♡'));

render();
