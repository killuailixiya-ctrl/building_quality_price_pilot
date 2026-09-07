import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const { SUPABASE_URL, SUPABASE_ANON_KEY, ADMIN_PASSWORD } = window.APP_CONFIG;
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const idPanel = document.getElementById("idPanel");
const comparePanel = document.getElementById("comparePanel");
const adminPanel = document.getElementById("adminPanel");
const annotatorInput = document.getElementById("annotatorId");
const annotatorLabel = document.getElementById("annotatorLabel");
const startBtn = document.getElementById("startBtn");
const leftCard = document.getElementById("leftCard");
const rightCard = document.getElementById("rightCard");
const equalBtn = document.getElementById("equalBtn");
const progressText = document.getElementById("progressText");

let annotatorId = localStorage.getItem("building_annotator_id") || "";
let images = [];
let results = [];
let currentPair = null;
let pairIndex = 0;

if (annotatorId) {
  annotatorInput.value = annotatorId;
  annotatorLabel.textContent = `当前标注者：${annotatorId}`;
}

async function loadImages() {
  const { data, error } = await supabase.from("images").select("id, pic_id, url");
  if (error) throw error;
  return data;
}

async function loadMyResults(id) {
  const { data, error } = await supabase
    .from("comparison_results")
    .select("left_id, right_id")
    .eq("annotator_id", id);
  if (error) throw error;
  return data || [];
}

function buildPairs(list) {
  const pairs = [];
  for (let i = 0; i < list.length; i++) {
    for (let j = i + 1; j < list.length; j++) {
      pairs.push([list[i], list[j]]);
    }
  }
  return pairs.sort(() => Math.random() - 0.5);
}

async function startCompare() {
  annotatorId = annotatorInput.value.trim();
  if (!annotatorId) {
    alert("请输入标注者 ID");
    return;
  }
  localStorage.setItem("building_annotator_id", annotatorId);
  annotatorLabel.textContent = `当前标注者：${annotatorId}`;
  images = await loadImages();
  results = await loadMyResults(annotatorId);
  const judged = new Set(results.map((r) => `${r.left_id}-${r.right_id}`));
  const pairs = buildPairs(images).filter(([a, b]) => !judged.has(`${a.id}-${b.id}`));
  if (pairs.length === 0) {
    alert("你已经完成全部对比");
    return;
  }
  window.pendingPairs = pairs;
  pairIndex = 0;
  idPanel.classList.add("hidden");
  comparePanel.classList.remove("hidden");
  showPair();
}

function showPair() {
  const pairs = window.pendingPairs;
  if (pairIndex >= pairs.length) {
    progressText.textContent = "全部完成！";
    return;
  }
  currentPair = pairs[pairIndex];
  document.getElementById("leftImg").src = currentPair[0].url;
  document.getElementById("rightImg").src = currentPair[1].url;
  progressText.textContent = `本次会话已完成 ${pairIndex} / ${pairs.length}`;
}

async function submit(result) {
  if (!currentPair) return;
  const [left, right] = currentPair;
  const { error } = await supabase.from("comparison_results").insert({
    annotator_id: annotatorId,
    left_id: left.id,
    right_id: right.id,
    result,
  });
  if (error) {
    alert("保存失败：" + error.message);
    return;
  }
  pairIndex += 1;
  showPair();
}

startBtn.addEventListener("click", startCompare);
leftCard.addEventListener("click", () => submit("left"));
rightCard.addEventListener("click", () => submit("right"));
equalBtn.addEventListener("click", () => submit("equal"));

document.getElementById("adminBtn").addEventListener("click", () => {
  adminPanel.classList.toggle("hidden");
});

document.getElementById("adminLoginBtn").addEventListener("click", async () => {
  const password = document.getElementById("adminPassword").value;
  if (password !== ADMIN_PASSWORD) {
    alert("密码错误");
    return;
  }
  const { data, error } = await supabase.from("comparison_results").select("*");
  if (error) {
    alert(error.message);
    return;
  }
  document.getElementById("adminContent").classList.remove("hidden");
  document.getElementById("adminStats").textContent = `总对比数：${data.length}`;
  document.getElementById("downloadBtn").onclick = () => {
    const csv = ["annotator_id,left_id,right_id,result,created_at"]
      .concat(data.map((r) => `${r.annotator_id},${r.left_id},${r.right_id},${r.result},${r.created_at}`))
      .join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "comparison_results.csv";
    a.click();
  };
});

document.getElementById("closeAdminBtn").addEventListener("click", () => {
  document.getElementById("adminContent").classList.add("hidden");
  adminPanel.classList.add("hidden");
});
