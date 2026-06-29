chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
if (changeInfo.status === 'complete' && tab.url && tab.url.startsWith('chrome-extension://')) {
chrome.scripting.executeScript({
target: { tabId: tabId },
func: () => {
try {
const settings = JSON.parse(localStorage.getItem('tab_pro_settings_v430') || '{}');
if (settings.autoFocusSearch === false) return;
} catch(e) {  }
const tryFocus = () => {
const el = document.getElementById('searchInput');
if (el && document.activeElement !== el) {
el.focus();
return true;
}
return false;
};
tryFocus();
[100, 500, 2000, 5000].forEach(ms => {
setTimeout(tryFocus, ms);
});
}
}).catch(() => {}); // 静默失败
}
});
chrome.commands.onCommand.addListener((command) => {
if (command === "open-popup") {
chrome.windows.create({
url: 'popup.html',
type: 'popup',
width: 400,
height: 580
});
}
});
chrome.runtime.onInstalled.addListener(() => {
chrome.declarativeNetRequest.updateDynamicRules({
removeRuleIds: [1], // 清除可能存在的旧规则
addRules: [
{
id: 1,
priority: 1,
action: {
type: "modifyHeaders",
responseHeaders: [
{ header: "X-Frame-Options", operation: "remove" },
{ header: "Content-Security-Policy", operation: "remove" }
]
},
condition: {
resourceTypes: ["sub_frame"] // 仅当请求是 iframe 缩略图时才剥离拦截头
}
}
]
});
});
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
if (request.action === "stock_fetch") {
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), request.timeout || 10000);
fetch(request.url, {
method: "GET",
signal: controller.signal
})
.then(res => res.arrayBuffer())
.then(buffer => {
clearTimeout(timeoutId);
const encoding = request.encoding || "utf-8";
const text = new TextDecoder(encoding).decode(buffer);
sendResponse({ ok: true, text });
})
.catch(err => {
clearTimeout(timeoutId);
sendResponse({ ok: false, error: err.message || String(err) });
});
return true;
}
if (request.action === "check_url") {
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 10000); // 10秒超时熔断
fetch(request.url, {
method: "GET", // GET 请求能最好地模拟真实访问
signal: controller.signal
})
.then(res => {
clearTimeout(timeoutId);
sendResponse({
status: (res.ok || (res.status >= 200 && res.status < 400)) ? 'up' : 'down',
status_code: res.status
});
})
.catch(err => {
clearTimeout(timeoutId);
if (err.name === 'AbortError') sendResponse({ status: 'timeout' });
else sendResponse({ status: 'error', error: err.message });
});
return true; // 告知 Chrome 我们会异步返回结果
}
});