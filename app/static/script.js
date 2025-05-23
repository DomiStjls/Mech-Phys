document.addEventListener("DOMContentLoaded", () => {
    const svg = document.getElementById("drawing-area");

    let selectedObjectId = null; // Для связывания объектов

    function getSelectedMode() {
        return document.querySelector('input[name="mode"]:checked').value;
    }

    function getObjectParams(mode) {
        if (mode === "plane") {
            return {
                angle: parseFloat(document.getElementById("plane-angle").value),
                length: parseFloat(document.getElementById("plane-length").value)
            };
        } else if (mode === "block") {
            return {
                width: parseFloat(document.getElementById("block-width").value),
                height: parseFloat(document.getElementById("block-height").value)
            };
        } else if (mode === "string") {
            return {
                attachment: document.getElementById("string-attachment").value
            };
        }
        return {};
    }

    const modeRadios = document.querySelectorAll('input[name="mode"]');
    console.log(modeRadios);
    modeRadios.forEach(radio => {
        radio.addEventListener("change", () => {
            const selected = getSelectedMode();
            console.log(selected);
            if (selected) {
                fetch("/set_mode", {
                    method: "POST",
                    headers: { "Content-Type": "application/x-www-form-urlencoded" },
                    body: `mode=${selected}`
                });
            }
        });
    });

    svg.addEventListener("click", async (e) => {
        const mode = getSelectedMode();
        const rect = svg.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        if (mode === "string") {
            const target = e.target.closest(".svg-object");
            if (target) {
                const id = target.getAttribute("data-id");
                if (!selectedObjectId) {
                    selectedObjectId = id;
                    target.setAttribute("stroke", "red");
                } else {
                    // добавить связь
                    await fetch("/add_relation", {
                        method: "POST",
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(new URLSearchParams({
                            source_id: selectedObjectId,
                            target_id: id,
                            relation_type: "string"
                        }))
                    });
                    location.reload(); // временно, позже можно делать renderRelation()
                }
            }
            return;
        }

        const params = getObjectParams(mode);

        let body = { type: mode, x: Math.round(x), y: Math.round(y) };
        for (const key in params) {
            body[key] = params[key];
        }
        console.log(body);
        const response = await fetch("/add_object", {
            method: "POST",
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const data = await response.json();
        location.reload();
        // if (data.status === "added") {
        //     renderObject(data.object);
        // }
    });

    // ctrl+z
    document.addEventListener('keydown', function (event) {

        if (event.ctrlKey && event.code == 'KeyZ') {
            event.preventDefault();
            console.log("ctrl+z")
            fetch('/undo', { method: 'POST' }).then(() => location.reload());
        }
    });
    // ctrl+z
    document.addEventListener('keydown', function (event) {

        if (event.ctrlKey && event.code == 'KeyC') {
            event.preventDefault();
            console.log("ctrl+c")
            fetch('/clear', { method: 'POST' }).then(() => location.reload());
        }
    });
    // Кнопка очистить рисунок
    document.getElementById('clear-btn').addEventListener('click', () => {
        fetch('/clear', { method: 'POST' }).then(response => {
            if (response.ok) {
                location.reload();
            } else {
                alert('Ошибка при очистке.');
            }
        });
    });
  
});
