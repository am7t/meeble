const followButton = document.querySelector('#profileFollow');

if (followButton) {
  followButton.addEventListener('click', async () => {
    followButton.disabled = true;
    const message = document.querySelector('#profileFollowMessage');
    message.hidden = true;
    try {
      const response = await fetch(followButton.dataset.followUrl, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          Accept: 'application/json',
          'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        }
      });
      let payload = {};
      try { payload = await response.json(); } catch (error) { /* Use the friendly fallback below. */ }
      if (!response.ok) throw new Error(payload.error || 'That follow could not be saved. Try again.');
      followButton.setAttribute('aria-pressed', String(payload.following));
      followButton.classList.toggle('is-following', payload.following);
      followButton.textContent = payload.following ? 'Following' : 'Follow';
      document.querySelector('#profileFollowerCount').textContent = payload.follower_count;
    } catch (error) {
      message.textContent = error.message || 'That follow could not be saved. Try again.';
      message.hidden = false;
    } finally {
      followButton.disabled = false;
    }
  });
}
