# Agent Quality Lab — 工作合同

## 项目使命

本项目是建立高质量、高信任、可验证、能纠错 Agent 研发环境的长期试验田，不是业务产品。优先通过架构、类型、静态分析、测试和 CI
降低错误概率；不要把更长的提示词当作主要防线。

“自进化”意味着把真实失误转成反例、规则、测试和架构改进。Agent 可以发现问题、生成规则 PR 和豁免提案，但不能自行批准政策、改变验收阈值、扩大抑制范围或续期例外。

任何未实际验证的能力必须标记 NOT_RUN；配置文件存在不代表工具运行成功，Agent 声称通过不等于真实证据。

## 权威文件

开始前先读 `README.md`、`docs/ARCHITECTURE.md`、`docs/RULES.md` 和 `docs/ROADMAP.md`。涉及规则/豁免时读 `docs/WAIVERS.md`
；涉及旧项目时读 `docs/MIGRATION.md`；涉及工具版本时读 `docs/TOOLCHAIN.md`。

规则冲突时停止并报告，不自行选择较宽松的规则。

## 唯一 Java 兼容基线：Java 8+

**本项目只有一个 Spring Boot 应用和一个 Java 8 应用基线。禁止恢复 app-modern / app-legacy 双应用结构，禁止提高应用最低 Java 版本。**

- 所有生产代码和测试代码均使用 Java 8 语法、JDK API 和字节码。
- 根 POM 的 `maven.compiler.release=8` 是唯一编译目标；所有模块必须遵循。
- Maven、编译器、格式化器和静态检查器使用 JDK 21+；默认构建宿主为 JDK 21。
- Java 8、11、17、21 分别作为 Surefire 测试 JVM 和 HTTP 应用运行时；构建 JVM 不随运行时通道降低。
- JDK 25 只执行 compile/package 与 Java 8 字节码审计；Spring Boot 2.7.18 官方兼容范围到 JDK 21，不得声称官方支持 JDK 25
  运行时。
- Spring Boot 2.7.18 已结束开源维护，只用于 Java 8 兼容实验，不作为新生产系统推荐版本。
- Maven 3.9.11–3.x；默认 Maven 3.9.11。禁止 Maven 4。
- Python >=3.10 仅用于仓库治理工具，不进入应用运行时。

固定工具链：Spring Boot 2.7.18、Maven Compiler 3.13.0、Spotless Maven 3.11.0、Eclipse JDT 4.12.0、Maven Checkstyle
Plugin 3.6.0、Checkstyle 14.4.0、ArchUnit 1.3.0、JaCoCo 0.8.14、Surefire 3.2.5、Enforcer 3.5.0、Exec Maven Plugin
3.5.1。升级前核实插件/引擎的构建运行时要求，并独立验证 Java 8 产物；不要求构建工具在 Java 8 启动。

## 架构约束

- `domain-core` 不得依赖 Spring；只包含领域、应用服务、ports 和 adapter。
- `app` 是唯一 Spring Boot 适配层；Web Controller 只能调用应用服务，不得直接访问 repository/adapter。
- 领域对象不可变，状态变更经 `Task.complete/cancel`；终态约束不可由 Controller 绕过。
- 并发状态更新必须保持按任务原子化。
- 所有新增 Java 代码必须兼容 Java 8；禁止 `var`、record、sealed、text block、switch expression、`List.of`、`Map.of`、
  `String.isBlank`、`Optional.isEmpty` 等 Java 9+ 语言或 API。
- HTTP 仅绑定 `127.0.0.1`。无数据库、账号令牌或外部业务服务；样例数据不得含真实个人信息。禁止将 Demo 直接部署公网或生产。

## 统一执行入口

```bash
python tools/lab.py doctor
python tools/lab.py selftest
python tools/lab.py format
python tools/lab.py verify
python tools/lab.py fixtures
python tools/lab.py check --runtime 8
```

JDK 25 编译专用通道：

```bash
python tools/lab.py compile
```

完整验证使用 `mise run matrix`。各 `check:8/11/17/21` 在 JDK 21 构建、执行全部 fixtures，
将所有 Java 测试和 HTTP smoke 交给指定运行时。`LAB_RUNTIME_JAVA_HOME` 是本机运行时覆盖；缺失、版本错配或 verify 失败必须停止。
JDK 25 的 `compile` 不等于运行时验证。禁止恢复版本选择 profile 或通过降低构建 JDK 绕开新版检查器。

## 工作流程与纠错

1. 明确任务、影响模块、非目标和验收检查；小任务不增加无用设计文件。
2. 缺陷修复先补失败用例；新规则同时补正例与负例。
3. 先由 Spotless 修复格式，再根据原始诊断修复业务代码。
4. 保持最小 diff，不顺手清理无关历史代码，不覆盖用户未提交修改。
5. 最多自行修复 3 轮；无法收敛时报告原因、尝试、剩余风险和需要的人工决策。
6. 所有测试、架构检查、兼容检查和格式检查必须通过；必要告警必须在报告中保留。
7. 交付说明包括实际命令、退出码、测试与报告路径、变更范围、豁免及未验证项。

## 禁止用“通过”代替“正确”

禁止跳过或删除失败测试、替换真实测试为恒真断言、扩大 excludes、关闭检查插件、加入全局 ignore/skip。
禁止用删掉代码路径、伪造报告、把所有 error 改为 warning 的方式让构建变绿。
禁止无审批更改版本、release、质量阈值、CI、受保护文件或抑制清单。
任何测试改动都需说明为什么是业务契约变化，而不是掩盖缺陷。
更改 `config/`、`tools/`、所有 POM、`.github/`、AGENTS.md 或测试，必须走独立的人类政策/验收审查。此约束还需要服务器端分支保护执行，不能靠本文件或本地
Hook 自证不可绕过。

## Warning 与例外

- `MethodLength` 是唯一全局 advisory 规则。
- 只有明确列入 allowlist 的命名规则支持具体 waiver/baseline。
- 例外必须有 id、文件精确内容哈希、规则、行号、负责人、原因、问题记录和到期日。
- 原始报告不删除命中；策略报告将该命中降为 warning，并附上例外详情。
- Agent 可以生成只读豁免提案，不可以自行批准、扩大范围、延长有效期或更新基线。
- 编译、格式、测试、架构、空 catch、报告缺失和工具执行失败不可豁免。
- metadata 中的 owner 不是审批证据；实际批准依赖 PR 审查与受保护环境。

## 持续演进

真实失败 → 记录问题 → 最小反例/正例 → 选择最低层有效约束 → 测试误报 → 人审规则 PR → 纳入回归。
优先顺序：领域模型/模块边界 → 编译/静态分析/测试 → Agent 工作指导 → 人审高风险部分。
不要一次堆满 PMD、P3C、SpotBugs、Error Prone、Sonar 等同类工具。先证明当前链路能工作再扩展。
修改模型、提示词、规则或工具版本后，用 `experiments/tasks/` 中相同任务重新评估。
指标来自实际运行：首次通过、修复轮数、误报、人审耗时、无关 diff、重复缺陷、活跃/过期豁免。没有数据时标 NOT_RUN，不得伪造趋势、通过率或安全保证。
