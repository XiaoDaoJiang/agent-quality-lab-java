# 首版规则清单

| ID | 意图 | 责任实现 | 严重性与例外 |
| --- | --- | --- | --- |
| FMT-001 | 统一可重现的源码排版 | Spotless + 固定 Eclipse JDT + XML | error，不豁免 |
| SRC-001 | 显式导入、禁止星号和无用 import | Checkstyle | error，不豁免 |
| SRC-002 | 控制语句必须有括号 | NeedBraces | error，不豁免 |
| SRC-003 | 不吞异常；写个注释也不能自动放行空 catch | EmptyCatchBlock，两个允许正则均为永不匹配 | error，不豁免 |
| SRC-004 | 稳定的命名规则 | Checkstyle 六类 Naming | error；允许具体限时 waiver/baseline |
| SRC-005 | equals/hashCode 约定、字符串比较等 | Checkstyle 精选规则 | error，不豁免 |
| OBS-001 | 方法过长先观察，不立即压垮遗留迁移 | MethodLength，60 非空/注释计数规则见 XML | warning，可见 |
| ARC-001 | domain 不依赖应用、端口、基础设施 | ArchUnit + 错误依赖反例 | error，不豁免 |
| ARC-002 | application 依赖接口而非具体 adapter | ArchUnit | error，不豁免 |
| ARC-003 | web 不绕过服务访问 repository | ArchUnit + 错误 Controller 反例 | error，不豁免 |
| BIZ-001 | 不可逆终态与幂等操作 | Task 方法 + 单元/并发测试 | error，不豁免 |
| CMP-001 | 保持核心 Java 8 API/字节码 | --release 8、class 52 审计、Java 9 API 反例 | error，不豁免 |
| CMP-002 | 使用真实旧运行时验证 | Surefire toolchain + runtime 断言 | error，不豁免 |
| GOV-001 | 不静默丢报告或漏文件 | quality_gate.py + 回归测试 | error，不豁免 |
| GOV-002 | 例外精确、可追踪、到期撤回 | quality_gate.py + 配额 + 内容哈希 | error，不豁免 |

Checkstyle 不负责排版缩进，以避免它与 Formatter 对同一问题给出相反答案。
首版不强制“所有 public 方法必须写一大段 Javadoc”等容易生成低价值噪音的规则。
MethodLength 是可见观察项；新代码出现大量 warning 仍应在 Review 中解释，不能当作质量目标。
`config/quality/policy.json` 是机器政策；新增可豁免类别需要先修改并测试治理程序，而不是仅添加一项 JSON。

## 新规则验收

必须有一个应当失败的反例、一个应当通过的正例、规则说明及误报评估。
能自动格式化的问题优先修复而不是新增告警。
规则升级必须独立于功能提交，注明范围和历史问题数量；不得悄悄更改严重级别或基线预算。
