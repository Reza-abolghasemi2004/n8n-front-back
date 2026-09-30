document.addEventListener("DOMContentLoaded", () => {
  // Mobile sidebar toggle
  const menuBtn = document.getElementById("mobile-menu-btn");
  const sidebar = document.getElementById("app-sidebar");
  if (menuBtn && sidebar) {
    menuBtn.addEventListener("click", () => {
      sidebar.classList.toggle("open");
    });
  }

  // Toast notifications auto-dismiss
  const toasts = document.querySelectorAll(".toast");
  toasts.forEach((toast) => {
    const closeBtn = toast.querySelector(".toast-close");
    if (closeBtn) {
      closeBtn.addEventListener("click", () => toast.remove());
    }
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transition = "opacity 0.25s ease";
      setTimeout(() => toast.remove(), 260);
    }, 5500);
  });

  // Confirmation dialogs for destructive forms
  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      const message = form.getAttribute("data-confirm") || "Are you sure?";
      if (!window.confirm(message)) {
        event.preventDefault();
      }
    });
  });

  // Loading states on form submission
  document.querySelectorAll("form[data-loading-form]").forEach((form) => {
    form.addEventListener("submit", () => {
      if (form.defaultPrevented) return;
      const submitBtn = form.querySelector("button[type='submit']");
      if (submitBtn && !submitBtn.classList.contains("is-loading")) {
        const loadingText = submitBtn.getAttribute("data-loading-text") || "Processing...";
        submitBtn.classList.add("is-loading");
        submitBtn.innerHTML = `<span class="spinner"></span><span>${loadingText}</span>`;
      }
    });
  });

  // Copy to clipboard helper
  document.querySelectorAll("[data-copy]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const value = btn.getAttribute("data-copy");
      if (!value || !navigator.clipboard) return;
      try {
        await navigator.clipboard.writeText(value);
        const original = btn.innerHTML;
        btn.textContent = "Copied!";
        setTimeout(() => {
          btn.innerHTML = original;
        }, 1400);
      } catch (_) {
        // Ignore clipboard permission errors
      }
    });
  });
});
