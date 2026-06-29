(function() {
const interactiveCanvas = document.getElementById('interactive-canvas');
if (!interactiveCanvas) return;
const ctx = interactiveCanvas.getContext('2d', { alpha: false });
const ambientLayer = document.getElementById('ambient-layer');
const bgLayer = document.getElementById('bg-layer');
const bgVideo = document.getElementById('bg-video');
const bgWallpaper = document.getElementById('bg-wallpaper');
let currentTheme = localStorage.getItem('interactiveTheme') || 'earth';
let isOptimizedMode = localStorage.getItem('interactiveOpt') === 'true';
const optSwitch = document.getElementById('interactive-opt-switch');
if (optSwitch) {
optSwitch.checked = isOptimizedMode;
optSwitch.addEventListener('change', (e) => {
isOptimizedMode = e.target.checked;
localStorage.setItem('interactiveOpt', isOptimizedMode);
initScene();
});
}
window.updateInteractiveVisibility = function(currentMode) {
const interactiveSettings = document.getElementById('interactive-settings');
if (currentMode === 'interactive') {
interactiveCanvas.style.display = 'block';
if(interactiveSettings) interactiveSettings.style.display = 'block';
if(ambientLayer) { ambientLayer.style.display = 'none'; ambientLayer.style.opacity = '0'; }
if(bgLayer) bgLayer.style.opacity = '0';
if(bgVideo) bgVideo.style.opacity = '0';
if(bgWallpaper) bgWallpaper.style.opacity = '0';
initScene();
} else if (currentMode === 'mesh') {
interactiveCanvas.style.display = 'none';
if(interactiveSettings) interactiveSettings.style.display = 'none';
if(ambientLayer) { ambientLayer.style.display = 'block'; ambientLayer.style.opacity = ''; }
} else {
interactiveCanvas.style.display = 'none';
if(interactiveSettings) interactiveSettings.style.display = 'none';
if(ambientLayer) { ambientLayer.style.display = 'none'; ambientLayer.style.opacity = ''; }
}
};
function updateInteractiveThemeColors(theme) {
const root = document.documentElement;
const themeColors = {
'earth': { b1: '#1e40af', b2: '#3b82f6', b3: '#60a5fa', b4: '#93c5fd', b5: '#dbeafe' }, // 蓝色系
'solar': { b1: '#dc2626', b2: '#ea580c', b3: '#f59e0b', b4: '#fbbf24', b5: '#fcd34d' }, // 红色到金色
'saturn': { b1: '#92400e', b2: '#d97706', b3: '#f59e0b', b4: '#fbbf24', b5: '#fed7aa' }, // 金棕色系
'quantum': { b1: '#7c3aed', b2: '#a855f7', b3: '#c084fc', b4: '#ddd6fe', b5: '#e9d5ff' }, // 紫色系
'cyber': { b1: '#00f2fe', b2: '#f012be', b3: '#7c3aed', b4: '#06b6d4', b5: '#ec4899' }, // 青粉紫色
'manifold': { b1: '#06b6d4', b2: '#3b82f6', b3: '#8b5cf6', b4: '#ec4899', b5: '#f97316' }  // 多彩渐变
};
const colors = themeColors[theme] || themeColors['earth'];
root.style.setProperty('transition', 'none');
root.style.setProperty('--bg-base', '#0f172a');
root.style.setProperty('--blob-1', colors.b1);
root.style.setProperty('--blob-2', colors.b2);
root.style.setProperty('--blob-3', colors.b3);
root.style.setProperty('--blob-4', colors.b4);
root.style.setProperty('--blob-5', colors.b5);
root.style.setProperty('--text-a', '#ffffff');
root.style.setProperty('--text-b', colors.b1);
root.offsetHeight;
setTimeout(() => {
root.style.setProperty('transition', '--bg-base 3s ease, --blob-1 3s ease, --blob-2 3s ease, --text-a 3s ease, --text-b 3s ease');
}, 50);
if (typeof updateClockStyle === 'function') updateClockStyle();
}
document.querySelectorAll('#interactive-theme-selector .mode-opt').forEach(opt => {
if (opt.dataset.theme === currentTheme) {
opt.classList.add('active');
} else {
opt.classList.remove('active');
}
});
document.querySelectorAll('#interactive-theme-selector .mode-opt').forEach(opt => {
opt.addEventListener('click', (e) => {
document.querySelectorAll('#interactive-theme-selector .mode-opt').forEach(el => el.classList.remove('active'));
e.target.classList.add('active');
currentTheme = e.target.dataset.theme;
localStorage.setItem('interactiveTheme', currentTheme);
initScene();
updateInteractiveThemeColors(currentTheme);
});
});
let width, height, cx, cy;
let canvasScale = 0.7; // 画布实际分辨率缩放比例
let time = 0;
let animationFrameId = null;
let lastFrameTime = 0;
let fpsLimit = parseInt(localStorage.getItem('canvas_fps_limit') || '0');
let fpsInterval = fpsLimit > 0 ? 1000 / fpsLimit : 0;
let isDragging = false;
let lastMouseX = 0, lastMouseY = 0;
let mouse = { x: -1000, y: -1000, isDown: false };
let RADIUS = 0, currentFocal = 1400;
let particles = [], stars = [];
let baseYaw = 0, currentPitch = 0.25, currentYaw = 0.0, targetPitch = 0.25, targetYaw = 0.0;
let currentExplosionScale = 1.0, currentHue = 190;
let earthYaw = 0;
let moon_cx = 0, moon_cy = 0, moon_cz = 0;
let earthImgData = null;
let moonImgData = null;
let isTexLoading = false;
let currentSpacing = 14;
const DAMPING = 0.965;
let cols, rows;
let waveCurrent = [], wavePrevious = [];
let cyberNodes = [];
let currentConnectDistance = 150;
function isUIArea(e) {
const t = e.target;
return t.closest('.sidebar') || t.closest('.side-drawer') || t.closest('.modal-content') ||
t.closest('.floating-panel') || t.closest('.tile-grid') || t.closest('.search-container') ||
t.closest('.utility-dock') || t.closest('.quote-card') || t.closest('.header');
}
function dropWave(x, y, radius, power) {
if (currentTheme !== 'manifold') return;
let cxGrid = Math.floor(x / currentSpacing);
let cyGrid = Math.floor(y / currentSpacing);
for (let i = -radius; i <= radius; i++) {
for (let j = -radius; j <= radius; j++) {
let nx = cxGrid + i, ny = cyGrid + j;
if (nx > 0 && nx < cols - 1 && ny > 0 && ny < rows - 1) {
let dist = Math.sqrt(i*i + j*j);
if(dist <= radius) wavePrevious[nx + ny * cols] += power * (1 - dist / (radius + 1));
}
}
}
}
window.addEventListener('mousedown', (e) => {
if(!isUIArea(e)) {
isDragging = true; mouse.isDown = true;
lastMouseX = e.clientX * canvasScale; lastMouseY = e.clientY * canvasScale;
if (currentTheme === 'manifold') dropWave(mouse.x, mouse.y, 4, -400);
}
});
window.addEventListener('mousemove', (e) => {
lastMouseX = mouse.x; lastMouseY = mouse.y;
mouse.x = e.clientX * canvasScale; mouse.y = e.clientY * canvasScale;
if (isDragging) {
targetYaw += (mouse.x - lastMouseX) * (0.005 / canvasScale);
targetPitch += (mouse.y - lastMouseY) * (0.005 / canvasScale);
targetPitch = Math.max(-Math.PI/2.2, Math.min(Math.PI/2.2, targetPitch));
}
if (currentTheme === 'manifold') {
let speed = Math.sqrt((mouse.x - lastMouseX)**2 + (mouse.y - lastMouseY)**2);
dropWave(mouse.x, mouse.y, 2, Math.min(speed * 1.5 + 20, 150));
}
});
window.addEventListener('mouseup', () => { isDragging = false; mouse.isDown = false; });
window.addEventListener('mouseleave', () => { isDragging = false; mouse.isDown = false; mouse.x = -1000; });
window.addEventListener('touchstart', (e) => {
if(!isUIArea(e)) {
isDragging = true; mouse.isDown = true;
mouse.x = e.touches[0].clientX * canvasScale; mouse.y = e.touches[0].clientY * canvasScale;
lastMouseX = mouse.x; lastMouseY = mouse.y;
if (currentTheme === 'manifold') dropWave(mouse.x, mouse.y, 3, 200);
}
}, { passive: true });
window.addEventListener('touchmove', (e) => {
if (isDragging) {
targetYaw += (e.touches[0].clientX * canvasScale - lastMouseX) * (0.005 / canvasScale);
targetPitch += (e.touches[0].clientY * canvasScale - lastMouseY) * (0.005 / canvasScale);
targetPitch = Math.max(-Math.PI/2.2, Math.min(Math.PI/2.2, targetPitch));
lastMouseX = mouse.x; lastMouseY = mouse.y;
mouse.x = e.touches[0].clientX * canvasScale; mouse.y = e.touches[0].clientY * canvasScale;
if (currentTheme === 'manifold') dropWave(mouse.x, mouse.y, 2, 80);
}
}, { passive: true });
window.addEventListener('touchend', () => { isDragging = false; mouse.isDown = false; });
function rotate3D(x, y, z, pitch, yaw) {
let cosX = Math.cos(pitch), sinX = Math.sin(pitch);
let y1 = y * cosX - z * sinX, z1 = z * cosX + y * sinX;
let cosY = Math.cos(yaw), sinY = Math.sin(yaw);
let x2 = x * cosY - z1 * sinY, z2 = z1 * cosY + x * sinY;
return { x: x2, y: y1, z: z2 };
}
function initStars() {
stars = [];
const numStars = isOptimizedMode ? 50 : (window.innerWidth <= 768 ? 100 : 250);
for(let i=0; i<numStars; i++) {
stars.push({
x: Math.random() * window.innerWidth, y: Math.random() * window.innerHeight,
size: Math.random() * 1.5 + 0.2, speed: Math.random() * 0.05 + 0.01,
alpha: currentTheme === 'earth' ? Math.random() * 0.5 + 0.3 : Math.random() * 0.5 + 0.2,
isRed: currentTheme === 'solar' && Math.random() > 0.7,
isGold: currentTheme === 'saturn' && Math.random() > 0.8
});
}
}
function get3DNoise(x, y, z) {
let n1 = Math.sin(x*3) + Math.cos(y*3) + Math.sin(z*3);
let n2 = Math.sin(x*7 + y*4) + Math.cos(y*5 - z*3);
return (n1 + n2 * 0.5);
}
function loadTexture(url) {
return new Promise((resolve) => {
let img = new Image();
img.crossOrigin = 'Anonymous';
img.src = url;
img.onload = () => {
let canvas = document.createElement('canvas');
canvas.width = 512; canvas.height = 256;
let ctx = canvas.getContext('2d');
ctx.drawImage(img, 0, 0, 512, 256);
resolve(ctx.getImageData(0, 0, 512, 256));
};
img.onerror = () => resolve(null);
});
}
class CyberNode {
constructor() {
this.x = Math.random() * width; this.y = Math.random() * height;
this.vx = (Math.random() - 0.5) * 1.5; this.vy = (Math.random() - 0.5) * 1.5;
this.radius = Math.random() * 2 + 1.5;
this.isCyan = Math.random() > 0.5;
}
update() {
this.x += this.vx; this.y += this.vy;
if (this.x <= 0 || this.x >= width) this.vx *= -1;
if (this.y <= 0 || this.y >= height) this.vy *= -1;
if (mouse.x !== -1000) {
let dx = this.x - mouse.x, dy = this.y - mouse.y, dist = Math.sqrt(dx * dx + dy * dy);
let currentRepelRadius = mouse.isDown ? 300 : 100;
if (dist < currentRepelRadius) {
let force = (currentRepelRadius - dist) / currentRepelRadius;
let pushMultiplier = mouse.isDown ? 5 : 0.5;
this.x += (dx / dist) * force * pushMultiplier; this.y += (dy / dist) * force * pushMultiplier;
}
}
}
draw(ctx) {
ctx.beginPath(); ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
let color = this.isCyan ? '#00f2fe' : '#f012be';
ctx.fillStyle = color;
if (!isOptimizedMode) { ctx.shadowBlur = 10; ctx.shadowColor = color; }
ctx.fill(); ctx.shadowBlur = 0;
}
}
class Particle {
constructor(bx, by, bz, type) {
this.bx = bx; this.by = by; this.bz = bz;
this.type = type;
this.px = 0; this.py = 0; this.scale = 1;
this.baseAlpha = 0; this.zDepth = 0;
this.offset = 0; this.connections = [];
this.screenX = width / 2; this.screenY = height / 2;
this.nxRot = 0; this.nyRot = 0; this.nzRot = 0;
this.r = 255; this.g = 255; this.b = 255;
this.cityIntensity = 0;
this.pulsePhase = Math.random() * Math.PI * 2; this.pulseSpeed = Math.random() * 0.08 + 0.02;
this.boilFreq = Math.random() * 5 + 3;
if (currentTheme === 'saturn') {
this.orbitAngle = Math.atan2(bz, bx); this.orbitDist = Math.sqrt(bx*bx + bz*bz);
if (type.includes('ring')) this.orbitSpeed = (Math.random() * 0.004 + 0.001) * (RADIUS / this.orbitDist);
else this.orbitSpeed = 0.0008;
}
}
update(pitch, yaw, renderCx) {
if (currentTheme === 'earth') {
let worldX = this.bx, worldY = this.by, worldZ = this.bz;
let objX = this.bx, objY = this.by, objZ = this.bz;
if (this.type === 'earth_tex') {
let cosE = Math.cos(earthYaw), sinE = Math.sin(earthYaw);
worldX = objX * cosE - objZ * sinE;
worldZ = objZ * cosE + objX * sinE;
objX = worldX; objZ = worldZ;
} else if (this.type === 'moon_tex') {
worldX += moon_cx;
worldY += moon_cy;
worldZ += moon_cz;
}
let rotated = rotate3D(worldX, worldY, worldZ, pitch, yaw);
this.zDepth = rotated.z;
let nRot = rotate3D(objX, objY, objZ, pitch, yaw);
this.nxRot = nRot.x; this.nyRot = nRot.y; this.nzRot = nRot.z;
this.scale = currentFocal / (this.zDepth + currentFocal);
this.px = renderCx + rotated.x * this.scale;
this.py = cy + rotated.y * this.scale;
return;
}
if (currentTheme === 'quantum') {
let qTime = time * 0.012;
let breathe = isOptimizedMode ? 0 : Math.sin(this.bx * 0.01 + qTime) * Math.cos(this.by * 0.01 + qTime) * 10;
let nx = this.bx / RADIUS, ny = this.by / RADIUS, nz = this.bz / RADIUS;
let tx = this.bx * currentExplosionScale + nx * breathe, ty = this.by * currentExplosionScale + ny * breathe, tz = this.bz * currentExplosionScale + nz * breathe;
let rotated = rotate3D(tx, ty, tz, pitch, yaw);
this.rotatedZ = rotated.z;
let scale = currentFocal / (this.rotatedZ + currentFocal);
this.projX = renderCx + rotated.x * scale; this.projY = cy + rotated.y * scale;
let repelX = 0, repelY = 0;
if (mouse.x !== -1000 && !mouse.isDown && !isOptimizedMode) {
let dx = this.projX - mouse.x, dy = this.projY - mouse.y, dist = Math.sqrt(dx*dx + dy*dy);
if (dist < 180) {
let force = Math.pow((180 - dist) / 180, 2);
repelX = (dx / dist) * force * 60; repelY = (dy / dist) * force * 60;
}
}
let spring = 0.1 + Math.max(0.1, (this.rotatedZ + RADIUS) / (RADIUS * 2)) * 0.15;
this.screenX += ((this.projX + repelX) - this.screenX) * spring;
this.screenY += ((this.projY + repelY) - this.screenY) * spring;
return;
}
if (currentTheme === 'saturn') {
this.orbitAngle += this.orbitSpeed;
this.bx = Math.cos(this.orbitAngle) * this.orbitDist;
this.bz = Math.sin(this.orbitAngle) * this.orbitDist;
}
let nx = this.bx / RADIUS, ny = this.by / RADIUS, nz = this.bz / RADIUS;
let currentRadius = RADIUS;
if (currentTheme === 'solar' && !isOptimizedMode) {
currentRadius += Math.sin(nx * this.boilFreq + time * 0.05) * Math.cos(ny * this.boilFreq + time * 0.05) * (RADIUS * 0.04);
}
let tx = nx * currentRadius - nx * this.offset;
let isRing = this.type && this.type.includes('ring');
let ty = ny * currentRadius - (isRing ? 0 : ny) * this.offset;
let tz = nz * currentRadius - nz * this.offset;
let rotated = rotate3D(tx, ty, tz, pitch, yaw);
this.zDepth = rotated.z;
this.scale = currentFocal / (rotated.z + currentFocal);
this.px = renderCx + rotated.x * this.scale;
this.py = cy + rotated.y * this.scale;
this.baseAlpha = Math.max(0.01, Math.min(1.0, (rotated.z + RADIUS * 2) / (RADIUS * 4)));
if (!isOptimizedMode) {
let dx = this.px - mouse.x, dy = this.py - mouse.y;
let dist = Math.sqrt(dx*dx + dy*dy);
if (dist < 150 && rotated.z > -RADIUS) {
let force = Math.pow((150 - dist) / 150, 2);
this.offset += (force * (currentTheme === 'saturn' ? 25 : 40) - this.offset) * 0.15;
} else this.offset += (0 - this.offset) * 0.08;
} else this.offset = 0;
}
}
function initScene() {
width = interactiveCanvas.width = Math.floor(window.innerWidth * 0.7);
height = interactiveCanvas.height = Math.floor(window.innerHeight * 0.7);
cx = width / 2; cy = height / 2;
const isMobile = window.innerWidth <= 768;
if (currentTheme === 'manifold') {
currentSpacing = isOptimizedMode ? 24 : 14;
cols = Math.ceil(width / currentSpacing); rows = Math.ceil(height / currentSpacing);
waveCurrent = new Float32Array(cols * rows); wavePrevious = new Float32Array(cols * rows);
} else if (currentTheme === 'cyber') {
cyberNodes = [];
currentConnectDistance = isOptimizedMode ? 100 : 150;
const maxNodes = isOptimizedMode ? (isMobile ? 60 : 100) : (isMobile ? 100 : 250);
for(let i = 0; i < maxNodes; i++) cyberNodes.push(new CyberNode());
}
else {
currentFocal = currentTheme === 'quantum' ? 800 : 1400;
if (currentTheme === 'earth') RADIUS = isMobile ? width * 0.42 : Math.min(height, width) * 0.38;
else if (currentTheme === 'solar') RADIUS = isMobile ? width * 0.42 : Math.min(height, width) * 0.35;
else if (currentTheme === 'saturn') RADIUS = isMobile ? width * 0.22 : Math.min(height, width) * 0.22;
else if (currentTheme === 'quantum') RADIUS = isMobile ? 160 : 260;
initStars();
particles = [];
let pCountBase = 0;
const isPowerSave = document.body.classList.contains('power-save-mode');
if (currentTheme === 'earth') pCountBase = isPowerSave ? 3000 : (isOptimizedMode ? 6000 : 16000);
else if (currentTheme === 'solar') pCountBase = isPowerSave ? 1500 : (isOptimizedMode ? 2000 : 7000);
else if (currentTheme === 'quantum') pCountBase = isPowerSave ? 120 : (isOptimizedMode ? 180 : 500);
if (isMobile) pCountBase = Math.floor(pCountBase * 0.45);
if (currentTheme === 'earth') {
targetPitch = 0.0;
let localOffsetHours = -(new Date().getTimezoneOffset()) / 60;
targetYaw = (localOffsetHours / 24) * Math.PI * 2 + Math.PI;
currentYaw = targetYaw;
if (!earthImgData && !isTexLoading) {
isTexLoading = true;
Promise.all([
loadTexture('https://cdn.jsdelivr.net/gh/mrdoob/three.js@master/examples/textures/planets/earth_atmos_2048.jpg'),
loadTexture('https://cdn.jsdelivr.net/gh/mrdoob/three.js@master/examples/textures/planets/moon_1024.jpg')
]).then(results => {
earthImgData = results[0]; moonImgData = results[1];
generateParticles(pCountBase);
});
} else generateParticles(pCountBase);
} else if (currentTheme === 'solar') {
targetPitch = 0.2; targetYaw = 0.0; generateParticles(pCountBase);
} else if (currentTheme === 'saturn') {
targetPitch = 0.45; targetYaw = 0.15; generateParticles(0);
} else if (currentTheme === 'quantum') {
targetPitch = 0.0; targetYaw = 0.0; generateParticles(pCountBase);
}
}
if (animationFrameId === null) animate();
}
function generateParticles(numParticles) {
particles = [];
const goldenRatio = (1 + Math.sqrt(5)) / 2;
const angleInc = Math.PI * 2 * goldenRatio;
if (currentTheme === 'earth') {
let mCount = Math.floor(numParticles * 0.2);
let mRadius = RADIUS * 0.25;
for (let i = 0; i < numParticles; i++) {
let t = i / numParticles; let inclination = Math.acos(1 - 2 * t); let azimuth = angleInc * i;
let x = Math.sin(inclination) * Math.cos(azimuth) * RADIUS;
let y = Math.cos(inclination) * RADIUS;
let z = Math.sin(inclination) * Math.sin(azimuth) * RADIUS;
let p = new Particle(x, y, z, 'earth_tex');
if (earthImgData) {
let u = ((azimuth / (Math.PI * 2)) + 0.5) % 1.0, v = inclination / Math.PI;
let px = Math.floor(u * 512), py = Math.floor(v * 256);
px = Math.max(0, Math.min(px, 511)); py = Math.max(0, Math.min(py, 255));
let idx = (py * 512 + px) * 4;
p.r = earthImgData.data[idx]; p.g = earthImgData.data[idx+1]; p.b = earthImgData.data[idx+2];
p.cityIntensity = 0;
if (p.r > p.b * 0.7 && p.r > 30) {
let noise = get3DNoise(p.bx/RADIUS*6, p.by/RADIUS*6, p.bz/RADIUS*6);
if (noise > 0.2) p.cityIntensity = Math.pow((noise - 0.2) / 0.8, 1.5);
}
} else { p.r = 30; p.g = 100; p.b = 200; }
particles.push(p);
}
for (let i = 0; i < mCount; i++) {
let t = i / mCount; let inclination = Math.acos(1 - 2 * t); let azimuth = angleInc * i;
let x = Math.sin(inclination) * Math.cos(azimuth) * mRadius;
let y = Math.cos(inclination) * mRadius;
let z = Math.sin(inclination) * Math.sin(azimuth) * mRadius;
let p = new Particle(x, y, z, 'moon_tex');
if (moonImgData) {
let u = ((azimuth / (Math.PI * 2)) + 0.5) % 1.0, v = inclination / Math.PI;
let px = Math.floor(u * 512), py = Math.floor(v * 256);
px = Math.max(0, Math.min(px, 511)); py = Math.max(0, Math.min(py, 255));
let idx = (py * 512 + px) * 4;
p.r = moonImgData.data[idx]; p.g = moonImgData.data[idx+1]; p.b = moonImgData.data[idx+2];
} else { p.r = 150; p.g = 150; p.b = 150; }
p.baseAlpha = 1.0;
particles.push(p);
}
return;
}
if (currentTheme === 'saturn') {
let numBody = isOptimizedMode ? 800 : 2500;
let numRings = isOptimizedMode ? 1500 : 4500;
if (window.innerWidth <= 768) { numBody = Math.floor(numBody * 0.5); numRings = Math.floor(numRings * 0.5); }
for (let i = 0; i < numBody; i++) {
let t = i / numBody; let inclination = Math.acos(1 - 2 * t); let azimuth = angleInc * i;
let x = Math.sin(inclination) * Math.cos(azimuth) * RADIUS; let y = Math.cos(inclination) * RADIUS; let z = Math.sin(inclination) * Math.sin(azimuth) * RADIUS;
let lat = Math.asin(y/RADIUS); let noise = get3DNoise(x/RADIUS, y/RADIUS, z/RADIUS);
let band = Math.sin(lat * 25 + noise * 1.5);
particles.push(new Particle(x, y, z, band > 0 ? 'body_light' : 'body_dark'));
}
for (let i = 0; i < numRings; i++) {
let rRatio = 1.15 + Math.random() * 1.35;
if ((rRatio > 1.65 && rRatio < 1.75) || (rRatio > 1.95 && rRatio < 2.0) || (rRatio < 1.25 && Math.random() > 0.2)) continue;
let r = rRatio * RADIUS, theta = Math.random() * Math.PI * 2;
let x = Math.cos(theta) * r, z = Math.sin(theta) * r, y = (Math.random() - 0.5) * RADIUS * 0.02;
particles.push(new Particle(x, y, z, Math.random() > 0.4 ? 'ring_ice' : 'ring_dust'));
}
return;
}
for (let i = 0; i < numParticles; i++) {
let t = i / numParticles; let inclination = Math.acos(1 - 2 * t); let azimuth = angleInc * i;
let x = Math.sin(inclination) * Math.cos(azimuth) * RADIUS, y = Math.cos(inclination) * RADIUS, z = Math.sin(inclination) * Math.sin(azimuth) * RADIUS;
let type = currentTheme === 'quantum' ? 'quantum_node' : 'active';
if (currentTheme === 'solar') {
type = get3DNoise(x/RADIUS, y/RADIUS, z/RADIUS) > 0.2 ? 'active' : 'base';
if ((type === 'base' && Math.random() > 0.3) || (type === 'active' && Math.random() > 0.6)) continue;
}
particles.push(new Particle(x, y, z, type));
}
let targetNodes = particles;
let maxDistSq = Math.pow(RADIUS * 0.15, 2);
for (let i = 0; i < targetNodes.length; i++) {
let p1 = targetNodes[i], distances = [];
for (let j = 0; j < targetNodes.length; j++) {
if (i === j) continue;
let p2 = targetNodes[j];
let dx = p1.bx - p2.bx, dy = p1.by - p2.by, dz = p1.bz - p2.bz, dSq = dx*dx + dy*dy + dz*dz;
if (currentTheme === 'quantum' || dSq < maxDistSq) distances.push({ node: p2, dist: dSq });
}
distances.sort((a, b) => a.dist - b.dist);
let connLimit = currentTheme === 'quantum' ? (isOptimizedMode ? 2 : 3) : 2;
p1.connections = distances.slice(0, connLimit).map(n => n.node);
}
}
window.addEventListener('resize', () => { if (interactiveCanvas.style.display !== 'none') initScene(); });
function drawSaturnParticles(startIndex, endIndex, isBack, renderCx) {
for(let i = startIndex; i < endIndex; i++) {
let p = particles[i];
let size = Math.max(1.0, p.scale * 2.2);
let shadowFactor = 1.0;
if (!isOptimizedMode && isBack && p.type.includes('ring')) {
let dx = p.px - renderCx, dy = p.py - cy, distToCenter = Math.sqrt(dx*dx + dy*dy);
if (dx > 0 && dy > -RADIUS*0.5 && distToCenter < RADIUS * 2.0) {
shadowFactor = 0.15 + 0.85 * Math.min(1, Math.max(0, (distToCenter - RADIUS*0.7) / (RADIUS*0.8)));
}
}
let finalAlpha = p.baseAlpha * (isBack ? 0.45 : 1.0) * shadowFactor;
if (p.type === 'ring_ice') { ctx.fillStyle = `rgba(226, 232, 240, ${finalAlpha * 0.9})`; ctx.fillRect(p.px - size/2, p.py - size/2, size, size); }
else if (p.type === 'ring_dust') { ctx.fillStyle = `rgba(217, 119, 6, ${finalAlpha * 0.7})`; ctx.fillRect(p.px - size/2, p.py - size/2, size, size); }
else if (p.type === 'body_light') { ctx.fillStyle = `rgba(254, 243, 199, ${finalAlpha * 0.85})`; ctx.fillRect(p.px - size, p.py - size/2, size*2, size); }
else if (p.type === 'body_dark') { ctx.fillStyle = `rgba(180, 83, 9, ${finalAlpha * 0.85})`; ctx.fillRect(p.px - size, p.py - size/2, size*2, size); }
}
}
function animate() {
if (fpsInterval > 0) {
const now = performance.now();
const elapsed = now - lastFrameTime;
if (elapsed < fpsInterval) {
animationFrameId = requestAnimationFrame(animate);
return;
}
lastFrameTime = now - (elapsed % fpsInterval);
}
if (document.hidden) {
animationFrameId = requestAnimationFrame(animate);
return;
}
if (interactiveCanvas.style.display === 'none') {
animationFrameId = requestAnimationFrame(animate);
return;
}
time++;
let lx_screen = 0, ly_screen = 0, lz_screen = 0; // 屏幕空间的光线向量
if (currentTheme === 'earth') {
let now = new Date();
let hoursUTC = now.getUTCHours() + now.getUTCMinutes() / 60 + now.getUTCSeconds() / 3600;
earthYaw = -(hoursUTC / 24) * Math.PI * 2;
let sunWorldX = 1, sunWorldY = 0, sunWorldZ = 0;
let sunRot = rotate3D(sunWorldX, sunWorldY, sunWorldZ, currentPitch, currentYaw + baseYaw);
lx_screen = sunRot.x; ly_screen = sunRot.y; lz_screen = sunRot.z;
let msSinceNewMoon = now.getTime() - new Date("Jan 11, 2024 11:57:00 UTC").getTime();
let currentPhase = (msSinceNewMoon % (29.530588 * 86400000)) / (29.530588 * 86400000);
let moonOrbitAngle = currentPhase * Math.PI * 2;
let mDist = RADIUS * 2.8;
moon_cx = Math.cos(moonOrbitAngle) * mDist;
moon_cz = Math.sin(moonOrbitAngle) * mDist;
moon_cy = Math.sin(moonOrbitAngle) * RADIUS * 0.3; // 轨道倾角
}
if (currentTheme === 'cyber') {
ctx.globalCompositeOperation = 'source-over'; ctx.fillStyle = '#030408'; ctx.fillRect(0, 0, width, height);
ctx.globalCompositeOperation = 'lighter'; ctx.lineWidth = 0.8;
for (let i = 0; i < cyberNodes.length; i++) {
for (let j = i + 1; j < cyberNodes.length; j++) {
if (Math.abs(cyberNodes[i].x - cyberNodes[j].x) > currentConnectDistance || Math.abs(cyberNodes[i].y - cyberNodes[j].y) > currentConnectDistance) continue;
let dist = Math.sqrt((cyberNodes[i].x - cyberNodes[j].x)**2 + (cyberNodes[i].y - cyberNodes[j].y)**2);
if (dist < currentConnectDistance) {
ctx.beginPath(); ctx.moveTo(cyberNodes[i].x, cyberNodes[i].y); ctx.lineTo(cyberNodes[j].x, cyberNodes[j].y);
ctx.strokeStyle = `rgba(${cyberNodes[i].isCyan ? '0,242,254' : '240,18,190'}, ${(1 - dist/currentConnectDistance) * 0.7})`; ctx.stroke();
}
}
}
if (mouse.x !== -1000) {
let mCR = isOptimizedMode ? 150 : 250;
for (let i = 0; i < cyberNodes.length; i++) {
if (Math.abs(cyberNodes[i].x - mouse.x) > mCR || Math.abs(cyberNodes[i].y - mouse.y) > mCR) continue;
let dist = Math.sqrt((cyberNodes[i].x - mouse.x)**2 + (cyberNodes[i].y - mouse.y)**2);
if (dist < mCR) {
let alpha = 1 - (dist / mCR);
ctx.beginPath(); ctx.moveTo(cyberNodes[i].x, cyberNodes[i].y); ctx.lineTo(mouse.x, mouse.y);
ctx.lineWidth = 1.5; ctx.strokeStyle = mouse.isDown ? `rgba(240,18,190,${alpha*0.8})` : `rgba(0,242,254,${alpha*0.6})`; ctx.stroke();
}
}
ctx.beginPath(); ctx.arc(mouse.x, mouse.y, mouse.isDown ? 6 : 3, 0, Math.PI * 2); ctx.fillStyle = mouse.isDown ? '#f012be' : '#ffffff'; ctx.fill();
}
cyberNodes.forEach(node => { node.update(); node.draw(ctx); });
animationFrameId = requestAnimationFrame(animate); return;
}
if (currentTheme === 'manifold') {
ctx.globalCompositeOperation = 'source-over'; ctx.fillStyle = '#030610'; ctx.fillRect(0, 0, width, height);
if(time % 60 === 0 && Math.random() > 0.3) dropWave(Math.random() * width, Math.random() * height, 1, Math.random() * 80 + 20);
for (let y = 1; y < rows - 1; y++) {
for (let x = 1; x < cols - 1; x++) {
let idx = x + y * cols;
waveCurrent[idx] = (wavePrevious[idx - 1] + wavePrevious[idx + 1] + wavePrevious[idx - cols] + wavePrevious[idx + cols]) / 2 - waveCurrent[idx];
waveCurrent[idx] *= DAMPING;
let val = waveCurrent[idx], px = x * currentSpacing, py = y * currentSpacing, size = 1.5, r = 10, g = 17, b = 40;
if (Math.abs(val) > 0.1) {
size = Math.min(1.5 + Math.abs(val) * 0.15, 6);
if (val > 0) { let intensity = Math.min(val * 4, 255); r = 0; g = Math.min(intensity * 1.5, 242); b = Math.min(intensity * 2, 254); }
else { let intensity = Math.min(Math.abs(val) * 4, 255); r = Math.min(intensity * 2, 240); g = 18; b = Math.min(intensity * 1.5, 190); }
}
ctx.fillStyle = `rgb(${r}, ${g}, ${b})`; ctx.fillRect(px - size/2, py - size/2, size, size);
}
}
let temp = wavePrevious; wavePrevious = waveCurrent; waveCurrent = temp;
animationFrameId = requestAnimationFrame(animate); return;
}
if (currentTheme === 'quantum') {
ctx.globalCompositeOperation = 'source-over';
let bgGradient = ctx.createRadialGradient(width/2, height/2, 0, width/2, height/2, Math.max(width, height));
bgGradient.addColorStop(0, '#111827'); bgGradient.addColorStop(1, '#02040a');
ctx.fillStyle = bgGradient; ctx.fillRect(0, 0, width, height);
ctx.globalCompositeOperation = 'lighter';
let targetYawQ = mouse.x !== -1000 ? (mouse.x - width / 2) * 0.003 : 0;
let targetPitchQ = mouse.y !== -1000 ? (mouse.y - height / 2) * 0.003 : 0;
let globalYaw = time * 0.0036 + targetYawQ, globalPitch = Math.sin(time * 0.0018) * 0.2 + targetPitchQ;
currentExplosionScale += ((mouse.isDown ? 2.5 : 1.0) - currentExplosionScale) * 0.08;
currentHue += ((mouse.isDown ? 320 : 190) - currentHue) * 0.08;
let renderCx = width / 2;
particles.forEach(p => p.update(globalPitch, globalYaw, renderCx));
particles.sort((a, b) => b.rotatedZ - a.rotatedZ);
ctx.beginPath(); ctx.lineWidth = 1;
for (let i = 0; i < particles.length; i++) {
let p = particles[i];
if (p.rotatedZ < -RADIUS * 0.3) continue;
for (let j = 0; j < p.connections.length; j++) {
let target = p.connections[j];
if (target && target.rotatedZ >= -RADIUS * 0.3) { ctx.moveTo(p.screenX, p.screenY); ctx.lineTo(target.screenX, target.screenY); }
}
}
ctx.strokeStyle = `hsla(${currentHue}, 100%, 65%, ${mouse.isDown ? 0.05 : 0.15})`; ctx.stroke();
particles.forEach(p => {
let depth = Math.max(0, Math.min(1, (p.rotatedZ + RADIUS * currentExplosionScale) / (RADIUS * 2 * currentExplosionScale)));
let size = Math.max(0.5, depth * 3.5), alpha = 0.1 + depth * 0.9, lightness = 40 + depth * 40;
ctx.beginPath(); ctx.arc(p.screenX, p.screenY, size, 0, Math.PI * 2);
ctx.fillStyle = `hsla(${currentHue}, 100%, ${lightness}%, ${alpha})`; ctx.fill();
const isPowerSave = document.body.classList.contains('power-save-mode');
if (depth > 0.8 && !isOptimizedMode && !isPowerSave) { ctx.shadowBlur = 10; ctx.shadowColor = `hsl(${currentHue}, 100%, 60%)`; ctx.fill(); ctx.shadowBlur = 0; }
});
animationFrameId = requestAnimationFrame(animate); return;
}
ctx.globalCompositeOperation = 'source-over';
let bgGradient = ctx.createRadialGradient(width/2, height/2, 0, width/2, height/2, Math.max(width, height));
if (currentTheme === 'earth') { bgGradient.addColorStop(0, '#020611'); bgGradient.addColorStop(1, '#000000'); }
else if (currentTheme === 'solar') { bgGradient.addColorStop(0, '#2a0500'); bgGradient.addColorStop(1, '#0a0100'); }
else { bgGradient.addColorStop(0, '#1c1510'); bgGradient.addColorStop(1, '#050505'); }
ctx.fillStyle = bgGradient; ctx.fillRect(0, 0, width, height);
stars.forEach(star => {
star.x -= star.speed + (currentYaw - targetYaw) * 10;
if(star.x < 0) star.x = width; if(star.x > width) star.x = 0;
ctx.globalAlpha = star.alpha; ctx.fillStyle = star.isRed ? '#fca5a5' : (star.isGold ? '#fde68a' : '#ffffff'); ctx.fillRect(star.x, star.y, star.size, star.size);
});
ctx.globalAlpha = 1.0;
currentPitch += (targetPitch - currentPitch) * 0.1; currentYaw += (targetYaw - currentYaw) * 0.1;
if (!isDragging) baseYaw += (currentTheme === 'earth' ? 0.001 : (currentTheme === 'solar' ? 0.0015 : 0.0005));
let finalYaw = currentYaw + baseYaw, renderCx = cx;
particles.forEach(p => p.update(currentPitch, finalYaw, renderCx));
particles.sort((a, b) => b.zDepth - a.zDepth);
if (currentTheme === 'earth') {
let splitIndex = particles.findIndex(p => p.zDepth < 0);
if (splitIndex === -1) splitIndex = particles.length;
const renderParticle = (p) => {
let nLen = Math.sqrt(p.nxRot*p.nxRot + p.nyRot*p.nyRot + p.nzRot*p.nzRot);
if (nLen === 0) return;
if (p.nzRot / nLen > 0.15) return;
let dot = (p.nxRot * lx_screen + p.nyRot * ly_screen + p.nzRot * lz_screen) / nLen;
let light = 0.02; // 深夜环境光
if (dot > 0.25) light = 1.0;
else if (dot > -0.25) { // 拓宽晨昏线的过渡区域
let t = (dot + 0.25) / 0.5;
light = 0.02 + 0.98 * (t * t * (3 - 2 * t));
}
let r = p.r * light, g = p.g * light, b = p.b * light;
let isCityDrawn = false;
if (p.type === 'earth_tex' && p.cityIntensity > 0) {
if (dot < 0.1) {
let ct = Math.min(1, (0.1 - dot) / 0.35); // 灯光渐渐亮起
let cityLight = ct * ct * (3 - 2 * ct) * p.cityIntensity;
if (cityLight > 0.02) {
r += 255 * cityLight * 0.9;
g += 210 * cityLight * 0.9;
b += 100 * cityLight * 0.9;
isCityDrawn = true;
}
}
}
if (p.type === 'moon_tex' && dot < 0) {
r += 12; g += 15; b += 22;
}
ctx.fillStyle = `rgb(${Math.floor(r)}, ${Math.floor(g)}, ${Math.floor(b)})`;
let size = p.type === 'moon_tex' ? Math.max(0.5, p.scale * 2.5) : Math.max(0.8, p.scale * 3.8);
ctx.fillRect(p.px - size/2, p.py - size/2, size, size + 0.6);
if (isCityDrawn && p.zDepth < 0 && !isOptimizedMode && r > 150) {
ctx.globalCompositeOperation = 'lighter';
ctx.fillStyle = `rgba(255, 210, 100, 0.4)`;
ctx.fillRect(p.px - size, p.py - size, size * 2, size * 2);
ctx.globalCompositeOperation = 'source-over';
}
};
ctx.globalCompositeOperation = 'source-over';
for(let i = 0; i < splitIndex; i++) renderParticle(particles[i]);
ctx.beginPath(); ctx.arc(renderCx, cy, RADIUS * 0.98, 0, Math.PI * 2);
ctx.fillStyle = '#020611'; ctx.fill();
for(let i = splitIndex; i < particles.length; i++) renderParticle(particles[i]);
ctx.globalCompositeOperation = 'lighter';
let halo = ctx.createRadialGradient(
renderCx + lx_screen * RADIUS * 0.6, cy + ly_screen * RADIUS * 0.6, RADIUS * 0.7,
renderCx, cy, RADIUS * 1.3
);
halo.addColorStop(0, 'rgba(0, 180, 255, 0.25)');
halo.addColorStop(1, 'rgba(0, 180, 255, 0)');
ctx.fillStyle = halo;
ctx.fillRect(renderCx - RADIUS*1.5, cy - RADIUS*1.5, RADIUS*3, RADIUS*3);
}
else if (currentTheme === 'saturn') {
let splitIndex = particles.findIndex(p => p.zDepth < 0); if (splitIndex === -1) splitIndex = particles.length;
if (!isOptimizedMode) {
let halo = ctx.createRadialGradient(renderCx, cy, RADIUS * 0.9, renderCx, cy, RADIUS * 1.6);
halo.addColorStop(0, 'rgba(217, 119, 6, 0.25)'); halo.addColorStop(0.4, 'rgba(251, 191, 36, 0.05)'); halo.addColorStop(1, 'rgba(251, 191, 36, 0)');
ctx.fillStyle = halo; ctx.fillRect(renderCx - RADIUS*1.7, cy - RADIUS*1.7, RADIUS*3.4, RADIUS*3.4);
}
ctx.globalCompositeOperation = 'lighter';
for(let i = 0; i < splitIndex; i++) {
let p = particles[i]; let size = Math.max(1.0, p.scale * 2.2);
let shadowFactor = (!isOptimizedMode && p.type.includes('ring')) ?
0.15 + 0.85 * Math.min(1, Math.max(0, (Math.sqrt((p.px-renderCx)**2 + (p.py-cy)**2) - RADIUS*0.7) / (RADIUS*0.8))) : 1.0;
let fAlpha = p.baseAlpha * 0.45 * shadowFactor;
if (p.type === 'ring_ice') { ctx.fillStyle = `rgba(226, 232, 240, ${fAlpha * 0.9})`; ctx.fillRect(p.px - size/2, p.py - size/2, size, size); }
else if (p.type === 'ring_dust') { ctx.fillStyle = `rgba(217, 119, 6, ${fAlpha * 0.7})`; ctx.fillRect(p.px - size/2, p.py - size/2, size, size); }
else if (p.type === 'body_light') { ctx.fillStyle = `rgba(254, 243, 199, ${fAlpha * 0.85})`; ctx.fillRect(p.px - size, p.py - size/2, size*2, size); }
else if (p.type === 'body_dark') { ctx.fillStyle = `rgba(180, 83, 9, ${fAlpha * 0.85})`; ctx.fillRect(p.px - size, p.py - size/2, size*2, size); }
}
ctx.globalCompositeOperation = 'source-over'; ctx.beginPath(); ctx.arc(renderCx, cy, RADIUS * 0.98, 0, Math.PI * 2);
let planetBody = ctx.createRadialGradient(renderCx - RADIUS*0.3, cy - RADIUS*0.4, 0, renderCx, cy, RADIUS * 1.02);
planetBody.addColorStop(0, '#fef08a'); planetBody.addColorStop(0.4, '#d97706'); planetBody.addColorStop(0.75, '#78350f'); planetBody.addColorStop(0.95, '#1c1917'); planetBody.addColorStop(1, 'rgba(28, 25, 23, 0)');
ctx.fillStyle = planetBody; ctx.fill();
ctx.globalCompositeOperation = 'lighter';
for(let i = splitIndex; i < particles.length; i++) {
let p = particles[i]; let size = Math.max(1.0, p.scale * 2.2);
let fAlpha = p.baseAlpha;
if (p.type === 'ring_ice') { ctx.fillStyle = `rgba(226, 232, 240, ${fAlpha * 0.9})`; ctx.fillRect(p.px - size/2, p.py - size/2, size, size); }
else if (p.type === 'ring_dust') { ctx.fillStyle = `rgba(217, 119, 6, ${fAlpha * 0.7})`; ctx.fillRect(p.px - size/2, p.py - size/2, size, size); }
else if (p.type === 'body_light') { ctx.fillStyle = `rgba(254, 243, 199, ${fAlpha * 0.85})`; ctx.fillRect(p.px - size, p.py - size/2, size*2, size); }
else if (p.type === 'body_dark') { ctx.fillStyle = `rgba(180, 83, 9, ${fAlpha * 0.85})`; ctx.fillRect(p.px - size, p.py - size/2, size*2, size); }
}
}
else if (currentTheme === 'solar') {
let splitIndex = particles.findIndex(p => p.zDepth < 0); if (splitIndex === -1) splitIndex = particles.length;
if (!isOptimizedMode) {
let halo = ctx.createRadialGradient(renderCx, cy, RADIUS * 0.9, renderCx, cy, RADIUS * 1.6);
halo.addColorStop(0, 'rgba(249, 115, 22, 0.4)'); halo.addColorStop(0.3, 'rgba(239, 68, 68, 0.1)'); halo.addColorStop(1, 'rgba(239, 68, 68, 0)');
ctx.fillStyle = halo; ctx.fillRect(renderCx - RADIUS*1.7, cy - RADIUS*1.7, RADIUS*3.4, RADIUS*3.4);
}
ctx.fillStyle = 'rgba(239, 68, 68, 0.25)';
for(let i = 0; i < splitIndex; i++) { let size = particles[i].scale * 1.5; ctx.fillRect(particles[i].px - size/2, particles[i].py - size/2, size, size); }
ctx.beginPath(); ctx.arc(renderCx, cy, RADIUS * 0.98, 0, Math.PI * 2);
let coreGradient = ctx.createRadialGradient(renderCx - RADIUS*0.2, cy - RADIUS*0.2, 0, renderCx, cy, RADIUS);
coreGradient.addColorStop(0, '#fffbeb'); coreGradient.addColorStop(0.3, '#fde047'); coreGradient.addColorStop(0.7, '#ea580c'); coreGradient.addColorStop(0.95, '#7f1d1d'); coreGradient.addColorStop(1, '#450a0a');
ctx.fillStyle = coreGradient; ctx.fill();
ctx.globalCompositeOperation = 'lighter'; ctx.beginPath(); ctx.lineWidth = 0.8; ctx.strokeStyle = `rgba(249, 115, 22, 0.25)`;
for(let i = splitIndex; i < particles.length; i++) {
let p = particles[i];
if ((p.type === 'active') && p.connections.length > 0) {
for (let target of p.connections) { if (target.zDepth < 0) { ctx.moveTo(p.px, p.py); ctx.lineTo(target.px, target.py); } }
}
}
ctx.stroke();
for(let i = splitIndex; i < particles.length; i++) {
let p = particles[i];
if (p.type === 'active') {
let twinkle = Math.sin(time * p.pulseSpeed + p.pulsePhase) * 0.5 + 0.5, finalAlpha = p.baseAlpha * (0.5 + twinkle * 0.5), size = Math.max(1, p.scale * 3.0);
ctx.fillStyle = `rgba(${twinkle > 0.8 ? '255, 255, 255' : '253, 224, 71'}, ${finalAlpha})`; ctx.fillRect(p.px - size/2, p.py - size/2, size, size);
if (p.zDepth > RADIUS * 0.6 && twinkle > 0.7 && !isOptimizedMode) {
let bloomSize = size * 2.5; ctx.fillStyle = `rgba(253, 224, 71, ${finalAlpha * 0.4})`;
ctx.fillRect(p.px - bloomSize/2, p.py - bloomSize/2, bloomSize, bloomSize);
}
} else {
let size = Math.max(0.8, p.scale * 2.0);
ctx.fillStyle = `rgba(239, 68, 68, ${p.baseAlpha * 0.7})`; ctx.fillRect(p.px - size/2, p.py - size/2, size, size);
}
}
}
animationFrameId = requestAnimationFrame(animate);
}
const fpsSelect = document.getElementById('canvas-fps-limit');
if (fpsSelect) {
fpsSelect.value = String(fpsLimit);
fpsSelect.addEventListener('change', (e) => {
fpsLimit = parseInt(e.target.value);
localStorage.setItem('canvas_fps_limit', fpsLimit);
fpsInterval = fpsLimit > 0 ? 1000 / fpsLimit : 0;
lastFrameTime = 0;
});
}
document.addEventListener('visibilitychange', () => {
if (document.visibilityState === 'hidden') {
if (animationFrameId !== null) {
cancelAnimationFrame(animationFrameId);
animationFrameId = null;
}
} else {
if (animationFrameId === null) {
initScene();
}
}
});
})();