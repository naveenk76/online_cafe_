socket.on("message", function(data) {
    let box = document.getElementById("chat-box");

    let p = document.createElement("p");
    p.innerHTML = "<b>" + data.user + ":</b> " + data.msg;

    box.appendChild(p);
    box.scrollTop = box.scrollHeight;
});