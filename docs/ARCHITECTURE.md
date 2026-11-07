# 架构与信任边界

## 单一 Java 8 基线

本项目只有两个 Maven 模块：`domain-core` 与 `app`。二者的生产代码和测试代码全部编译为 Java 8（class major 52）。`app` 是唯一
Spring Boot 2.7.18 应用；没有 modern/legacy 双应用，也不将 Java 17 作为最低要求。

Spring Boot 2.7.18 官方兼容 Java 8–21，已结束开源维护。JDK 25 作为额外编译宿主执行 compile/package 和字节码审计，不在 JDK
25 启动该应用；不宣称 Boot 2.7.18 官方支持 Java 25 运行时。

构建与运行时分离：默认 JDK 21 启动 Maven、编译器及检查器，`--release 8` 限制生产和测试代码的 API 与字节码。
Surefire 使用显式 JVM 路径分别运行于 Java 8/11/17/21，HTTP 冒烟使用同一通道的 JVM；没有不同版本的业务应用。

## 模块边界

`web → application → ports ← adapter`。领域对象仅依赖 JDK；`domain-core` 不依赖 Spring。`app` 负责 Spring
Configuration、HTTP Controller 和异常映射。Controller 不得直接访问 repository/adapter。

每个任务的不变量位于不可变 `Task`；状态更新使用 `ConcurrentHashMap.compute` 保持同一任务的原子性。并发测试验证“完成/取消最多一个成功”，而不是只用单线程
happy path。

## 约束层次

模型约束防止不合法状态通过公共构造器出现；ArchUnit 限制依赖方向；Checkstyle 发现已定义的代码规范违规；Spotless 统一格式；JUnit
验证行为；JaCoCo 衡量覆盖率。所有工具都有覆盖边界。Lint 通过不代表实现正确，也不代表不存在漏洞。

## 例外策略

Checkstyle 原始报告不安装 suppression filter，保留所有 finding。Python 策略适配器不重新实现 Java
AST/Linter，只检查报告完整性、finding 覆盖、严重级别和限时例外元数据。原始 error 仅在精确 waiver/baseline 命中时转为可见
warning。

任何 Maven 工具执行错误、报告缺失、报告格式异常、漏扫源码、过期例外或 finding 消失，都 fail-closed。格式、编译、测试、架构、空
catch 不可豁免。

## 工具链信任边界

默认构建宿主为 JDK 21：Spotless Maven 3.11.0、Eclipse JDT 4.12.0、Checkstyle 14.4.0、Maven Checkstyle Plugin
3.6.0、Compiler Plugin 3.13.0、Surefire 3.2.5、Enforcer 3.5.0、ArchUnit 1.3.0、JaCoCo 0.8.14。
升级后在 JDK 21 执行全部门禁，在 Java 8/11/17/21 执行全部测试和 HTTP，并额外验证 JDK 25 compile-only。
构建工具自身的 JDK 下限与应用最低运行时分别验收，不能只看生成字节码目标。

## 真实安全边界

编写业务的 Agent 如果能改 POM/测试/CI，自然也能破坏检查；单仓库程序不能阻止拥有同等权限的人改程序本身。必须结合只读 CI
token、分支保护、无 bypass 权限、独立人审与可信政策检查。没有服务器保护时，只能称为本地质量检查链，不能称为不可绕过的合并门禁。
