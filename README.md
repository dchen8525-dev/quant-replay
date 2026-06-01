# QuantReplay

QuantReplay 是一个本地 A 股模拟交易复盘和量化学习工具。它用于记录手工模拟买入交易，缓存日线行情，复盘后续走势，运行入门级策略回测，跟踪模拟账户，评估自选股强度，比较指数基准，并输出收益、盈亏、回撤、浮盈浮亏、止损模拟和复盘统计。

本项目不是实盘交易系统，不连接券商接口，也不会执行真实交易。

## 快速开始

安装依赖：

```bash
pip install -r requirements.txt
```

启动应用：

```bash
streamlit run app.py
```

SQLite 数据库会自动创建在 `data/quant_replay.db`。当前本地版本号见 `VERSION`。

运行测试：

```bash
pytest
python -m ruff check .
python -m compileall app.py src tests
```

## 样例数据

`sample_data/` 目录提供用于导入流程测试和本地演示的 CSV 文件：

- `watchlist_sample.csv`
- `trades_sample.csv`

这些样例数据不是投资建议。

## 目录结构

```text
app.py
  -> src/pages/*              Streamlit 页面
  -> src/data_fetcher.py      带缓存的数据源调度
  -> src/providers/*          腾讯、东方财富、指数、Mock 数据源
  -> src/database.py          SQLite 持久化、标签、日志和行情缓存
  -> src/backtest/*           入门策略回测
  -> src/account/*            模拟账户流水和指标
  -> src/strength.py          自选股和分类强度排名
  -> src/review.py            确定性交易复盘报告
  -> src/factors/*            因子库、排名、IC、分位收益评估
  -> src/portfolio/*          组合构建、暴露、再平衡和风险指标
  -> src/strategy_lab/*       策略注册、参数网格、walk-forward、实验历史
  -> src/research/*           Markdown/HTML/CSV 报告、快照、可复现元数据
  -> src/data_quality/*       数据健康、修复、数据源对比、交易日观测
  -> src/regime/*             市场状态和行业轮动分析
  -> src/release.py           发布就绪检查
  -> src/analyzer.py          盈亏、回撤、止损、基准、标签统计
  -> src/charts.py            Plotly 图表
```

## 数据源

应用使用统一的数据源抽象：

- `AkshareTencentProvider`
- `AkshareEastmoneyProvider`
- `AkshareIndexTencentProvider`
- `MockProvider`

腾讯数据源优先使用。东方财富作为备用数据源保留，失败会被捕获并记录，不会导致应用崩溃。数据获取流程会先检查本地 SQLite 缓存，只拉取缺失的左右区间，然后写入缓存并去重。

## 主要功能

- 新建模拟买入交易。
- 策略回测：均线交叉、突破、均值回归。
- 模拟账户：现金、持仓、已实现和未实现盈亏。
- 自选股强度排名和分类强度分析。
- 按标签、分类、信心分组的复盘报告。
- 因子研究：简单技术因子、未来收益评估、rank IC、分位收益。
- 组合实验：等权、分数加权、风险调整、暴露限制、再平衡模拟。
- 策略实验室：策略注册、参数网格、walk-forward、实验历史。
- 研究报告：Markdown/HTML/CSV 导出、研究快照和快照对比。
- 数据健康：缓存健康、数据源对比、Baostock/Tushare 可选接入。
- 市场状态：指数趋势、波动、风险偏好标签和行业轮动分析。
- 历史日线行情获取和 SQLite 缓存。
- 交易分析：最终收益、盈亏、最大浮盈浮亏、最大回撤、持有天数。
- 止损模拟：3%、5%、8%、10%。
- 指数基准比较和超额收益。
- 交易标签和标签级统计。
- 交易历史、仪表盘、自选股管理。
- CSV 导入导出和数据库备份。
- 数据源诊断、缓存状态、发布就绪检查。

## 基准比较

交易分析支持以下指数基准：

- 沪深300
- 中证500
- 上证指数
- 深证成指
- 创业板指

基准数据使用 `sh000300` 这类指数代码存储在同一张 `daily_prices` 表中。应用会展示个股收益、基准收益、超额收益和是否跑赢基准。

## 标签和复盘统计

交易可以添加常用形态标签，例如 `放量突破`、`低吸`、`趋势跟随`，也支持自定义逗号分隔标签。Dashboard 会按标签聚合表现，帮助识别哪些交易模式更有效。

## 导入导出

应用支持本地备份工作流：

- 导出交易 CSV。
- 导入模拟交易 CSV。
- 导出自选股 CSV。
- 导入自选股 CSV。
- 导出行情缓存 CSV。
- 导出完整 SQLite 数据库备份。

## 回测

Strategy Backtest 页面使用日线收盘价生成信号，并在下一个可用交易日开盘价执行交易，避免同一天收盘价同时用于信号和成交。当前版本为多头、单仓位、全仓模型，包含佣金和滑点。

支持的入门策略：

- Moving Average Cross
- Breakout
- Mean Reversion

## 模拟账户

Simulated Account 页面把多笔 BUY/SELL 交易作为同一个模拟账户管理，展示现金余额、当前持仓、账户权益、已实现盈亏和未实现盈亏。它不连接券商 API。

## 强度排名

Strength Ranking 页面会计算自选股近期收益、波动率、距高点距离、均线趋势状态，并生成透明的 0-100 分强度分数。Dashboard 也会按自选股分类展示分类强度。

## 因子研究

Factor Research 页面评估自选股的简单技术因子：

- `momentum_5d`
- `momentum_20d`
- `momentum_60d`
- `volatility_20d`
- `volume_ratio_5d`
- `ma_distance_20d`
- `drawdown_from_60d_high`
- `turnover_proxy`

页面会输出因子排名、未来 5 日和 20 日收益、rank IC、分位胜率和分位平均收益。它使用同一套本地缓存和数据源抽象，不依赖财务报表数据。

## 组合实验

Portfolio Lab 页面支持基于自选股构建简单组合：

- 等权重。
- 分数加权。
- 风险调整加权。

它支持单票上限、分类暴露上限、现金保留、每周/每月/每季度再平衡、基准比较、换手率、波动率、最大回撤、类 Sharpe 指标、分类暴露和单票暴露。

## 策略实验室

Strategy Lab 页面支持入门策略实验：

- MA Cross
- Breakout
- Mean Reversion
- Strength Rotation
- Factor Ranking

它会运行参数网格、训练/测试 walk-forward 检查，保存实验历史，并对参数过多、交易太少、小样本超高收益、缺少测试期等情况给出过拟合警告。

## 研究报告

Research Reports 页面可以生成交易复盘、策略回测、因子研究、组合复盘和月度学习总结等本地研究产物。报告支持导出为 Markdown、HTML 或 CSV。研究快照会存入 SQLite，并带稳定哈希，方便后续对比。

## 数据健康

Data Health 页面用于对比数据源、检查缓存覆盖，并报告重复日期、缺失收盘价、零价或负价、日期非递增、空区间等异常。腾讯、东方财富、Mock 和可选 Baostock 数据源可以用于对比。Tushare 是可选功能，仅在配置 `TUSHARE_TOKEN` 后启用。

## 市场状态

Market Regime 页面基于 MA20/MA60、60 日高点回撤和 20 日波动率分位数，把选定指数分类为 bull trend、bear trend、sideways、high/low volatility、risk-on/risk-off 等状态。它也会按近期收益和 MA20 趋势持续性排名自选股分类，标出强势、转弱和改善的分类。

## 截图

截图占位和截图建议见 `docs/screenshots/README.md`。

## 发布

发布记录见 `CHANGELOG.md`，stable release 检查清单见 `docs/RELEASE_CHECKLIST.md`。Data Diagnostics 页面包含 Release Readiness 表，用于检查发布文件、样例数据、数据库忽略规则、README 状态和明显的已提交密钥。

## 限制

- 当前版本是本地优先、单用户工具。
- 不支持真实交易、券商登录、下单执行、tick 数据、Level2 数据、高频交易或机器学习预测。

## 路线图

```text
PHASE_1 ✅ COMPLETED
PHASE_2 ✅ COMPLETED
PHASE_3 ✅ COMPLETED
PHASE_4 ✅ COMPLETED
PHASE_5 ✅ COMPLETED
PHASE_6 ✅ COMPLETED
PHASE_7 ✅ COMPLETED
PHASE_8 ✅ COMPLETED
PHASE_9 ✅ COMPLETED
PHASE_10 ✅ COMPLETED
```

下一阶段：无。稳定发布准备已经完成。
