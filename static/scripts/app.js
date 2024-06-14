
let main_wheel_color = "#5B7C99"
let n_slices = 5
let n = 0

let socket = io();
socket.on('connect', receive_input);
socket.on('server_response', receive_input);

function receive_input(msg) {
    console.log("getting server message")
    console.log(msg)
    draw(msg)
}


function draw(msg) {
    let highlight = msg["radial_section"];
    console.log("drawing")
    console.log(highlight)
    console.log("==========")

    let canvas = document.getElementById("canvas");
    let ctx = canvas.getContext("2d");
    let beginAngle = 0;
    let endAngle = 0;
    for (let i = 0; i < n_slices; i++) {
        beginAngle = endAngle;
        endAngle = endAngle + 2 * Math.PI / n_slices;
        ctx.beginPath();
        if (i===highlight){
            if(msg["click"]){
                ctx.fillStyle = "#0000FF";
            } else {
                ctx.fillStyle = "#FF0000";
            }

        }
        else {
            ctx.fillStyle = main_wheel_color;
        }

        // Drawing the arc
        ctx.moveTo(500, 500);
        ctx.arc(500, 500, 500, beginAngle, endAngle);
        ctx.lineTo(500, 500);
        ctx.stroke();

        // Fill
        ctx.fill();
    }
}

window.onload = draw;