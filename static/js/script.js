"use strict";

const figP = document.getElementsByClassName('fig-p')
const links = document.getElementsByClassName("link")
const navIcons = document.getElementsByClassName("nav-icon")
const greetingDiv = document.querySelector('.greeting')
const skillSpan = document.querySelector('.skills-span')
const worksSpan = document.querySelector('.works-span')
const contactSpan = document.querySelector('.body-input')
const btnMessage = document.querySelector(".btn-messages")
const messageBox = document.querySelector(".messages")
const cookieBanner = document.querySelector('.cookie')
const cookieX = document.querySelector('.cookie-x')

function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

function toggleIndex(link, icon, index) {
    for (let j = 0; j < link.length; j++) {
        link[j].classList.remove('active')
    }
    link[index].classList.toggle('active')

    for (let j = 0; j < icon.length; j++) {
        icon[j].classList.remove('colored')
    }
    icon[index].classList.toggle('colored')
}

let timeOut = 400
for (let i = 0; i < figP.length; i++) {
    setTimeout(() => {
        figP[i].classList.toggle("get-back")
    }, timeOut)
    timeOut += 400
}

for (let i = 0; i < links.length; i++) {
    links[i].addEventListener('click', e => {
        for (let j = 0; j < links.length; j++) {
            links[j].classList.remove('active')
        }
        links[i].classList.toggle("active")
    })
}

for (let i = 0; i < navIcons.length; i++) {
    navIcons[i].addEventListener('click', e => {
        for (let j = 0; j < navIcons.length; j++) {
            navIcons[j].classList.remove('colored')
        }
        navIcons[i].classList.toggle("colored")
    })
}

window.addEventListener('scroll', e => {
    if (isInViewport(greetingDiv)) {
        toggleIndex(links, navIcons, 0)
    }

    if (isInViewport(skillSpan)) {
        toggleIndex(links, navIcons, 1)
    }

    if (isInViewport(worksSpan)) {
        toggleIndex(links, navIcons, 2)
    }

    if (isInViewport(contactSpan)) {
        toggleIndex(links, navIcons, 3)
    }
})

const swiper = new Swiper('.swiper', {
    loop: true,
    slidesPerView: 1,
    spaceBetween: 10,
    autoplay: {
        delay: 2000,
        disableOnInteraction: false,
    },
    navigation: {
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev',
    },
    breakpoints: {
        576: {
            slidesPerView: 2,
            spaceBetween: 20
        },
        992: {
            slidesPerView: 3,
            spaceBetween: 20
        },
        1440: {
            slidesPerView: 4,
            spaceBetween: 20
        }
    }
});


//Django flash message
if (btnMessage) {
    btnMessage.onclick = e => {
        e.preventDefault()
        messageBox.style.transition = "all .2s linear"
        messageBox.style.right = "-370px"
    }
}

if (messageBox) {
    setTimeout(() => {
        messageBox.style.transition = "all .2s linear"
        messageBox.style.right = "-370px"
    }, 4000)
}

// Cookie Policy
let cookiePolicy = localStorage.getItem("cookiePolicy")
if (cookiePolicy === null) {
    localStorage.setItem('cookiePolicy', 'false')
    cookiePolicy = "false"
}

if (cookiePolicy === 'false') {
    cookieBanner.style.display = "flex"
}

cookieX.addEventListener('click', e => {
    e.preventDefault()
    cookieBanner.style.display = "none"
    localStorage.setItem('cookiePolicy', 'true')
})

