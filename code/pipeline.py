# -*- coding: utf-8 -*-
"""
企业数字化转型测度：五步流水线主脚本
--------------------------------------------------
Step 1  数据获取：读取年报纯文本（真实场景：巨潮资讯网下载年报并解析PDF）
Step 2  文本预处理：去除HTML标签/特殊字符/停用词，统一全半角
Step 3  中文分词：jieba 精确模式分词，加载自定义数字化词表
Step 4  词典匹配与词频统计：按五维数字化转型词典匹配计数
Step 5  测度计算与面板输出：ln(1+词频) 主测度 + 分类词频占比，输出企业-年份面板

运行：python pipeline.py
输出：output/dt_wordfreq.csv（词频明细）
      output/panel_digital_transformation.csv（企业-年份面板，主交付物）
"""
import os
import re
import glob
import jieba
import pandas as pd

from dictionary import DIGITAL_DICT, DIMENSIONS, STOPWORDS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_DIR = os.path.join(ROOT, "data", "corpus")
OUT_DIR = os.path.join(ROOT, "output")
os.makedirs(OUT_DIR, exist_ok=True)


# ---------------- Step 1 数据获取 ----------------
def step1_load_corpus():
    files = sorted(glob.glob(os.path.join(CORPUS_DIR, "*.txt")))
    if not files:
        raise FileNotFoundError("语料为空，请先运行 simulate_corpus.py")
    records = []
    for fp in files:
        fname = os.path.basename(fp)
        code, year = fname[:-4].rsplit("_", 1)
        with open(fp, "r", encoding="utf-8") as f:
            raw = f.read()
        records.append({"code": code, "year": int(year), "raw_text": raw})
    print(f"[Step1] 读取年报文本 {len(records)} 份")
    return pd.DataFrame(records)


# ---------------- Step 2 文本预处理 ----------------
HTML_RE = re.compile(r"<[^>]+>")
SPECIAL_RE = re.compile(r"[^\u4e00-\u9fa5A-Za-z0-9，。；：、（）]")

def clean_text(text: str) -> str:
    text = HTML_RE.sub("", text)          # 去 HTML 标签
    text = text.replace("（", "(").replace("）", ")")
    text = SPECIAL_RE.sub("", text)       # 去特殊字符与空白
    return text

def remove_stopwords(tokens):
    return [t for t in tokens if t not in STOPWORDS and len(t.strip()) > 0]

def step2_preprocess(df):
    df["clean_text"] = df["raw_text"].map(clean_text)
    print(f"[Step2] 预处理完成，平均字符数 {df['clean_text'].str.len().mean():.0f}")
    return df


# ---------------- Step 3 中文分词 ----------------
def step3_tokenize(df):
    # 将词典中的多字词加入 jieba 自定义词表，保证整词匹配
    for words in DIGITAL_DICT.values():
        for w in words:
            jieba.add_word(w, freq=1000000)
    df["tokens"] = df["clean_text"].map(lambda s: remove_stopwords(jieba.lcut(s)))
    print(f"[Step3] 分词完成，平均词数 {df['tokens'].map(len).mean():.0f}")
    return df


# ---------------- Step 4 词典匹配与词频统计 ----------------
def step4_match(df):
    for dim, words in DIGITAL_DICT.items():
        wset = set(words)
        df[f"freq_{dim}"] = df["tokens"].map(lambda ts, s=wset: sum(1 for t in ts if t in s))
    df["freq_total"] = sum(df[f"freq_{d}"] for d in DIMENSIONS)
    print("[Step4] 词典匹配完成")
    return df


# ---------------- Step 5 测度计算与面板输出 ----------------
def step5_measure(df):
    for dim in DIMENSIONS:
        df[f"ratio_{dim}"] = df[f"freq_{dim}"] / df["freq_total"].replace(0, pd.NA)
    # 主测度：总词频加 1 取自然对数（吴非等，2021）
    df["DT"] = (1 + df["freq_total"]).map(lambda x: __import__("math").log(x))
    df["DT_kw"] = df["freq_total"]  # 关键词计数口径（稳健性）
    panel = df[["code", "year", "DT", "DT_kw", "freq_total"] +
               [f"freq_{d}" for d in DIMENSIONS] +
               [f"ratio_{d}" for d in DIMENSIONS]].copy()
    wordfreq = df[["code", "year", "DT", "DT_kw"] +
                  [f"freq_{d}" for d in DIMENSIONS]]
    panel.to_csv(os.path.join(OUT_DIR, "panel_digital_transformation.csv"),
                 index=False, encoding="utf-8-sig")
    wordfreq.to_csv(os.path.join(OUT_DIR, "dt_wordfreq.csv"),
                    index=False, encoding="utf-8-sig")
    print(f"[Step5] 面板数据 {panel.shape[0]} 行已输出")
    print(panel.groupby("year")["DT"].agg(["mean", "std", "max"]).round(3))
    return panel


if __name__ == "__main__":
    data = step1_load_corpus()
    data = step2_preprocess(data)
    data = step3_tokenize(data)
    data = step4_match(data)
    step5_measure(data)
