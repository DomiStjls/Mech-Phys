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

    modeRadios.forEach(radio => {
        radio.addEventListener("change", () => {
            const selected = getSelectedMode();

            if (selected) {
                fetch("/set_mode", {
                    method: "POST",
                    headers: { "Content-Type": "application/x-www-form-urlencoded" },
                    body: `mode=${selected}`
                });
            }
        });
    });
    let anchors = [];

    svg.addEventListener("click", async (e) => {
        const mode = getSelectedMode();
        if (mode !== "info") {
            if (e.target.classList.contains("anchor-point")) {
                let selectedAnchorId = null;
                selectedAnchorId = e.target.dataset.id;
                console.log("Выбрана точка крепления:", selectedAnchorId);

                const params = getObjectParams(mode);
                // Визуально подсветим
                // document.querySelectorAll(".anchor-point").forEach(p => p.setAttribute("fill", "grey"));

                if (mode === "string") {
                    console.log(anchors, "Все выбранные точки для нити");
                    attachment = params["attachment"];
                    if (attachment === "two-way" && anchors.length === 1) {
                        anchors.push({
                            x: Math.round(e.clientX),
                            y: Math.round(e.clientY),
                            type_add: mode,
                            anchor_id: selectedAnchorId,
                        });
                        body = { anchor_1: anchors[0].anchor_id, anchor_2: anchors[1].anchor_id, type_add: mode, attachment: attachment };
                        const response = await fetch("/add_string", {
                            method: "POST",
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(body)
                        });
                        anchors = [];
                        const data = await response.json();
                        location.reload();

                    } else {
                        anchors.push({
                            x: Math.round(e.clientX),
                            y: Math.round(e.clientY),
                            type_add: mode,
                            anchor_id: selectedAnchorId,
                        });


                    }
                } else {
                    let body = { x: Math.round(e.clientX), y: Math.round(e.clientY), type_add: mode, anchor_id: selectedAnchorId };

                    for (const key in params) {
                        body[key] = params[key];
                    }
                    const response = await fetch("/add_relation", {
                        method: "POST",
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(body)
                    });
                    const data = await response.json();
                    location.reload();
                }


            } else {

                const rect = svg.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                const mode = getSelectedMode();
                let params_string = getObjectParams("string");
                if (mode === "string") {
                    if (anchors.length === 1 && params_string["attachment"] === "one-way") {

                        // добавить связь
                        await fetch("/add_string", {
                            method: "POST",
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                attachment: "one-way",
                                anchor_1: anchors[0].anchor_id,
                                x: Math.round(e.clientX),
                                y: Math.round(e.clientY),
                                mode: mode
                            })
                        });
                        anchors = [];
                        location.reload(); // временно, позже можно делать renderRelation()



                    }
                    return;
                }

                const params = getObjectParams(mode);

                let body = { type: mode, x: Math.round(x), y: Math.round(y) };
                for (const key in params) {
                    body[key] = params[key];
                }
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
            }

        }
    });





    // Функция для отправки параметров на сервер с дебонсингом
    let updateTimeout = null;
    async function updateParams() {
        if (updateTimeout) {
            clearTimeout(updateTimeout);
        }
        updateTimeout = setTimeout(async () => {
            const params = {
                plane_angle: document.getElementById("plane-angle").value,
                plane_length: document.getElementById("plane-length").value,
                block_width: document.getElementById("block-width").value,
                block_height: document.getElementById("block-height").value,
                string_attachment: document.getElementById("string-attachment").value
            };

            try {
                await fetch("/set_params", {
                    method: "POST",
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(params)
                });
            } catch (error) {
                console.error("Ошибка при сохранении параметров:", error);
            }
        }, 400);
    }

    const paramInputs = [
        document.getElementById("plane-angle"),
        document.getElementById("plane-length"),
        document.getElementById("block-width"),
        document.getElementById("block-height"),
        document.getElementById("string-attachment")
    ];

    paramInputs.forEach(input => {
        if (input) {
            input.addEventListener("change", updateParams);
            input.addEventListener("input", updateParams); // для сохранения при вводе с дебонсингом
        }
    });

    function showPopupForObject(objectId, position) {
        const popup = document.getElementById('popup');
        const popupBody = document.getElementById('popup-body');

        // Позиционирование попапа
        popup.style.top = `${position.top}px`;
        popup.style.left = `${position.left}px`;

        fetch(`/forces/popup/${objectId}`)
            .then(response => response.text())
            .then(html => {
                popupBody.innerHTML = html;
                popup.classList.remove('hidden');
            });
    }


    document.querySelectorAll('.clickable-object').forEach(obj => {
        obj.addEventListener('click', function (e) {
            const objectId = this.dataset.id;
            const rect = this.getBoundingClientRect();
            const x = (e.clientX < 1000 ? e.clientX + 200 : e.clientX);

            const y = (e.clientY > 500 ? e.clientY - 500 : 20);


            showPopupForObject(objectId, {
                top: y,
                left: x
            });
        });
    });

    // Закрытие попапа
    document.getElementById('closePopupBtn').addEventListener('click', () => {
        document.getElementById('popup').classList.add('hidden');
    });

    // ctrl+z
    document.addEventListener('keydown', function (event) {

        if (event.ctrlKey && event.code == 'KeyZ') {
            event.preventDefault();
            fetch('/undo', { method: 'POST' }).then(() => location.reload());
        }
    });
    // ctrl+c
    document.addEventListener('keydown', function (event) {

        if (event.ctrlKey && event.code == 'KeyC') {
            event.preventDefault();
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
