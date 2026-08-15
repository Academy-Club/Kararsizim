document.addEventListener("DOMContentLoaded", () => {
  const rowsContainer = document.getElementById("option-rows");
  const addButton = document.getElementById("add-option");
  if (!rowsContainer || !addButton) return;

  const MIN_OPTIONS = 2;
  const MAX_OPTIONS = 5;

  function rows() {
    return Array.from(rowsContainer.querySelectorAll(".option-row-input"));
  }

  function refreshControls() {
    const count = rows().length;
    addButton.disabled = count >= MAX_OPTIONS;
    rowsContainer.querySelectorAll(".option-row-input__remove").forEach((button) => {
      button.disabled = count <= MIN_OPTIONS;
    });
  }

  function addRow() {
    if (rows().length >= MAX_OPTIONS) return;
    const index = rows().length + 1;
    const row = document.createElement("div");
    row.className = "option-row-input";
    row.innerHTML =
      '<input type="text" name="option" maxlength="80" class="option-input" placeholder="Seçenek ' +
      index +
      '">' +
      '<button type="button" class="option-row-input__remove btn btn--secondary">Kaldır</button>';
    rowsContainer.appendChild(row);
    refreshControls();
  }

  rowsContainer.addEventListener("click", (event) => {
    if (event.target.classList.contains("option-row-input__remove") && rows().length > MIN_OPTIONS) {
      event.target.closest(".option-row-input").remove();
      refreshControls();
    }
  });

  addButton.addEventListener("click", addRow);

  refreshControls();
});
