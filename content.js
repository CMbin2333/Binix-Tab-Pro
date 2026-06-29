document.addEventListener('click', function(e) {
const target = e.target.closest('a');
if (target && target.getAttribute('target') === '_blank') {
target.setAttribute('target', '_self'); // 强行改为“当前框架内打开”
}
}, true); // 使用捕获阶段，确保在网站自身 JS 反应前生效