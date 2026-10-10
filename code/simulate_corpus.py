# -*- coding: utf-8 -*-
"""
模拟语料生成脚本（用于论文可复现演示）
--------------------------------------------------
真实研究场景中，年报全文应从巨潮资讯网（www.cninfo.com.cn）下载，
经 PDF 解析（pdfplumber）得到纯文本。本脚本以可控方式生成"模拟年报文本"，
用于在不依赖外部数据的条件下完整复现五步测度流水线与后续统计分析。

生成逻辑：
  1. 模拟 60 家 A 股上市公司、2019—2023 共 5 年的年报"经营讨论与分析"章节；
  2. 每家公司赋予潜在"数字化转型强度" latent，且强度随时间缓慢上升；
  3. 文本由通用模板句 + 数字化语句按强度抽样拼装而成，数字化语句密度
     与 latent 正相关，从而保证后续测度与回归结果具有真实研究中的统计结构。
"""
import os
import random
import pandas as pd

random.seed(42)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_DIR = os.path.join(ROOT, "data", "corpus")

INDUSTRIES = ["制造业", "信息技术业", "批发零售业", "金融业", "房地产业", "电力热力业"]

# 通用（非数字化）语句库
GENERIC_SENTS = [
    "报告期内，公司坚持稳健经营，主营业务收入保持平稳增长。",
    "公司持续优化产品结构，提升产品质量与服务水平。",
    "报告期内，公司加强内部管理，控制成本费用，经营效率有所提升。",
    "公司积极拓展市场渠道，客户结构进一步改善。",
    "面对复杂的外部环境，公司及时调整经营策略，化解各类经营风险。",
    "公司重视人才队伍建设，员工培训体系不断完善。",
    "报告期内，公司加大市场开拓力度，区域布局更加合理。",
    "公司严格执行质量管理体系，产品合格率保持在较高水平。",
    "公司深化供应链协同，与上游供应商建立长期稳定合作关系。",
    "报告期内，公司治理结构规范运作，信息披露真实、准确、完整。",
    "公司稳步推进产能建设，在建工程按计划投入。",
    "公司坚持现金分红政策，积极回报全体股东。",
    "报告期内，公司主营业务未发生重大变化，经营模式保持稳定。",
    "公司加强预算管理与资金统筹，财务结构保持稳健。",
    "公司积极履行社会责任，推进绿色生产与节能减排。",
]

# 数字化语句库（按五大维度）
DIGITAL_SENTS = {
    "人工智能": [
        "公司引入机器学习算法优化生产排程，人工智能应用场景不断丰富。",
        "报告期内，公司上线智能客服系统，运用自然语言处理技术提升响应效率。",
        "公司建设计算机视觉质检平台，深度学习模型识别准确率持续提升。",
        "公司探索生成式人工智能在研发设计中的应用，构建行业大模型。",
    ],
    "区块链": [
        "公司搭建区块链溯源平台，利用分布式账本技术保障供应链透明。",
        "报告期内，公司试点智能合约结算，探索区块链技术在供应链金融中的落地。",
    ],
    "云计算": [
        "公司将核心业务系统迁移至云平台，采用混合云架构降低运维成本。",
        "报告期内，公司依托云计算与边缘计算，实现设备数据的实时采集与分析。",
        "公司构建私有云数据中心，容器技术支撑业务系统弹性扩容。",
    ],
    "大数据": [
        "公司建设数据中台，推进数据治理与数据资产化管理。",
        "报告期内，公司运用大数据与文本挖掘技术洞察客户需求，精准营销初见成效。",
        "公司整合异构数据源，构建企业级数据仓库，数据挖掘能力显著增强。",
    ],
    "数字技术应用": [
        "公司深入推进数字化转型，实施智能制造升级改造项目。",
        "报告期内，公司依托工业互联网平台实现车间设备互联互通。",
        "公司发展电子商务与线上平台，移动支付覆盖率进一步提升。",
        "公司启动数字孪生工厂建设，数字化经营管理水平持续提高。",
        "公司加强企业资源计划（ERP）与信息系统建设，推动产业数字化。",
    ],
}

FIRM_CODES = [f"SZ{300000 + i * 137:06d}" if i % 3 == 0 else f"SH{600000 + i * 151:06d}"
              for i in range(60)]


def make_corpus():
    if not os.path.exists(CORPUS_DIR):
        os.makedirs(CORPUS_DIR)
    rows = []
    for i, code in enumerate(FIRM_CODES):
        # 企业潜在数字化强度：与研发强度、企业规模正相关（符合理论预期）
        industry = INDUSTRIES[i % len(INDUSTRIES)]
        size = random.uniform(21.5, 26.5)          # ln(总资产)
        lev = random.uniform(0.15, 0.70)           # 资产负债率
        roa = random.uniform(-0.05, 0.12)          # 总资产收益率
        rd = random.uniform(0.005, 0.12)           # 研发强度
        base = min(max(3.2 * rd + 0.10 * (size - 21.5) +
                       random.uniform(-0.12, 0.12), 0.02), 0.9)
        for t, year in enumerate(range(2019, 2024)):
            latent = min(base + 0.05 * t + random.uniform(-0.03, 0.03), 0.98)
            n_sent = 60
            n_digital = int(n_sent * latent)
            sents = random.choices(GENERIC_SENTS, k=n_sent - n_digital) + \
                random.choices(sum(DIGITAL_SENTS.values(), []), k=n_digital)
            random.shuffle(sents)
            text = "。".join(sents) + "。"
            fname = f"{code}_{year}.txt"
            with open(os.path.join(CORPUS_DIR, fname), "w", encoding="utf-8") as f:
                f.write(text)
            rows.append({
                "code": code, "year": year, "industry": industry,
                "size": round(size + 0.06 * t, 3), "lev": round(lev + random.uniform(-0.02, 0.02), 3),
                "roa": round(roa + random.uniform(-0.01, 0.01), 3),
                "rd": round(rd + 0.003 * t, 4),
            })
    cov = pd.DataFrame(rows)
    cov_path = os.path.join(ROOT, "data", "firm_covariates.csv")
    cov.to_csv(cov_path, index=False, encoding="utf-8-sig")
    print(f"已生成 {cov.shape[0]} 份模拟年报文本至 {CORPUS_DIR}")
    print(f"企业协变量文件：{cov_path}")


if __name__ == "__main__":
    make_corpus()
