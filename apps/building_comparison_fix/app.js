const ADMIN_PASSWORD = "20021217";
const STORAGE_KEY = "fix_results_v1";
let annotatorId = localStorage.getItem("fix_annotator_id") || "";
let pairs = [];
let pairIndex = 0;
let currentPair = null;

const idPanel = document.getElementById("idPanel");
const comparePanel = document.getElementById("comparePanel");
const adminPanel = document.getElementById("adminPanel");
const annotatorInput = document.getElementById("annotatorId");
const annotatorLabel = document.getElementById("annotatorLabel");
const progressText = document.getElementById("progressText");
if (annotatorId) annotatorInput.value = annotatorId;

function getResults() {
  return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
}

async function startCompare() {
  annotatorId = annotatorInput.value.trim();
  if (!annotatorId) { alert("请输入标注者 ID"); return; }
  localStorage.setItem("fix_annotator_id", annotatorId);
  annotatorLabel.textContent = `当前标注者：${annotatorId}`;
  const res = await fetch("fix_pairs.json");
  pairs = await res.json();
  const done = new Set(getResults().filter(r => r.annotator_id === annotatorId).map(r => `${r.left_id}|${r.right_id}`));
  const remaining = pairs.filter(([a,b]) => !done.has(`${a}|${b}`));
  if (remaining.length === 0) { alert("你已完成全部修复对比"); return; }
  pairs = remaining;
  pairIndex = 0;
  idPanel.classList.add("hidden");
  comparePanel.classList.remove("hidden");
  showPair();
}

function showPair() {
  if (pairIndex >= pairs.length) { progressText.textContent = "全部完成！"; return; }
  currentPair = pairs[pairIndex];
  document.getElementById("leftImg").src = `images/${currentPair[0]}`;
  document.getElementById("rightImg").src = `images/${currentPair[1]}`;
  progressText.textContent = `本次已完成 ${pairIndex} / ${pairs.length}；左图 ${currentPair[0]}，右图 ${currentPair[1]}`;
}

function submit(result) {
  if (!currentPair) return;
  const rows = getResults();
  rows.push({ annotator_id: annotatorId, left_id: currentPair[0], right_id: currentPair[1], result });
  localStorage.setItem(STORAGE_KEY, JSON.stringify(rows));
  pairIndex += 1;
  showPair();
}

document.getElementById("startBtn").addEventListener("click", startCompare);
document.getElementById("leftCard").addEventListener("click", () => submit("left"));
document.getElementById("rightCard").addEventListener("click", () => submit("right"));
document.getElementById("equalBtn").addEventListener("click", () => submit("equal"));

document.getElementById("adminBtn").addEventListener("click", () => adminPanel.classList.toggle("hidden"));
document.getElementById("adminLoginBtn").addEventListener("click", () => {
  if (document.getElementById("adminPassword").value !== ADMIN_PASSWORD) { alert("密码错误"); return; }
  const rows = getResults();
  document.getElementById("adminContent").classList.remove("hidden");
  document.getElementById("adminStats").textContent = `总修复对比数：${rows.length}`;
  document.getElementById("downloadBtn").onclick = () => {
    const csv = ["annotator_id,left_id,right_id,result"].concat(rows.map(r => `${r.annotator_id},${r.left_id},${r.right_id},${r.result}`)).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "fix_comparison_results.csv"; a.click();
  };
});
document.getElementById("closeAdminBtn").addEventListener("click", () => {
  document.getElementById("adminContent").classList.add("hidden");
  adminPanel.classList.add("hidden");
});
