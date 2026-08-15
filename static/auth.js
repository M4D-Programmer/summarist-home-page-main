document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('auth-modal');
  if (!modal) return;

  const openButtons = document.querySelectorAll('[data-open-auth="true"]');
  const closeButton = modal.querySelector('.auth-modal__close');
  const form = modal.querySelector('form');
  const actionInput = document.getElementById('auth-action');
  const guestButton = modal.querySelector('[data-guest-login="true"]');

  const showModal = () => modal.classList.remove('hidden');
  const hideModal = () => modal.classList.add('hidden');

  openButtons.forEach((button) => button.addEventListener('click', showModal));
  closeButton.addEventListener('click', hideModal);
  modal.addEventListener('click', (event) => {
    if (event.target === modal) hideModal();
  });

  document.querySelectorAll('[data-auth-mode]').forEach((button) => {
    button.addEventListener('click', () => {
      const mode = button.dataset.authMode;
      actionInput.value = mode;
      form.querySelector('button[type="submit"]').textContent = mode === 'register' ? 'Register' : 'Login';
      const title = modal.querySelector('h2');
      title.textContent = mode === 'register' ? 'Create your account' : 'Welcome back';
    });
  });

  guestButton.addEventListener('click', () => {
    const emailInput = form.querySelector('input[name="email"]');
    const passwordInput = form.querySelector('input[name="password"]');
    emailInput.value = 'guest@gmail.com';
    passwordInput.value = 'guest123';
    actionInput.value = 'login';
    form.submit();
  });
});
