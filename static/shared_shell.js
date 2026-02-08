// 统一测量 footer 高度，确保滚动容器预留安全空间。
function measureFooter() {
    const footer = document.getElementById('copyrightBar');
    if (!footer) return;
    const height = Math.ceil(footer.getBoundingClientRect().height || 0);
    document.documentElement.style.setProperty('--footer-h', `${height}px`);
}

window.addEventListener('load', measureFooter);
window.addEventListener('resize', measureFooter);
