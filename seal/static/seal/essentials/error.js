const floatDiv = document.getElementById("float-div");
let width = window.innerWidth;

const eCodeList = eCode.split('');

for (let i = 0; i < width/10; i++) {
    const span = document.createElement("span");
    span.classList.add("particle");
    span.innerText = eCodeList[Math.floor(Math.random() * eCodeList.length)];;
    floatDiv.appendChild(span);
}

const particles = document.querySelectorAll('.particle');

for (let i = 0; i < particles.length; i++) {
    const particle = particles[i];
    particle.style.top = `${Math.random() * 100}%`;
    particle.style.left = `${Math.random() * 100}%`;
    particle.style.fontWeight = ['normal', 'bold', 'bolder', 'lighter'][Math.floor(Math.random() * 4)];
    particle.style.fontSize = `${Math.floor(Math.random() * 10) + 12}px`;
    particle.style.filter = `blur(${Math.floor(Math.random() * 120) / 100}px)`;
    particle.style.animation =`${Math.floor(Math.random() * 20) + 20}s ${['float', 'floatReverse', 'float2','floatReverse2'][Math.floor(Math.random() * 4)]} infinite`;
}