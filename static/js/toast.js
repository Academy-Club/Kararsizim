document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".toast").forEach((toast) => {
    setTimeout(() => toast.remove(), 3000);
  });
});
