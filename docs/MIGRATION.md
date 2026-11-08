# 向已有系统渐进迁移

## 原则

先迁移质量检查链，不顺便升级 Spring Boot、JDK 业务运行时、数据库或所有依赖。Demo 的最低 Java 基线是 8；旧项目若仍使用 Java
8，可将构建宿主单独升级到 JDK 21，继续复用业务运行时及 Eclipse Formatter 配置；不能提高应用最低版本。

## 建议切片

**切片 0：固定现状。** 记录 JDK、Maven、Spring Boot、EclipseCodeFormatter 的 JDT 版本和 XML、P3C 插件版本、构建命令、现有静态检查及已知历史问题。

**切片 1：只接一个模块。** 从 5–10 条高确定性规则开始，先跑报告评估误报。观察阶段不要冒称门禁已强制；正式启用后，缺报告或工具执行失败必须阻断。

**切片 2：统一格式。** 复用团队已有 Eclipse XML，不把全仓突然改成 Google Style。当前 Spotless 3.11.0 在 JDK 21 构建环境运行，使用 Eclipse
JDT Formatter XML，应用继续保持 Java 8。先验证 IDEA 插件与 Maven Spotless 的格式结果一致，再扩大覆盖范围。

**切片 3：冻结存量。** 为少量确实不能立即修复的问题建立待审 baseline，记录 owner、原因、issue、文件内容 SHA-256
和到期日。新问题不准进入旧基线。本 Demo 采用完整文件哈希，故意偏保守；文件改动后必须重新审查。

**切片 4：接入构建门禁。** 将 Spotless Check、Checkstyle 与策略适配器接入 Maven 生命周期，再接 Jenkins/GitLab CI。确保普通
`mvn verify` 不能绕过质量检查。

**切片 5：按风险加深。** 为重要状态转换补测试，再限制模块依赖，然后试运行 P3C/PMD、SpotBugs
等分析器。每次只启用能解释、能重现、误报可接受的规则；维护规则所有权矩阵，避免工具重复或冲突。

**切片 6：集中复用。** 多项目确有需要时，再发布统一 Maven Parent / 规则 JAR，或评估 TCA/Sonar。第一版不自行开发组织级质量平台，也不
fork 所有工具。

## Java 8 兼容核对

- 所有业务源码和测试源码使用 Java 8 语法与 API。
- `maven.compiler.release=8`；在 JDK 21+ 通过 `--release 8` 限制 API 与字节码。
- 第三方依赖的 class major version 不得超过 52；不能只审计自有代码。
- Spotless、Checkstyle 与 Maven 在 JDK 21+ 启动，独立验证其执行状态；全量应用测试和 HTTP 在 Java 8 上执行。
- 真实 JDK 8 测试与应用启动是必要验收；JDK 25 compile-only 不能替代 Java 8 运行验证。
- Spring Boot 2.7.18 官方兼容至 Java 21，已结束开源维护。JDK 25 运行时不在本 Demo 的官方支持声明中。

## 大格式提交

一次性纯格式提交应与功能修改分开，必要时使用 `.git-blame-ignore-revs` 记录纯格式版本。不能用忽略 blame 掩盖业务变化。共享格式配置和
JDT 版本升级需要评估 Diff、IDE 与 CI 一致性及回滚方案。
