(function() {
'use strict';
const container = document.querySelector('.ext-popup-container');
const searchInput = document.getElementById('ext-search-input');
const searchClear = document.getElementById('ext-search-clear');
const searchIcon = document.querySelector('.ext-search-icon');
const resultsContainer = document.getElementById('ext-results');
const tabs = container.querySelectorAll('.ext-tab');
const settingsPanel = document.getElementById('ext-settings-panel');
const settingsBackBtn = document.getElementById('ext-settings-back');
const confirmOverlay = document.getElementById('ext-confirm-overlay');
const confirmMsg = document.getElementById('ext-confirm-msg');
const confirmCancel = document.getElementById('ext-confirm-cancel');
const confirmOk = document.getElementById('ext-confirm-ok');
const searchArea = document.querySelector('.ext-search-area');
const footerHint = document.querySelector('.ext-footer-hint');
let currentTab = 'history';
let activeIndex = -1;
let resultItems = [];
let debounceTimer = null;
let pendingDelete = null;
function showToast(msg) {
let el = document.getElementById('popup-toast');
if (!el) {
el = document.createElement('div');
el.id = 'popup-toast';
el.style.cssText = 'position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:rgba(255,255,255,0.12);backdrop-filter:blur(10px);color:#fff;padding:8px 20px;border-radius:20px;font-size:13px;z-index:99999;pointer-events:none;transition:opacity 0.3s;white-space:nowrap;';
document.body.appendChild(el);
}
el.textContent = msg;
el.style.opacity = '1';
clearTimeout(el._timeout);
el._timeout = setTimeout(function() { el.style.opacity = '0'; }, 1500);
}
const SETTINGS_KEY = 'binixovo_ext_settings';
const LAST_TAB_KEY = 'binixovo_last_tab';
const VISITS_KEY = 'binixovo_bookmark_visits';
function loadSettings() {
try {
var raw = localStorage.getItem(SETTINGS_KEY);
return raw ? JSON.parse(raw) : {
defaultTab: 'unified',
themeColor: '#ff453a',
sortByVisits: true,
dateFold: true,
deleteConfirm: true,
autoExpandDate: true,
rememberLastTab: false
};
} catch (e) { return { defaultTab: 'unified', themeColor: '#ff453a', sortByVisits: true, dateFold: true, deleteConfirm: true, autoExpandDate: true, rememberLastTab: false }; }
}
function saveSettings(s) {
localStorage.setItem(SETTINGS_KEY, JSON.stringify(s));
}
function applySettings(s) {
container.style.setProperty('--ext-accent', s.themeColor);
container.style.setProperty('--ext-accent-hover', s.themeColor + 'cc');
var sel = document.getElementById('ext-setting-default-tab');
if (sel) sel.value = s.defaultTab;
var colorInput = document.getElementById('ext-setting-theme-color');
if (colorInput) colorInput.value = s.themeColor;
var sortCb = document.getElementById('ext-setting-sort-visit');
if (sortCb) sortCb.checked = s.sortByVisits;
var dateCb = document.getElementById('ext-setting-date-fold');
if (dateCb) dateCb.checked = s.dateFold;
var delCb = document.getElementById('ext-setting-delete-confirm');
if (delCb) delCb.checked = s.deleteConfirm;
var autoExpCb = document.getElementById('ext-setting-auto-expand-date');
if (autoExpCb) autoExpCb.checked = s.autoExpandDate;
var remCb = document.getElementById('ext-setting-remember-last-tab');
if (remCb) remCb.checked = s.rememberLastTab;
var defGroup = document.getElementById('ext-default-tab-group');
if (defGroup) defGroup.style.display = s.rememberLastTab ? 'none' : '';
}
var settings = loadSettings();
applySettings(settings);
document.getElementById('ext-setting-default-tab').addEventListener('change', function() {
settings.defaultTab = this.value;
saveSettings(settings);
});
document.getElementById('ext-setting-theme-color').addEventListener('input', function() {
settings.themeColor = this.value;
saveSettings(settings);
container.style.setProperty('--ext-accent', this.value);
container.style.setProperty('--ext-accent-hover', this.value + 'cc');
});
document.getElementById('ext-setting-sort-visit').addEventListener('change', function() {
settings.sortByVisits = this.checked;
saveSettings(settings);
if (currentTab === 'bookmarks') { activeIndex = -1; renderResults(searchInput.value); }
});
document.getElementById('ext-setting-delete-confirm').addEventListener('change', function() {
settings.deleteConfirm = this.checked;
saveSettings(settings);
});
document.getElementById('ext-setting-date-fold').addEventListener('change', function() {
settings.dateFold = this.checked;
saveSettings(settings);
activeIndex = -1; renderResults(searchInput.value);
});
document.getElementById('ext-setting-auto-expand-date').addEventListener('change', function() {
settings.autoExpandDate = this.checked;
saveSettings(settings);
activeIndex = -1; renderResults(searchInput.value);
});
document.getElementById('ext-setting-remember-last-tab').addEventListener('change', function() {
settings.rememberLastTab = this.checked;
saveSettings(settings);
var defGroup = document.getElementById('ext-default-tab-group');
if (defGroup) defGroup.style.display = this.checked ? 'none' : '';
});
document.getElementById('ext-clear-bookmarks-stats').addEventListener('click', function() {
if (confirm('确定要清除所有书签访问统计数据吗？此操作不可撤销。')) {
localStorage.removeItem(VISITS_KEY);
showToast('已清除书签访问统计');
if (currentTab === 'bookmarks') { activeIndex = -1; renderResults(searchInput.value); }
}
});
document.getElementById('ext-clear-history').addEventListener('click', function() {
if (confirm('确定要清除所有浏览历史记录吗？此操作不可撤销。')) {
chrome.history.deleteAll(function() {
showToast('已清除所有历史记录');
if (currentTab === 'history') { activeIndex = -1; renderResults(searchInput.value); }
});
}
});
function getVisitCounts() {
try { var raw = localStorage.getItem(VISITS_KEY); return raw ? JSON.parse(raw) : {}; }
catch (e) { return {}; }
}
function incrementVisit(url) {
var visits = getVisitCounts();
visits[url] = (visits[url] || 0) + 1;
localStorage.setItem(VISITS_KEY, JSON.stringify(visits));
}
function flattenBookmarks(node, result) {
if (node.url) {
result.push({ id: node.id, title: node.title || '(无标题)', url: node.url, dateAdded: node.dateAdded || Date.now() });
}
if (node.children) { node.children.forEach(function(child) { flattenBookmarks(child, result); }); }
}
function loadBookmarks(callback) {
if (typeof chrome !== 'undefined' && chrome.bookmarks) {
chrome.bookmarks.getTree(function(tree) {
var items = [];
if (tree && tree.length > 0) flattenBookmarks(tree[0], items);
if (settings.sortByVisits) {
var visits = getVisitCounts();
items.forEach(function(item) {
item.visitCount = visits[item.url] || 0;
item.favicon = getFaviconForUrl(item.url);
item.tag = getDomain(item.url);
item.date = formatDateIso(item.dateAdded);
});
items.sort(function(a, b) { return b.visitCount - a.visitCount || b.dateAdded - a.dateAdded; });
} else {
items.forEach(function(item) {
item.favicon = getFaviconForUrl(item.url);
item.tag = getDomain(item.url);
item.date = formatDateIso(item.dateAdded);
item.visitCount = 0;
});
items.sort(function(a, b) { return b.dateAdded - a.dateAdded; });
}
callback(items);
});
} else { callback([]); }
}
function loadHistory(callback) {
if (typeof chrome !== 'undefined' && chrome.history) {
var oneMonthAgo = Date.now() - 30 * 24 * 60 * 60 * 1000;
chrome.history.search({ text: '', maxResults: 100, startTime: oneMonthAgo }, function(items) {
var result = items.slice(0, 100).map(function(item) {
return {
id: item.url,
title: item.title || '(无标题)',
url: item.url,
lastVisitTime: item.lastVisitTime || Date.now(),
visitCount: item.visitCount || 1,
favicon: getFaviconForUrl(item.url),
tag: getDomain(item.url),
date: formatDateIso(item.lastVisitTime || Date.now()),
time: formatRelativeTime(item.lastVisitTime || Date.now())
};
});
result.sort(function(a, b) { return b.lastVisitTime - a.lastVisitTime; });
callback(result);
});
} else { callback([]); }
}
function loadDownloads(callback) {
if (typeof chrome !== 'undefined' && chrome.downloads) {
chrome.downloads.search({ limit: 50, orderBy: ['-startTime'] }, function(items) {
var result = items.map(function(item) {
return {
id: item.id,
title: item.filename ? item.filename.split(/[\\/]/).pop() : '(未知文件)',
url: item.url,
filePath: item.filename || '',
fileSize: formatFileSize(item.fileSize || 0),
startTime: item.startTime || '',
state: item.state || '',
favicon: getFileIcon(item.filename || ''),
tag: getFileType(item.filename || ''),
date: formatDateIso(new Date(item.startTime || Date.now()).getTime())
};
});
result.sort(function(a, b) {
return new Date(b.startTime).getTime() - new Date(a.startTime).getTime();
});
callback(result);
});
} else { callback([]); }
}
function loadUnified(callback) {
var pending = 3;
var allItems = [];
loadBookmarks(function(items) {
items.forEach(function(item) { item.source = 'bookmarks'; item._sortKey = item.dateAdded || 0; });
allItems.push.apply(allItems, items);
if (--pending === 0) finish();
});
loadHistory(function(items) {
items.forEach(function(item) { item.source = 'history'; item._sortKey = item.lastVisitTime || 0; });
allItems.push.apply(allItems, items);
if (--pending === 0) finish();
});
loadDownloads(function(items) {
items.forEach(function(item) { item.source = 'downloads'; item._sortKey = new Date(item.startTime).getTime() || 0; });
allItems.push.apply(allItems, items);
if (--pending === 0) finish();
});
function finish() {
allItems.sort(function(a, b) { return b._sortKey - a._sortKey; });
callback(allItems);
}
}
function getFaviconForUrl(url) {
try {
return `chrome-extension://${chrome.runtime.id}/_favicon/?pageUrl=${encodeURIComponent(url)}&size=32`;
} catch (e) { return ''; }
}
function getDomain(url) {
try { return new URL(url).hostname.replace('www.', ''); }
catch (e) { return url.substring(0, 30); }
}
function formatDateIso(ts) {
var d = new Date(ts);
return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
}
function formatRelativeTime(ts) {
var now = Date.now(), diff = now - ts;
if (diff < 60000) return '刚刚';
if (diff < 3600000) return Math.floor(diff / 60000) + ' 分钟前';
if (diff < 86400000) return Math.floor(diff / 3600000) + ' 小时前';
if (diff < 172800000) return '昨天';
if (diff < 604800000) return Math.floor(diff / 86400000) + ' 天前';
var d = new Date(ts);
return (d.getMonth() + 1) + '/' + d.getDate();
}
function formatFileSize(bytes) {
if (bytes === 0) return '0 B';
var units = ['B', 'KB', 'MB', 'GB'];
var i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
return (bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1) + ' ' + units[i];
}
function getFileIcon(filename) {
var ext = (filename || '').split('.').pop().toLowerCase();
var map = { pdf: '📄', zip: '📦', rar: '📦', '7z': '📦', jpg: '🖼️', jpeg: '🖼️', png: '🖼️', gif: '🖼️', webp: '🖼️', svg: '🖼️', mp4: '🎬', mov: '🎬', avi: '🎬', mkv: '🎬', mp3: '🎵', wav: '🎵', flac: '🎵', exe: '⚙️', msi: '⚙️', apk: '📱', doc: '📝', docx: '📝', xls: '📊', xlsx: '📊', ppt: '📽️', pptx: '📽️', txt: '📃', md: '📃', json: '📋', xml: '📋', csv: '📋', html: '🌐', css: '🎨', js: '📜', ts: '📜', py: '🐍' };
return map[ext] || '📁';
}
function getFileType(filename) {
var ext = (filename || '').split('.').pop().toLowerCase();
var map = { pdf: 'PDF', zip: '压缩包', rar: '压缩包', '7z': '压缩包', jpg: '图片', jpeg: '图片', png: '图片', gif: '图片', webp: '图片', svg: '图片', mp4: '视频', mov: '视频', avi: '视频', mkv: '视频', mp3: '音频', wav: '音频', flac: '音频', exe: '安装包', msi: '安装包', apk: '安装包', doc: '文档', docx: '文档', xls: '表格', xlsx: '表格', ppt: '演示', pptx: '演示', txt: '文本', md: '文本', json: '数据', xml: '数据', csv: '数据', html: '网页', css: '样式', js: '脚本', ts: '脚本', py: '脚本' };
return map[ext] || ext.toUpperCase();
}
function getFileEmoji(tag) {
var map = { 'PDF': '📄', '压缩包': '📦', '图片': '🖼️', '视频': '🎬', '音频': '🎵', '安装包': '⚙️', '文档': '📝', '表格': '📊', '演示': '📽️', '文本': '📃', '网页': '🌐', '样式': '🎨', '脚本': '📜', '数据': '📋' };
return map[tag] || '📁';
}
function escapeHtml(str) { var div = document.createElement('div'); div.textContent = str; return div.innerHTML; }
function escapeHtmlAttr(str) {
return String(str).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
function initPopup() {
var defaultTab = settings.defaultTab || 'unified';
if (settings.rememberLastTab !== false) {
var lastTab = localStorage.getItem(LAST_TAB_KEY);
if (lastTab && container.querySelector('.ext-tab[data-tab="' + lastTab + '"]')) {
defaultTab = lastTab;
}
}
currentTab = defaultTab;
tabs.forEach(function(t) { t.classList.remove('active'); });
var defaultTabBtn = container.querySelector('.ext-tab[data-tab="' + defaultTab + '"]');
if (defaultTabBtn) defaultTabBtn.classList.add('active');
activeIndex = -1;
renderResults('');
searchInput.focus();
}
tabs.forEach(function(tab) {
tab.addEventListener('click', function() {
tabs.forEach(function(t) { t.classList.remove('active'); });
tab.classList.add('active');
currentTab = tab.dataset.tab;
searchInput.value = '';
searchClear.style.display = 'none';
activeIndex = -1;
settingsPanel.style.display = 'none';
localStorage.setItem(LAST_TAB_KEY, currentTab);
if (currentTab === 'search') {
showSearchMode();
} else {
hideSearchMode();
}
renderResults('');
searchInput.focus();
});
});
searchInput.addEventListener('input', function() {
var val = searchInput.value;
searchClear.style.display = val ? 'flex' : 'none';
clearTimeout(debounceTimer);
debounceTimer = setTimeout(function() { activeIndex = -1; renderResults(val); }, 250);
});
searchClear.addEventListener('click', function() {
searchInput.value = '';
searchClear.style.display = 'none';
activeIndex = -1;
renderResults('');
searchInput.focus();
});
if (searchIcon) {
searchIcon.style.cursor = 'pointer';
searchIcon.addEventListener('click', function() {
clearTimeout(debounceTimer);
activeIndex = -1;
renderResults(searchInput.value);
});
}
function filterItems(items, query) {
if (!query.trim()) return items;
var q = query.toLowerCase();
return items.filter(function(item) {
return (item.title || '').toLowerCase().indexOf(q) !== -1 ||
(item.url || '').toLowerCase().indexOf(q) !== -1 ||
(item.tag || '').toLowerCase().indexOf(q) !== -1;
});
}
function groupByDate(items) {
var groups = new Map();
items.forEach(function(item) {
var d = item.date || '未知';
if (!groups.has(d)) groups.set(d, []);
groups.get(d).push(item);
});
return Array.from(groups.entries()).sort(function(a, b) { return b[0].localeCompare(a[0]); });
}
function formatDateLabel(dateStr) {
var today = formatDateIso(Date.now());
var yesterday = formatDateIso(Date.now() - 86400000);
if (dateStr === today) return '今天';
if (dateStr === yesterday) return '昨天';
try {
var d = new Date(dateStr + 'T00:00:00');
if (isNaN(d.getTime())) return dateStr;
var weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
return dateStr + ' ' + weekdays[d.getDay()];
} catch (e) { return dateStr; }
}
function renderResults(query) {
resultsContainer.innerHTML = '<div class="ext-loading"><span>加载中...</span></div>';
function doRender(items) {
resultItems = [];
var filtered;
var q = (query || '').trim();
if ((currentTab === 'bookmarks' || currentTab === 'unified') && q === '访问') {
var visits = getVisitCounts();
filtered = items.slice();
filtered.forEach(function(item) {
item.visitCount = visits[item.url] || 0;
});
filtered.sort(function(a, b) { return b.visitCount - a.visitCount; });
} else {
filtered = filterItems(items, query);
}
if (!q) {
filtered = filtered.slice(0, 30);
}
resultItems = filtered;
resultsContainer.innerHTML = '';
if (filtered.length === 0) {
resultsContainer.innerHTML = '<div class="ext-empty-state"><svg width="40" height="40" viewBox="0 0 40 40" fill="none" opacity="0.3"><circle cx="18" cy="18" r="8" stroke="currentColor" stroke-width="2"/><path d="M23.5 23.5L31 31" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/></svg><p>' + (query ? '没有匹配的结果' : '输入关键词开始搜索') + '</p></div>';
return;
}
if (settings.dateFold) {
var groups = groupByDate(filtered);
var groupDomMap = [];
groups.forEach(function(g) {
var date = g[0];
var groupItems = g[1];
var groupDiv = document.createElement('div');
groupDiv.className = 'ext-date-group' + (settings.autoExpandDate ? '' : ' collapsed');
groupDiv.dataset.date = date;
var header = document.createElement('div');
header.className = 'ext-date-header';
header.tabIndex = 0;
header.innerHTML = '<span class="ext-date-arrow"><svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M4 2l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></span><span class="ext-date-label">' + formatDateLabel(date) + '</span><span class="ext-date-count">' + groupItems.length + ' 条</span>';
header.addEventListener('click', function(e) {
e.stopPropagation();
groupDiv.classList.toggle('collapsed');
});
var content = document.createElement('div');
content.className = 'ext-date-content';
var itemRefs = [];
groupItems.forEach(function(item, idx) {
var entry = createResultElement(item);
content.appendChild(entry.el);
itemRefs.push(entry);
});
groupDiv.appendChild(header);
groupDiv.appendChild(content);
resultsContainer.appendChild(groupDiv);
groupDomMap.push({ header: header, groupDiv: groupDiv, itemRefs: itemRefs });
});
resultsContainer._groupDomMap = groupDomMap;
} else {
var itemRefs = [];
filtered.forEach(function(item, idx) {
var entry = createResultElement(item);
resultsContainer.appendChild(entry.el);
itemRefs.push(entry);
});
resultsContainer._groupDomMap = [{ itemRefs: itemRefs }];
}
}
if (currentTab === 'bookmarks') { loadBookmarks(doRender); }
else if (currentTab === 'history') { loadHistory(doRender); }
else if (currentTab === 'downloads') { loadDownloads(doRender); }
else if (currentTab === 'unified' || currentTab === 'search') { loadUnified(doRender); }
}
function bindFaviconFallback(el, faviconUrl) {
var faviconEl = el.querySelector('.ext-result-favicon');
var textEl = el.querySelector('.ext-result-icon-text');
if (!faviconEl || !faviconUrl) {
if (faviconEl) faviconEl.remove();
return;
}
faviconEl.addEventListener('load', function() {
faviconEl.classList.add('loaded');
if (textEl) textEl.classList.add('hidden');
});
faviconEl.addEventListener('error', function() {
faviconEl.remove();
});
}
function createResultElement(item) {
var el = document.createElement('div');
el.className = 'ext-result-item';
if ((currentTab === 'downloads' || currentTab === 'unified' || currentTab === 'search') && (item.state === 'interrupted' || item.state === 'canceled')) {
el.classList.add('ext-download-canceled');
}
el.tabIndex = 0;
var copyBtn = '<button class="ext-action-btn ext-action-copy" title="复制链接" data-action="copy" data-url="' + escapeHtmlAttr(item.url || '') + '"><svg width="14" height="14" viewBox="0 0 14 14" fill="none"><rect x="5" y="5" width="8" height="8" rx="1.5" stroke="currentColor" stroke-width="1.2"/><path d="M3 9V2.5A1.5 1.5 0 0 1 4.5 1H9" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg></button>';
var deleteBtn = '<button class="ext-action-btn ext-action-delete" title="删除" data-action="delete" data-id="' + escapeHtmlAttr(item.id || '') + '" data-url="' + escapeHtmlAttr(item.url || '') + '" data-title="' + escapeHtmlAttr(item.title || '') + '"><svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 3.5h10M5 3.5V2.5A1 1 0 0 1 6 1.5h2a1 1 0 0 1 1 1v1" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/><path d="M3.5 3.5v9a1 1 0 0 0 1 1h5a1 1 0 0 0 1-1v-9" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg></button>';
if (currentTab === 'bookmarks') {
var firstChar = (item.title || 'B')[0];
var faviconHtml = '<span class="ext-result-icon-text">' + firstChar + '</span><img class="ext-result-favicon" src="' + escapeHtml(item.favicon || '') + '">';
var visitBadge = (item.visitCount > 0 && settings.sortByVisits) ? '<span class="ext-tag ext-tag-visit">访问' + item.visitCount + '次</span>' : '';
el.innerHTML = '<div class="ext-result-icon">' + faviconHtml + '</div><div class="ext-result-main"><span class="ext-result-title">' + escapeHtml(item.title) + '</span><span class="ext-result-url">' + escapeHtml(item.url) + '</span></div><div class="ext-result-tags"><span class="ext-tag ext-tag-bookmark">' + escapeHtml(item.tag || '') + '</span>' + visitBadge + '</div><div class="ext-result-actions">' + copyBtn + deleteBtn + '</div>';
bindFaviconFallback(el, item.favicon);
} else if (currentTab === 'history') {
firstChar = (item.title || 'H')[0];
faviconHtml = '<span class="ext-result-icon-text">' + firstChar + '</span><img class="ext-result-favicon" src="' + escapeHtml(item.favicon || '') + '">';
el.innerHTML = '<div class="ext-result-icon">' + faviconHtml + '</div><div class="ext-result-main"><span class="ext-result-title">' + escapeHtml(item.title) + '</span><span class="ext-result-url">' + escapeHtml(item.url) + '</span></div><div class="ext-result-tags"><span class="ext-tag ext-tag-history">' + escapeHtml(item.tag || '') + '</span><span class="ext-tag ext-tag-default">' + escapeHtml(item.time || '') + '</span></div><div class="ext-result-actions">' + copyBtn + deleteBtn + '</div>';
bindFaviconFallback(el, item.favicon);
} else if (currentTab === 'downloads') {
var stateLabel = item.state === 'interrupted' ? '<span class="ext-tag ext-tag-warning">已取消</span>' : (item.state === 'complete' ? '<span class="ext-tag ext-tag-success">已完成</span>' : '');
var folderBtn = '<button class="ext-action-btn ext-action-folder" title="打开文件夹" data-action="folder" data-id="' + escapeHtmlAttr(item.id || '') + '"><svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1.5 3.5A1 1 0 0 1 2.5 2.5h2.8l1.2 1.5h4A1 1 0 0 1 11.5 5v6a1 1 0 0 1-1 1h-8a1 1 0 0 1-1-1V3.5Z" stroke="currentColor" stroke-width="1.2"/></svg></button>';
var redownloadBtn = '<button class="ext-action-btn ext-action-redownload" title="重新下载" data-action="redownload" data-url="' + escapeHtmlAttr(item.url || '') + '"><svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M7 1.5v7M4 6l3 3 3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M1.5 9.5v1.5a1 1 0 0 0 1 1h9a1 1 0 0 0 1-1V9.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg></button>';
el.innerHTML = '<div class="ext-result-icon">' + getFileEmoji(item.tag) + '</div><div class="ext-result-main"><span class="ext-result-title">' + escapeHtml(item.title) + '</span><span class="ext-result-url">' + escapeHtml(item.fileSize || '') + ' ' + stateLabel + '</span></div><div class="ext-result-tags"><span class="ext-tag ext-tag-download">' + escapeHtml(item.tag || '') + '</span></div><div class="ext-result-actions">' + copyBtn + folderBtn + redownloadBtn + deleteBtn + '</div>';
} else if (currentTab === 'unified' || currentTab === 'search') {
deleteBtn = '<button class="ext-action-btn ext-action-delete" title="删除" data-action="delete" data-id="' + escapeHtmlAttr(item.id || '') + '" data-url="' + escapeHtmlAttr(item.url || '') + '" data-title="' + escapeHtmlAttr(item.title || '') + '" data-source="' + escapeHtmlAttr(item.source || '') + '"><svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 3.5h10M5 3.5V2.5A1 1 0 0 1 6 1.5h2a1 1 0 0 1 1 1v1" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/><path d="M3.5 3.5v9a1 1 0 0 0 1 1h5a1 1 0 0 0 1-1v-9" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg></button>';
var isDownload = item.source === 'downloads';
var sourceLabel = item.source === 'bookmarks' ? '书签' : (item.source === 'history' ? '历史' : '下载');
var sourceTagClass = item.source === 'bookmarks' ? 'ext-tag-bookmark' : ('ext-tag-' + item.source);
var sourceBadge = '<span class="ext-tag ' + sourceTagClass + '">' + sourceLabel + '</span>';
if (isDownload) {
stateLabel = item.state === 'interrupted' ? '<span class="ext-tag ext-tag-warning">已取消</span>' : (item.state === 'complete' ? '<span class="ext-tag ext-tag-success">已完成</span>' : '');
folderBtn = '<button class="ext-action-btn ext-action-folder" title="打开文件夹" data-action="folder" data-id="' + escapeHtmlAttr(item.id || '') + '"><svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1.5 3.5A1 1 0 0 1 2.5 2.5h2.8l1.2 1.5h4A1 1 0 0 1 11.5 5v6a1 1 0 0 1-1 1h-8a1 1 0 0 1-1-1V3.5Z" stroke="currentColor" stroke-width="1.2"/></svg></button>';
redownloadBtn = '<button class="ext-action-btn ext-action-redownload" title="重新下载" data-action="redownload" data-url="' + escapeHtmlAttr(item.url || '') + '"><svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M7 1.5v7M4 6l3 3 3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M1.5 9.5v1.5a1 1 0 0 0 1 1h9a1 1 0 0 0 1-1V9.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg></button>';
el.innerHTML = '<div class="ext-result-icon">' + getFileEmoji(item.tag) + '</div><div class="ext-result-main"><span class="ext-result-title">' + escapeHtml(item.title) + '</span><span class="ext-result-url">' + escapeHtml(item.fileSize || '') + ' ' + stateLabel + '</span></div><div class="ext-result-tags">' + sourceBadge + '<span class="ext-tag ext-tag-download">' + escapeHtml(item.tag || '') + '</span></div><div class="ext-result-actions">' + copyBtn + folderBtn + redownloadBtn + deleteBtn + '</div>';
} else {
firstChar = (item.title || 'U')[0];
faviconHtml = '<span class="ext-result-icon-text">' + firstChar + '</span><img class="ext-result-favicon" src="' + escapeHtml(item.favicon || '') + '">';
visitBadge = (item.source === 'bookmarks' && item.visitCount > 0) ? '<span class="ext-tag ext-tag-visit">访问' + item.visitCount + '次</span>' : '';
var timeBadge = item.source === 'history' ? '<span class="ext-tag ext-tag-default">' + escapeHtml(item.time || '') + '</span>' : '';
el.innerHTML = '<div class="ext-result-icon">' + faviconHtml + '</div><div class="ext-result-main"><span class="ext-result-title">' + escapeHtml(item.title) + '</span><span class="ext-result-url">' + escapeHtml(item.url) + '</span></div><div class="ext-result-tags">' + sourceBadge + '<span class="ext-tag ' + sourceTagClass + '">' + escapeHtml(item.tag || '') + '</span>' + visitBadge + timeBadge + '</div><div class="ext-result-actions">' + copyBtn + deleteBtn + '</div>';
bindFaviconFallback(el, item.favicon);
}
}
el.addEventListener('click', function(e) {
if (e.target.closest('.ext-action-btn')) return;
openItem(item);
});
return { el: el, item: item };
}
resultsContainer.addEventListener('error', function(e) {
if (e.target.classList.contains('ext-result-favicon')) {
var textEl = e.target.parentElement.querySelector('.ext-result-icon-text');
if (textEl) textEl.classList.remove('hidden');
e.target.remove();
}
}, true);
resultsContainer.addEventListener('click', function(e) {
var btn = e.target.closest('.ext-action-btn');
if (!btn) return;
e.preventDefault();
e.stopPropagation();
var action = btn.dataset.action;
var itemUrl = btn.dataset.url || '';
var itemId = btn.dataset.id || '';
var itemTitle = btn.dataset.title || '';
var itemSource = btn.dataset.source || '';
if (action === 'copy') {
navigator.clipboard.writeText(itemUrl).then(function() {
showToast('链接已复制');
}).catch(function() {
var ta = document.createElement('textarea');
ta.value = itemUrl;
ta.style.cssText = 'position:fixed;left:-9999px;';
document.body.appendChild(ta);
ta.select();
document.execCommand('copy');
document.body.removeChild(ta);
showToast('链接已复制');
});
} else if (action === 'delete') {
if (settings.deleteConfirm) {
var tempItem = { id: itemId, url: itemUrl, title: itemTitle, source: itemSource };
pendingDelete = { item: tempItem, callback: function() { activeIndex = -1; renderResults(searchInput.value); searchInput.focus(); } };
confirmMsg.textContent = '确定要删除 "' + (itemTitle || '此项').substring(0, 80) + '" 吗？';
confirmOverlay.style.display = 'flex';
} else {
executeDelete(itemId, itemUrl, function() { activeIndex = -1; renderResults(searchInput.value); searchInput.focus(); }, itemSource);
}
} else if (action === 'folder') {
if (itemId && typeof chrome !== 'undefined' && chrome.downloads) {
chrome.downloads.show(parseInt(itemId));
}
} else if (action === 'redownload') {
if (itemUrl && typeof chrome !== 'undefined' && chrome.downloads) {
chrome.downloads.download({ url: itemUrl }, function() { showToast('已开始重新下载'); });
}
}
});
function executeDelete(id, url, callback, source) {
if (currentTab === 'bookmarks') {
if (typeof chrome !== 'undefined' && chrome.bookmarks && id) {
chrome.bookmarks.remove(id, function() { showToast('已删除书签'); if (callback) callback(); });
}
} else if (currentTab === 'history') {
if (typeof chrome !== 'undefined' && chrome.history && url) {
chrome.history.deleteUrl({ url: url }, function() { showToast('已删除历史记录'); if (callback) callback(); });
}
} else if (currentTab === 'downloads') {
if (typeof chrome !== 'undefined' && chrome.downloads && id) {
chrome.downloads.erase({ id: parseInt(id) }, function() { showToast('已清除下载记录'); if (callback) callback(); });
}
} else if (currentTab === 'unified' || currentTab === 'search') {
if (source === 'bookmarks' && typeof chrome !== 'undefined' && chrome.bookmarks && id) {
chrome.bookmarks.remove(id, function() { showToast('已删除书签'); if (callback) callback(); });
} else if (source === 'history' && typeof chrome !== 'undefined' && chrome.history && url) {
chrome.history.deleteUrl({ url: url }, function() { showToast('已删除历史记录'); if (callback) callback(); });
} else if (source === 'downloads' && typeof chrome !== 'undefined' && chrome.downloads && id) {
chrome.downloads.erase({ id: parseInt(id) }, function() { showToast('已清除下载记录'); if (callback) callback(); });
}
}
}
function openItem(item) {
if (currentTab === 'downloads' || ((currentTab === 'unified' || currentTab === 'search') && item.source === 'downloads')) {
if (item.id && typeof chrome !== 'undefined' && chrome.downloads) {
chrome.downloads.show(item.id);
} else if (item.filePath) {
window.open('file:///' + item.filePath.replace(/\\/g, '/'));
}
} else if (currentTab === 'bookmarks' || ((currentTab === 'unified' || currentTab === 'search') && item.source === 'bookmarks')) {
incrementVisit(item.url);
window.open(item.url, '_blank');
} else {
window.open(item.url, '_blank');
}
}
function hideDeleteConfirm() { confirmOverlay.style.display = 'none'; pendingDelete = null; }
confirmCancel.addEventListener('click', hideDeleteConfirm);
confirmOverlay.addEventListener('click', function(e) { if (e.target === confirmOverlay) hideDeleteConfirm(); });
confirmOk.addEventListener('click', function() {
if (!pendingDelete) return;
var item = pendingDelete.item;
var callback = pendingDelete.callback;
hideDeleteConfirm();
executeDelete(item.id, item.url, callback, item.source || '');
});
function doDelete() {
if (activeIndex < 0 || activeIndex >= resultItems.length) return;
var item = resultItems[activeIndex];
function refresh() { activeIndex = -1; renderResults(searchInput.value); searchInput.focus(); }
if (settings.deleteConfirm) {
pendingDelete = { item: item, callback: refresh };
confirmMsg.textContent = '确定要删除 "' + (item.title || '此项').substring(0, 80) + '" 吗？';
confirmOverlay.style.display = 'flex';
} else {
executeDelete(item.id, item.url, refresh, item.source || '');
}
}
document.addEventListener('keydown', function(e) {
if (confirmOverlay.style.display === 'flex') {
if (e.key === 'Escape') { e.preventDefault(); hideDeleteConfirm(); }
return;
}
if (settingsPanel.style.display === 'flex' && e.key === 'Escape') {
e.preventDefault();
settingsPanel.style.display = 'none';
searchInput.focus();
return;
}
function getNavElements() {
var groups = resultsContainer.querySelectorAll('.ext-date-group');
var nav = [];
var flatIdx = 0;
if (groups.length > 0) {
groups.forEach(function(g) {
var isCollapsed = g.classList.contains('collapsed');
nav.push({ type: 'header', el: g.querySelector('.ext-date-header'), groupDiv: g });
if (!isCollapsed) {
var items = g.querySelectorAll('.ext-result-item');
items.forEach(function(itemEl, i) {
nav.push({ type: 'item', el: itemEl, groupDiv: g, itemIndex: flatIdx });
flatIdx++;
});
}
});
} else {
var items = resultsContainer.querySelectorAll('.ext-result-item');
items.forEach(function(itemEl) {
nav.push({ type: 'item', el: itemEl, groupDiv: null, itemIndex: flatIdx });
flatIdx++;
});
}
return nav;
}
var navElements = getNavElements();
var currentFocused = document.activeElement;
var currentNavIdx = -1;
for (var i = 0; i < navElements.length; i++) {
if (navElements[i].el === currentFocused) { currentNavIdx = i; break; }
}
if (e.key === 'ArrowDown') {
e.preventDefault();
if (navElements.length === 0) return;
var nextIdx = currentNavIdx < 0 ? 0 : Math.min(currentNavIdx + 1, navElements.length - 1);
focusNavElement(navElements[nextIdx]);
activeIndex = navElements[nextIdx].type === 'item' ? navElements[nextIdx].itemIndex : -1;
highlightActiveByIndex(activeIndex);
} else if (e.key === 'ArrowUp') {
e.preventDefault();
if (navElements.length === 0) return;
var prevIdx = currentNavIdx < 0 ? 0 : Math.max(currentNavIdx - 1, 0);
focusNavElement(navElements[prevIdx]);
activeIndex = navElements[prevIdx].type === 'item' ? navElements[prevIdx].itemIndex : -1;
highlightActiveByIndex(activeIndex);
} else if (e.key === 'ArrowRight') {
e.preventDefault();
var group = findCurrentGroup(currentFocused);
if (group && group.classList.contains('collapsed')) { group.classList.remove('collapsed'); }
} else if (e.key === 'ArrowLeft') {
e.preventDefault();
var groupL = findCurrentGroup(currentFocused);
if (groupL && !groupL.classList.contains('collapsed')) {
groupL.classList.add('collapsed');
if (currentFocused && groupL.contains(currentFocused) && !currentFocused.classList.contains('ext-date-header')) {
groupL.querySelector('.ext-date-header').focus();
}
}
} else if (e.key === 'Delete') {
e.preventDefault();
doDelete();
} else if (e.key === 'Enter') {
e.preventDefault();
if (currentFocused && currentFocused.classList.contains('ext-date-header')) {
currentFocused.closest('.ext-date-group').classList.toggle('collapsed');
} else if (activeIndex >= 0 && activeIndex < resultItems.length) {
openItem(resultItems[activeIndex]);
} else if (currentTab === 'search') {
var q = searchInput.value.trim();
if (q) doEngineSearch(q);
}
} else if (e.key === 'Tab') {
e.preventDefault();
var tabKeys = ['bookmarks', 'history', 'downloads', 'unified', 'search'];
var curIdx = tabKeys.indexOf(currentTab);
var nextTabIdx = e.shiftKey ? (curIdx - 1 + 5) % 5 : (curIdx + 1) % 5;
var nextKey = tabKeys[nextTabIdx];
tabs.forEach(function(t) { t.classList.remove('active'); });
container.querySelector('.ext-tab[data-tab="' + nextKey + '"]').classList.add('active');
currentTab = nextKey;
searchInput.value = '';
searchClear.style.display = 'none';
activeIndex = -1;
settingsPanel.style.display = 'none';
renderResults('');
if (currentTab === 'search') {
showSearchMode();
} else {
hideSearchMode();
}
searchInput.focus();
}
});
function findCurrentGroup(focusedEl) {
if (!focusedEl) return null;
if (focusedEl.classList.contains('ext-date-header')) return focusedEl.closest('.ext-date-group');
if (focusedEl.classList.contains('ext-result-item')) return focusedEl.closest('.ext-date-group');
return null;
}
function focusNavElement(navEntry) {
if (navEntry && navEntry.el) {
navEntry.el.focus();
navEntry.el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
}
}
function highlightActiveByIndex(idx) {
var allItems = resultsContainer.querySelectorAll('.ext-result-item');
allItems.forEach(function(el) { el.classList.remove('active'); });
var visibleIdx = 0;
for (var i = 0; i < allItems.length; i++) {
var group = allItems[i].closest('.ext-date-group');
if (group && group.classList.contains('collapsed')) continue;
if (visibleIdx === idx) { allItems[i].classList.add('active'); break; }
visibleIdx++;
}
}
var currentTheme = localStorage.getItem('popup_theme') || 'light';
if (currentTheme === 'dark') {
container.classList.add('dark');
document.body.classList.add('dark-bg');
updateDarkIcon('dark');
}
function updateDarkIcon(theme) {
var icon = document.getElementById('ext-dark-icon');
if (!icon) return;
if (theme === 'dark') {
icon.innerHTML = '<defs><mask id="mk"><rect width="14" height="14" fill="white"/><circle cx="10" cy="5.5" r="4.3" fill="black"/></mask></defs><circle cx="8" cy="7" r="5" fill="currentColor" mask="url(#mk)"/>';
} else {
icon.innerHTML = '<circle cx="7" cy="7" r="2.5" stroke="currentColor" stroke-width="1.2" fill="none"/><path d="M7 1v1.5M7 11.5V13M1 7h1.5M11.5 7H13M2.76 2.76l1.06 1.06M10.18 10.18l1.06 1.06M2.76 11.24l1.06-1.06M10.18 3.82l1.06-1.06" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>';
}
}
document.getElementById('ext-dark-toggle').addEventListener('click', function() {
if (currentTheme === 'light') {
container.classList.add('dark');
document.body.classList.add('dark-bg');
currentTheme = 'dark';
localStorage.setItem('popup_theme', 'dark');
updateDarkIcon('dark');
showToast('已切换为暗色模式');
} else {
container.classList.remove('dark');
document.body.classList.remove('dark-bg');
currentTheme = 'light';
localStorage.setItem('popup_theme', 'light');
updateDarkIcon('light');
showToast('已切换为亮色模式');
}
});
document.getElementById('ext-settings-btn').addEventListener('click', function() {
var isVisible = settingsPanel.style.display === 'flex';
settingsPanel.style.display = isVisible ? 'none' : 'flex';
if (!isVisible) { applySettings(settings); }
});
settingsBackBtn.addEventListener('click', function() {
settingsPanel.style.display = 'none';
});
var importOverlay = document.getElementById('ext-import-overlay');
var importInfo = document.getElementById('ext-import-info');
var importCatList = document.getElementById('ext-import-cat-list');
var importCancelBtn = document.getElementById('ext-import-cancel');
var CAT_DATA_KEY = 'tab_pro_fixed_v3';
var CAT_ORDER_KEY = 'tab_pro_cat_order';
var CAT_NAMES = { video: '视频', code: '代码', social: '社交' };
document.getElementById('ext-import-btn').addEventListener('click', function() {
chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
if (!tabs || tabs.length === 0) { showToast('无法获取当前标签页'); return; }
var tab = tabs[0];
var title = tab.title || '(无标题)';
var url = tab.url || '';
if (!url || url.startsWith('chrome://') || url.startsWith('chrome-extension://') || url.startsWith('about:')) {
showToast('无法导入此页面（系统页面不支持）');
return;
}
var raw = localStorage.getItem(CAT_DATA_KEY);
var data = raw ? JSON.parse(raw) : {};
var catOrder = (function() {
try { return JSON.parse(localStorage.getItem(CAT_ORDER_KEY)); }
catch(e) { return Object.keys(data); }
})() || Object.keys(data);
importInfo.textContent = '\u300C' + title + '\u300D';
importCatList.innerHTML = '';
catOrder.forEach(function(catKey) {
var tiles = data[catKey] || [];
var displayName = CAT_NAMES[catKey] || catKey;
var div = document.createElement('div');
div.className = 'ext-import-cat-item';
div.innerHTML = '<span class="ext-import-cat-icon">&#128279;</span>' +
escapeHtml(displayName) +
'<span class="ext-import-cat-count">' + tiles.length + ' 个磁贴</span>';
div.addEventListener('click', function() {
var exists = tiles.some(function(t) { return t.url === url; });
if (exists) {
showToast('\u300C' + displayName + '\u300D中已存在此网页');
importOverlay.style.display = 'none';
return;
}
if (!data[catKey]) data[catKey] = [];
data[catKey].push({ name: title, url: url });
localStorage.setItem(CAT_DATA_KEY, JSON.stringify(data));
importOverlay.style.display = 'none';
showToast('已导入到 \u300C' + displayName + '\u300D');
});
importCatList.appendChild(div);
});
importOverlay.style.display = 'flex';
});
});
importCancelBtn.addEventListener('click', function() {
importOverlay.style.display = 'none';
});
importOverlay.addEventListener('click', function(e) {
if (e.target === importOverlay) importOverlay.style.display = 'none';
});
var searchEngineBtn = document.getElementById('ext-search-engine-btn');
var searchEngineIcon = document.getElementById('ext-search-engine-icon');
var engineDrop = document.getElementById('ext-engine-drop');
var engineDropInner = document.getElementById('ext-engine-drop-inner');
var SEARCH_ENGINES = {
google: { name: 'Google', url: 'https://www.google.com/search?q=%s', icon: 'https://www.google.com/favicon.ico', group: 'search' },
bing: { name: 'Bing', url: 'https://cn.bing.com/search?q=%s', icon: 'https://cn.bing.com/favicon.ico', group: 'search' },
baidu: { name: 'Baidu', url: 'https://www.baidu.com/s?wd=%s', icon: 'https://www.baidu.com/favicon.ico', group: 'search' },
duckduckgo: { name: 'DuckDuckGo', url: 'https://duckduckgo.com/?q=%s', icon: 'https://duckduckgo.com/favicon.ico', group: 'search' },
brave: { name: 'Brave', url: 'https://search.brave.com/search?q=%s', icon: 'https://search.brave.com/favicon.ico', group: 'search' },
sogou: { name: '搜狗', url: 'https://www.sogou.com/web?query=%s', icon: 'https://www.sogou.com/favicon.ico', group: 'search' },
so360: { name: '360搜索', url: 'https://www.so.com/s?q=%s', icon: 'https://www.so.com/favicon.ico', group: 'search' },
yahoo: { name: 'Yahoo', url: 'https://search.yahoo.com/search?p=%s', icon: 'https://s.yimg.com/rz/l/favicon.ico', group: 'search' },
chatgpt: { name: 'ChatGPT', url: 'https://chatgpt.com/?q=%s', icon: 'https://chatgpt.com/favicon.ico', group: 'ai' },
perplexity: { name: 'Perplexity', url: 'https://www.perplexity.ai/search?q=%s', icon: 'https://www.perplexity.ai/favicon.ico', group: 'ai' },
kimi: { name: 'Kimi', url: 'https://kimi.moonshot.cn/?q=%s', icon: 'https://kimi.moonshot.cn/favicon.ico', group: 'ai' },
doubao: { name: '豆包', url: 'https://www.doubao.com/?q=%s', icon: 'https://www.doubao.com/favicon.ico', group: 'ai' },
metaso: { name: '秘塔AI', url: 'https://metaso.cn/?q=%s', icon: 'https://metaso.cn/favicon.ico', group: 'ai' },
felo: { name: 'Felo', url: 'https://felo.ai/search?q=%s', icon: 'https://felo.ai/favicon.ico', group: 'ai' },
bilibili: { name: '哔哩哔哩', url: 'https://search.bilibili.com/all?keyword=%s', icon: 'https://www.bilibili.com/favicon.ico', group: 'media' },
youtube: { name: 'YouTube', url: 'https://www.youtube.com/results?search_query=%s', icon: 'https://www.youtube.com/favicon.ico', group: 'media' },
douyin: { name: '抖音', url: 'https://www.douyin.com/search/%s', icon: 'https://www.douyin.com/favicon.ico', group: 'media' },
tiktok: { name: 'TikTok', url: 'https://www.tiktok.com/search?q=%s', icon: 'https://www.tiktok.com/favicon.ico', group: 'media' }
};
var ENGINE_GROUPS = [
{ key: 'search', label: '综合搜索' },
{ key: 'ai', label: 'AI 搜索' },
{ key: 'media', label: '媒体流媒体' }
];
var searchCurrentEngine = localStorage.getItem('popup_search_engine') || 'google';
var engineDropdownOpen = false;
function updateSearchEngineIcon() {
var eng = SEARCH_ENGINES[searchCurrentEngine];
if (eng && searchEngineIcon) { searchEngineIcon.src = eng.icon; }
}
function doEngineSearch(query) {
if (!query.trim()) return;
var eng = SEARCH_ENGINES[searchCurrentEngine];
if (!eng) return;
var url = eng.url.replace('%s', encodeURIComponent(query.trim()));
if (typeof chrome !== 'undefined' && chrome.tabs) {
chrome.tabs.create({ url: url });
} else {
window.open(url, '_blank');
}
}
function renderEngineDrop() {
if (!engineDropInner) return;
var customEngines = [];
try { customEngines = JSON.parse(localStorage.getItem('custom_engines') || '[]'); } catch (e) {}
var allEngines = Object.assign({}, SEARCH_ENGINES);
customEngines.forEach(function(ce) {
allEngines[ce.id] = { name: ce.name, url: ce.url, icon: ce.icon || '', group: ce.group || 'custom' };
});
var html = '';
var usedKeys = new Set();
[].concat(ENGINE_GROUPS, [{ key: 'custom', label: '自定义' }]).forEach(function(group) {
var groupBtns = '';
Object.keys(allEngines).forEach(function(k) {
if (group.key === 'custom') {
if (SEARCH_ENGINES[k]) return;
var activeClass = searchCurrentEngine === k ? ' active' : '';
groupBtns += '<button class="ext-eng-btn' + activeClass + '" data-engine="' + k + '"><img src="' + (allEngines[k].icon || '') + '" alt="" onerror="this.style.display=\'none\'"><span>' + allEngines[k].name + '</span></button>';
usedKeys.add(k);
return;
}
if (allEngines[k].group === group.key) {
var activeClass = searchCurrentEngine === k ? ' active' : '';
groupBtns += '<button class="ext-eng-btn' + activeClass + '" data-engine="' + k + '"><img src="' + (allEngines[k].icon || '') + '" alt="" onerror="this.style.display=\'none\'"><span>' + allEngines[k].name + '</span></button>';
usedKeys.add(k);
}
});
if (!groupBtns) return;
html += '<div class="ext-eng-group-label">' + group.label + '</div>' + groupBtns;
});
engineDropInner.innerHTML = html;
engineDropInner.querySelectorAll('.ext-eng-btn').forEach(function(btn) {
btn.addEventListener('click', function(e) {
e.stopPropagation();
var key = btn.dataset.engine;
searchCurrentEngine = key;
localStorage.setItem('popup_search_engine', key);
updateSearchEngineIcon();
closeEngineDrop();
var q = searchInput.value.trim();
if (q) doEngineSearch(q);
});
});
}
function openEngineDrop() {
renderEngineDrop();
engineDrop.style.display = 'block';
engineDropdownOpen = true;
document.addEventListener('click', closeEngineDropOutside);
}
function closeEngineDrop() {
engineDrop.style.display = 'none';
engineDropdownOpen = false;
document.removeEventListener('click', closeEngineDropOutside);
}
function closeEngineDropOutside(e) {
if (!engineDropdownOpen) return;
if (!engineDrop.contains(e.target) && e.target !== searchEngineBtn && !searchEngineBtn.contains(e.target)) {
closeEngineDrop();
}
}
searchEngineBtn.addEventListener('click', function(e) {
e.stopPropagation();
if (engineDropdownOpen) { closeEngineDrop(); return; }
openEngineDrop();
});
function showSearchMode() {
searchEngineBtn.style.display = 'flex';
updateSearchEngineIcon();
}
function hideSearchMode() {
searchEngineBtn.style.display = 'none';
closeEngineDrop();
}
updateSearchEngineIcon();
hideSearchMode();
initPopup();
})();