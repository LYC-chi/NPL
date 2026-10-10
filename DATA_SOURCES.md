# 数据来源说明

> 按作业要求：一句话说明每个文件的来源与处理步骤。

| 文件 | 来源与处理步骤 |
|---|---|
| `data/corpus/*.txt` | 由 `code/simulate_corpus.py` 程序生成的模拟年报"经营讨论与分析"章节文本（每文件对应一家公司某一年份；真实研究应替换为巨潮资讯网 www.cninfo.com.cn 下载的年报PDF并经 pdfplumber 解析为纯文本）。因体积原因语料不入库，运行脚本即可再生。 |
| `data/firm_covariates.csv` | 由 `code/simulate_corpus.py` 同步生成的企业—年份财务协变量（企业规模、资产负债率、ROA、研发强度、所属行业），数值在合理取值范围内模拟，并与语料数字化密度内置关联。 |
| `output/panel_digital_transformation.csv` | 由 `code/pipeline.py` 第五步输出：对语料经清洗→jieba分词→五维词典匹配后，按 DT=ln(1+总词频) 计算的企业—年份主面板（300观测，14字段）。 |
| `output/dt_wordfreq.csv` | 由 `code/pipeline.py` 第四步输出的五维数字化关键词词频明细（人工智能/区块链/云计算/大数据/数字技术应用）。 |
| `output/desc_stats_by_year.csv` | 由 `code/analysis.py` 对主面板分组汇总得到的分年度描述统计。 |
| `output/desc_stats_by_industry.csv` | 由 `code/analysis.py` 对主面板分组汇总得到的分行业描述统计。 |
| `output/reliability_validity.csv` | 由 `code/analysis.py` 计算的信度（Cronbach's α、折半信度）与效度（同时效度、已知组差异）指标。 |
| `output/regression_results.csv` | 由 `code/analysis.py` 以OLS估计的回归结果（因变量DT，含年份与行业固定效应）。 |
| `docs/thesis.md` | 论文全文Markdown版，作者撰写。 |
| `docs/毕业论文_*.docx` | 论文Word版（含封面、目录、正文、参考文献），由论文排版流水线从 thesis.md 生成。 |
| `code/dictionary.py` | 数字化转型五维关键词词典（79词），参考吴非等（2021，《管理世界》）词表并扩充新词。 |

**透明性声明**：本文为预演毕业论文模拟稿，语料为程序生成的模拟数据（生成逻辑见 `simulate_corpus.py`），仅用于完整演示"NLP测度构建五步流水线"方法与统计检验流程；全部经验数字仅具有方法演示意义，不构成对真实经济关系的推断。将 `data/corpus/` 替换为真实年报语料后，`pipeline.py` 与 `analysis.py` 无需修改即可复现全部分析。
