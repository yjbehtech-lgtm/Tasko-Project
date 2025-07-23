// static/countdown.js

function startCooldown(secondsLeft) {
    const cooldownDiv = document.getElementById('cooldown');
    const button = document.querySelector('button');
    const message = document.getElementById('message');

    button.disabled = true;
    cooldownDiv.style.display = 'block';

    const interval = setInterval(() => {
        secondsLeft--;
        cooldownDiv.innerText = `冷却中：${secondsLeft} 秒`;

        if (secondsLeft <= 0) {
            clearInterval(interval);
            cooldownDiv.style.display = 'none';
            message.innerText = '';
            button.disabled = false;
        }
    }, 1000);
}
