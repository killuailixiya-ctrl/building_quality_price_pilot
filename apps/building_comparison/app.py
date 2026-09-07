import csv
import itertools
import os
import random
from pathlib import Path

import pandas as pd
import streamlit as st
from trueskill import Rating, rate_1vs1


APP_DIR = Path(__file__).resolve().parent
IMAGE_DIR = APP_DIR / "images"
MANIFEST_CSV = APP_DIR / "images_manifest.csv"
PAIRS_CSV = APP_DIR / "comparison_pairs.csv"
RESULTS_CSV = APP_DIR / "comparison_results.csv"
COUNT_CSV = APP_DIR / "image_comparison_counts.csv"


def load_manifest() -> list[str]:
    df = pd.read_csv(MANIFEST_CSV)
    return df["pic_id"].astype(str).tolist()


def generate_pairs(ids: list[str]) -> None:
    pairs = list(itertools.combinations(ids, 2))
    random.Random(42).shuffle(pairs)
    with open(PAIRS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["left", "right"])
        writer.writerows(pairs)


def ensure_files() -> None:
    if not PAIRS_CSV.exists():
        generate_pairs(load_manifest())
    if not RESULTS_CSV.exists():
        with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["left", "right", "result", "left_mu", "right_mu"])


def read_pairs() -> list[tuple[str, str]]:
    with open(PAIRS_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    return [(r[0], r[1]) for r in rows[1:] if len(r) >= 2]


def remove_pair(left: str, right: str) -> None:
    pairs = read_pairs()
    with open(PAIRS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["left", "right"])
        for a, b in pairs:
            if not (a == left and b == right):
                writer.writerow([a, b])


st.set_page_config(page_title="建筑图片两两对比", page_icon="🏙️", layout="centered")
st.title("建筑图片两两对比")
st.markdown("请根据第一印象选择哪张建筑的视觉品质更好。")

ensure_files()

if "ratings" not in st.session_state:
    st.session_state.ratings = {pic: Rating() for pic in load_manifest()}
if "comparison_count" not in st.session_state:
    st.session_state.comparison_count = 0

pairs = read_pairs()
if not pairs:
    st.success("所有对比已完成！")
    st.stop()

left, right = pairs[0]
col1, col2 = st.columns(2)
with col1:
    st.image(str(IMAGE_DIR / left), use_container_width=True)
    st.button("左侧更好", key="left_btn", type="primary", use_container_width=True)
with col2:
    st.image(str(IMAGE_DIR / right), use_container_width=True)
    st.button("右侧更好", key="right_btn", type="primary", use_container_width=True)

st.button("两者相当", key="equal_btn", use_container_width=True)

if st.session_state.left_btn or st.session_state.right_btn or st.session_state.equal_btn:
    if st.session_state.left_btn:
        result = "left"
    elif st.session_state.right_btn:
        result = "right"
    else:
        result = "equal"

    a = st.session_state.ratings[left]
    b = st.session_state.ratings[right]
    if result == "left":
        new_a, new_b = rate_1vs1(a, b)
    elif result == "right":
        new_b, new_a = rate_1vs1(b, a)
    else:
        new_a, new_b = rate_1vs1(a, b, drawn=True)

    st.session_state.ratings[left] = new_a
    st.session_state.ratings[right] = new_b
    st.session_state.comparison_count += 1

    with open(RESULTS_CSV, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([left, right, result, f"{new_a.mu:.3f}", f"{new_b.mu:.3f}"])
    remove_pair(left, right)
    st.rerun()

st.sidebar.header("管理员")
password = st.sidebar.text_input("下载密码", type="password")
if password == "2023202090005":
    if RESULTS_CSV.exists():
        st.sidebar.download_button("下载对比结果", data=RESULTS_CSV.read_bytes(), file_name="comparison_results.csv", mime="text/csv")
    st.sidebar.write("已完成对比：", st.session_state.comparison_count)
