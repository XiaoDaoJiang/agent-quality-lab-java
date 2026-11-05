# 渐进路线与完成定义

## M0：单应用 Java 8 试验田

[x] 单一 Spring Boot 应用 + 无 Spring 领域核心；所有源码目标 Java 8。
[x] Maven、Spotless、Eclipse JDT、Checkstyle、ArchUnit、JUnit、JaCoCo 选择 Java 8+ 兼容版本线。
[x] 不可变状态机、原子内存存储、HTTP 契约及架构测试。
[x] 原始 finding 可见的限时 warning/baseline 政策与离线回归测试。
[x] 真实检查器负例脚本、Agent 任务集、CI 模板与人审配置说明。
[ ] JDK 8/11/17/21 完整 Maven 验证、真实 Checkstyle/Spotless/ArchUnit/HTTP 实验。
[ ] JDK 25 compile-only 与 Java 8 字节码审计。
[ ] 远程仓库分支保护、真实 CODEOWNERS、环境审批配置。

“有配置/代码”与“已经在目标环境通过”是两种状态，不能混写。

## M1：跑通闭环

在 JDK 8、11、17、21 运行 format → verify → fixtures → HTTP smoke；在 JDK 25 运行 compile-only。
修正配置不一致必须保留原始失败证据并通过规则审查；不能全局关闭检查。
随后做第一个 Codex 任务，记录首次通过与修复轮数。
通过标准：故意违规能稳定阻断、合法例外可见、过期/漏扫能阻断、合法代码不会误阻断。

## M2：迁移一个真实旧模块

只引入一个真实业务链、有限规则与受审 baseline。保持原 Java 8 运行时和 Spring 版本不动。
记录历史/新增问题、无关 Diff 与人审时间。没有收益数据就不扩大部署。

## M3：增加缺陷与业务约束

根据真实漏检选择 P3C/PMD、SpotBugs 或其他分析器。扩展之前先设计原始报告、可信运行状态、正反例和适用豁免政策，并核对分析器是否能在 JDK 8 启动。

## M4：评估自进化质量

模型/Harness/提示词/工具变动时用相同任务集重复评估；测量误报、回退与重复缺陷，而不仅是 PR 数量。
从事故与 Review 反馈新增反例；Agent 提交规则改进 PR，维护者审核后升级。
不启用无条件自动合并、不赋予 Agent 改质量阈值/审批自己/自动续期例外的能力。
