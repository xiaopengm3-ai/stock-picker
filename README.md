A股智能选股系统 V2.0
机构级量化研究框架 — 个人投资者使用

全市场 4000+ 只 A 股中，通过 基本面 × 技术面 × 资金面 × 行业面 × 消息面 × 催化剂 × 市场环境 七维复合评分，每日精选 1–2 只 最优质标的。

核心特性
41 个因子：估值/成长/质量/预期 + 趋势/动量/量价/形态/多周期 + 北向/主力/筹码 + 行业景气 + 资讯情绪 + 催化剂
量化严谨：防未来函数、幸存者偏差处理、行业中性化、市值中性化、MAD 去极值、ZScore 标准化
AI 增强：OpenAI/Claude/Gemini/DeepSeek/Local 多模型可插拔，新闻情绪分析、催化剂识别、投资逻辑生成
市场自适应：四大指数牛熊判断，因子权重动态调节
完整闭环：选股 → 持有 → 卖出（时间/技术/基本面止盈止损 + 分级减仓）
YAML 配置驱动：改权重/阈值不改代码
内置回测：逐日循环 + T+1 成交模拟 + 绩效指标 + 网格搜索优化
因子评价：IC/ICIR 分析 + 分层回测 + 贡献率 + 自动降权淘汰
快速开始
# 安装依赖
pip install -r requirements.txt

# 运行选股（默认 Top 2）
python main.py

# 详细输出
python main.py --verbose --top 5

# 指定历史日期
python main.py --date 2026-01-15

# 回测
python main.py --backtest --start 2024-01-01 --end 2025-12-31

# 权重优化
python main.py --optimize

# AI 分析（需要 API key）
python main.py --ai openai
打包为独立 EXE
pip install pyinstaller
pyinstaller --onefile --name StockPicker --add-data "config.yaml;." main.py
# exe 在 dist/StockPicker.exe
把 config.yaml 放在 exe 同目录，双击运行。

配置
所有参数在 config.yaml 中修改：

weights:
  fundamental: 0.35    # 基本面权重
  technical: 0.25      # 技术面权重
  capital_flow: 0.10   # 资金行为权重
  industry: 0.10       # 行业景气权重
  news: 0.10           # 消息面权重
  catalyst: 0.05       # 催化剂权重
  market_regime: 0.05  # 市场环境权重

screening:
  top_n: 2             # 每日输出数量
  min_score: 60        # 最低分数阈值

ai:
  provider: "none"     # openai/claude/gemini/deepseek/local/none
  model: "gpt-4o-mini"
输出示例
══════════════════════════════════════════════════════════════
  A股智能选股系统 V2.0  选股日期: 2026-06-02
══════════════════════════════════════════════════════════════

  ── 市场环境 ───────────────────────────────────────
  温度: 58/100  震荡偏多  建议仓位: 60%
  上证指数: 3245.18 多头  沪深300: 3891.42 多头

╔══════════════════════════════════════════════════════════╗
║  🏆 #1  贵州茅台 (600519)
║      推荐等级: S  ⭐⭐⭐⭐⭐  周期: 中线
║      最终得分: 87.3 / 100
║      行业: 食品饮料
╠══════════════════════════════════════════════════════════╣
║  评分明细:
║    基本面: 52.2    技术面: 22.1    资金面: 8.5
║    行业面: 7.2     消息面: 7.8     催化剂: 4.3
║    市场环境: 4.1
╠──────────────────────────────────────────────────────╣
║  投资逻辑 (AI): 贵州茅台作为高端白酒龙头，当前PE处于...
║  风险提示: ⚡ 白酒消费税改革 ⚡ 消费复苏不及预期
╚══════════════════════════════════════════════════════════╝
架构
stock-picker/
├── main.py              CLI 入口，8 步流水线
├── config.yaml          全局 YAML 配置
│
├── data/                数据采集与治理 (akshare + 缓存 + 质量检查)
├── preprocessing/       因子预处理 (MAD/ZScore/行业市值中性化/防未来函数)
│
├── factors/             因子引擎 (41 因子 F01–F41)
│   ├── fundamental/     基本面：估值 + 成长 + 质量 + 预期
│   ├── technical/       技术面：趋势 + 动量 + 量价 + 形态 + 多周期
│   ├── capital/         资金面：北向 + 主力 + 筹码
│   ├── industry/        行业面：景气度 + 相对强度
│   ├── news/            消息面：资讯情绪 + 社区情绪
│   └── catalyst/        催化剂：预增/回购/增持/并购/政策
│
├── ai/                  大模型 AI 分析层 (5 模型可插拔)
├── environment/         市场状态识别 (四大指数牛熊 + 权重自适应)
├── exit/                卖出逻辑 (时间/技术/基本面/分级止盈止损)
├── risk/                风险控制 (硬过滤/流动性/行业集中度/黑名单)
├── eval/                因子评价 (IC/ICIR/分层回测/贡献率/自动降权)
├── backtest/            回测引擎 (逐日循环/T+1 模拟/绩效/优化)
├── scoring/             评分融合 (7 维加权 100%)
└── output/              CLI 输出 (打分卡 + AI 投资逻辑)
技术栈
类别	选型
语言	Python 3.10+
数据	akshare + 东方财富爬虫
处理	pandas, numpy, scikit-learn
缓存	pyarrow (Parquet)
AI	openai, anthropic, ollama
测试	pytest (14 tests)
打包	PyInstaller
开发计划
Phase	内容	状态
Phase 1	基础设施 + 因子引擎 (F01–F38)	✅
Phase 2	AI + 消息 + 催化剂 + 市场环境 + 卖出	✅
Phase 3	回测 + 因子评价 + 风控 + 优化	✅
免责声明
本系统仅提供研究参考，不构成投资建议。股市有风险，投资需谨慎。

License
MIT
