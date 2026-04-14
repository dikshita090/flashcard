document.querySelectorAll("[data-flip-card]").forEach((card) => {
    const trigger = card.querySelector("[data-flip-trigger]");
    if (!trigger) {
        return;
    }

    trigger.addEventListener("click", () => {
        card.classList.add("is-flipped");
    });
});
