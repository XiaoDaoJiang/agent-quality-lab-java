# 限时例外与基线

## 三种结果

**error**：阻断交付。**advisory warning**：明确选择观察的规则，当前只有 MethodLength。
**waived/baselined warning**：原始为 error，但一条精确且有效的记录将单个命中降为 warning。
不是 `failOnViolation=false` 全面放行，也不通过 native suppression 从原始 XML 中删除问题。

## 首版能与不能

仅命名规则可以申请例外。格式、空 catch、编译错误、测试失败、架构依赖、报告/治理错误不可降级。
这些不可降级项不是所有公司所有场景的永恒真理，而是此 Demo 的初始政策；需要改变必须单独设计和人工审查。
无“忽略所有”和“整个包免检”开关。

## 一条记录

waivers.json 和 baseline.json 结构相同，kind 分别为 waiver / baseline：

```json
{
  "id": "WAIVER-001",
  "kind": "waiver",
  "engine": "checkstyle",
  "file": "domain-core/src/main/java/dev/agentlab/core/compat/LegacyCustomerRow.java",
  "rule": "MemberName",
  "line": 5,
  "sourceSha256": "必须来自被审查源文件的真实 SHA-256",
  "owner": "实际负责人",
  "reason": "充分说明为何不能现在修复以及保留的风险（不少于20字符）",
  "issue": "docs/issues/实际问题记录.md",
  "created": "YYYY-MM-DD",
  "expires": "YYYY-MM-DD"
}
```

上例仅说明格式，不是可以直接批准的配置。现有 BASE-001 已占据对应 scope，不允许再加重复 waiver。
以 UTC 日期判断，到期日当天 00:00 开始失效。单次 waiver ≤30 天，baseline ≤90 天。
默认最多 3 条 waiver、1 条 baseline；不是一键生成几千条既有问题白名单。

## 申请流程

先运行真实工具得到 finding；检查是否误报或兼容性需求；优先尝试修复。
无法修复时运行 `python tools/quality_gate.py propose --module domain-core` 输出草稿，补上负责人、问题、理由和日期。
Agent 只提案。人类维护者在政策 PR 中审查，修改记录，并通过服务器侧审批后合并。
不设可自填即生效的 approvedBy 字段，因为文件里写个名字不是身份验证。

生效后每次构建原始 error 仍在 XML；JSON 中含 originalSeverity=error、effectiveSeverity=warning 与元数据。
源文件任何字节变化即失效：这是保守策略，避免在同一行、同一文件中悄悄引入新问题被旧例外覆盖。
一个记录命中两次、找不到原命中、缺元数据、越界路径、内容哈希不符、过期、预算超限都阻断。

## 基线与迁移

baseline 表示在某个受审代码版本上确认的存量债务，waiver 表示一次特殊情况。
它们都不是永久允许，实际效果都只是精确命中降级并显示。
修复后删除对应记录；不得自动重新生成整份 baseline，更不能自动延长所有 expires。
治理文件和生成器也需要保护。真正审批能力由 CI 环境和分支规则保证，详见 CI-SETUP。
