# 工具链验收与验证边界

## 当前：新版默认工具链

用户于 2026-11-06 要求先提交实验，再将新版作为默认。实验已提交为 `daacc5b`；默认切换不使用版本 profile。
当前 Maven 宿主为 JDK 21，Spotless 3.11.0、Checkstyle 14.4.0；源码/API/生产与测试字节码继续 Java 8（major 52）。

| 本机命令 | 结果 | 原始证据 |
|---|---|---|
| `mise run check` | 0；项目 settings，无 MAVEN_ARGS 覆盖；JDK 21 构建、Java 8 全量测试、fixtures 与 HTTP | `.lab/normal-toolchain-20261106/check-project-settings.log` |
| `mise run matrix` | 0；同样使用项目 settings；8/11/17/21 四个测试/HTTP 通道及 JDK 25 compile-only 通过 | 同目录 `matrix-project-settings.log`、`matrix-project-settings-result.json` |
| `mise run format`、`mise run verify` | 均为 0；默认测试 JVM 为 JDK 21 | 同目录 `format.log`、`verify-default.log` |
| `mise run start` | Java 8 启动成功，HTTP 探测返回预期 404；测试结束后终止进程树，父进程退出 1、清理退出 0 | 同目录 `start.log`、`start-result.json` |

各 Java 测试通道执行 33 项 Java 测试，未跳过、未失败；Checkstyle 7 个正反例和 Java 8 API 反例通过。
最终 Python 治理回归为 66 项，通过；包括错误宿主、错配运行时、无效 settings、隐式 Java 25 测试和失败后不得继续 HTTP 的负例。
每个运行时的报告、实际 JVM 与 JAR SHA-256 由 `check` 自动保存到 `.lab/runs/<run-id>/`，不借用旧 JAR 或下一通道的报告。
CI 已调整为 JDK 21 构建加独立测试 JVM；本表仅记录本机证据，远程 CI 和独立人审以对应 PR 状态为准，尚无本机以外的 Linux/macOS 验证证据。
本机系统 mise 未覆盖，实际使用经校验的隔离版本 2026.11.2。手工 Ctrl+C、完整无缓存机器初始化未验证。
Python 入口显式使用版本控制内的 Maven Central settings；不需要实验目录的 settings，不改用户全局配置。
历史失败与例外原样保留；当前 BASE-001 scoped warning 没有扩大。

## 2026-11-07 格式化补验与后续决策

JDK 21.0.11 和 25.0.4.1 分别对同一组 26 个隔离文件执行当前 POM 继承的 Spotless 3.11.0 + Eclipse JDT 4.12.0。
包括 23 个当前源码/测试文件、1 个未格式化的中文/泛型/lambda 样例、2 个导入正反例。两次退出均为 0、未使用缓存跳过；
26 个输出逐字节一致。未格式化样例确实被改写，无用导入删除、有效导入保留；仓库 Java 源码未改变。
命令、日志、输出哈希及空 Diff 保存在 `.lab/formatter-acceptance-20261107/`。

IDEA 项目窗口可定位，当前项目设置文件已指向 `config/formatter/eclipse-codestyle.xml` 的 `P3C-CodeStyle`。
Computer Use 两次画面捕获分别返回 `FrameArrived timed out: timed out waiting on channel` 和
`window capture timed out: timed out waiting on channel`，因此转为手动补验。

用户在 IDEA 中手动格式化并保存 `idea-probe/FormatterProbe.java`。与同目录下
`jdk21/probe/src/main/java/fixtures/FormatterProbe.java` 比较：两份输出逐字节一致，均为 498 字节、LF，
SHA-256 为 `5df8c6f2817f6694b566ada014d289830889dc451a71252b79a7be9fd5f1a51e`；未格式化输入为 395 字节。
实操结论仅覆盖这个样例；比较记录保存在 `.lab/formatter-acceptance-20261107/idea-result.json`。

本机阶段通过。正式交付需要由独立审查者走 `quality-policy-review`，并在 PR 中取得该提交对应的 `quality-gate` 成功证据后再评估合并。

## 历史：首次旧工具链验收

验收时间：2026-11-05 至 2026-11-06（Asia/Shanghai）。命令记录使用 UTC 时间。

**旧工具链首次验收未全部通过：JDK 21 被 Spotless `removeUnusedImports` 的兼容性错误阻断。**
JDK 8、11、17 的完整验收和 JDK 25 compile-only 已通过。
2026-11-06 用户决定先记录兼容性差异，不通过移除自动清理步骤绕过；该候选已撤回，当前门禁和失败状态保留。

## 本轮环境与原始证据

- Windows x64；Python 3.12.0；Maven 3.9.6，位于项目允许的 3.6.3–3.x 范围内。
- 原有 JDK：Oracle 1.8.0_202、Temurin 11.0.24+8、Temurin 17.0.10+7。
- 本轮补齐：Zulu 21.0.13.0.3+1、Zulu 25.0.5.0.3+1，使用便携 ZIP，未修改系统环境变量或默认 JDK。
- 两个 ZIP 均来自 [Azul 官方下载服务](https://www.azul.com/downloads/)，下载元数据及官方 SHA-256 保存在证据目录。
- JDK 21 ZIP SHA-256：`7428890c66267aac516514085745dbedc6b8e7703eb0f7d73fb65cf9cd2cf306`。
- JDK 25 ZIP SHA-256：`792e1454a4abdd8379bb335f3f284652487cbb4113c92962312080b5bc661f72`。

证据根目录：`.lab/acceptance-20261105/`。该目录被 Git 忽略，需要单独保留或交付，提交本文不会带上原始日志。

| 内容 | 路径（相对于证据根目录） |
|------|-------------------------|
| 初始用户工作区快照、初始 Diff | `initial-workspace.zip`、`initial.diff`、`initial-status.txt` |
| 实际命令、JAVA_HOME、退出码、耗时、UTC 时间 | `commands.jsonl`；各执行目录的 `result.json` |
| 原始标准输出与错误输出 | 各执行目录的 `raw.log` |
| Maven 子命令证据 | 仓库 `.lab/runs/*/command-evidence.jsonl`；隔离副本清理待执行；各执行目录亦保存原始日志 |
| 测试、覆盖率、Checkstyle 与策略报告 | 各执行目录的 `{domain-core,app}/target/` |
| 字节码及测试总审计 | 各成功 verify/compile 目录的 `target/lab-summary.json` |
| HTTP 应用日志 | 各 HTTP 执行目录的 `target/smoke/` |
| 已撤回的诊断实验 | `proposal-*` 日志；原始副本快照及补丁保存在 `evidence.zip` 内 |

报告已在切换 JDK 或清理构建前分别复制保存，不能把后续 JDK 25 compile-only 的报告当作运行时测试报告。

## 实际工作区结果

表中数字为入口命令的实际退出码。`—` 表示按合同不执行。

| JDK | doctor | format | verify | fixtures | HTTP smoke | compile-only |
|-----|--------|--------|--------|----------|------------|--------------|
| 8u202 | 0 | 0 | 0 | 0 | 0 | — |
| 11.0.24 | 0 | 0 | 0 | 0 | 0 | — |
| 17.0.10 | 0 | 0 | 0 | 0 | 0 | — |
| 21.0.13.0.3 | 0 | **1** | **1** | 0 | 0，见下文限制 | — |
| 25.0.5.0.3 | 0 | 隔离格式化对比为 0 | — | 0 | — | 0 |

实际执行命令：

```powershell
# 每次在子进程中将 JAVA_HOME 和 PATH 指向对应 JDK 后执行
python tools/lab.py doctor
python tools/lab.py format
python tools/lab.py verify
python tools/lab.py fixtures
python tools/http_smoke.py --jar app/target/app-0.2.0-SNAPSHOT.jar

# JDK 25 专用通道，另执行 fixtures 验证真实检查器
python tools/lab.py compile
python tools/lab.py fixtures
```

JDK 8 首次运行顺序为 doctor → verify → format → fixtures → HTTP；format 没有产生源码改动。
其余三个运行时按 doctor → format → verify → fixtures → HTTP 顺序运行。
JDK 21 的失败没有被忽略或计为通过；后续 fixtures、HTTP 是分别记录的独立诊断。

- 成功的三个运行时每次均执行 39 项 Python 测试和 33 项 Java 测试（domain-core 26、app 7）。
  Java 测试 failures/errors/skipped 均为 0，ArchUnit、运行时断言和 JaCoCo 门槛通过。
- domain-core 实际行覆盖率为 53/53，分支覆盖率为 20/20。只描述本次样例，不外推质量保证。
- 生产和测试 class 经审计均为 major 52，包括 JDK 25 编译产物。
- 实际工作区的 fixtures 在五个 JDK 上均通过：5 个真实 Checkstyle 样例及 Java 9 API 负例。
- 每次成功 HTTP smoke 均完成脚本中的六项 API 断言，绑定 127.0.0.1，并退出其启动的进程。
- **原工作区 JDK 21 的 HTTP 使用的是前一轮 JDK 17 构建的 JAR**：21 的 verify 在 domain-core 阶段失败，
  尚未清理 app 的旧产物。它只证明该 JAR 在 21 上的 HTTP 行为，不能补足 21 的构建、测试和覆盖率；
  本轮原工作区 JDK 21 的 Java 测试与最终审计为 **NOT_RUN**。
- JDK 25 未运行应用或 Surefire 测试；compile 命令内的 `-DskipTests` 是合同明确的 compile-only 通道，
  不用于四个运行时的 verify，也不代表 Spring Boot 2.7.18 官方支持 JDK 25 运行时。

原工作区执行目录前缀：`jdk8-*`、`jdk11-*`、`jdk17-*`、`jdk21-*`、`jdk25-*`。
JDK 8 的首次 verify 单独命名为 `jdk8-verify-initial/`。

## JDK 21 兼容性差异与已撤回的诊断实验

详见 [TOOLCHAIN-001](issues/TOOLCHAIN-001.md)。原候选补丁已撤回，不再作为待应用方案；历史内容仅保存在原始证据归档中。

最小复现只有一个带 import 的 Java 类，以及 Spotless 2.30.0 的 `removeUnusedImports` 步骤，
JDK 21 稳定以退出码 1 报 `JCTree$JCImport.getQualifiedIdentifier()` 的 `NoSuchMethodError`。
Eclipse 排版引擎不涉及该调用；本机 javap 证据解释了为何 JDK 17 和 25 成功、21 失败。

候选在隔离副本中删除自动清理步骤，保留 Checkstyle `UnusedImports` error 检查及所有原有门禁，
并增加真实检查器的未使用导入负例和正常导入正例。以下数据只作为历史诊断证据保留；
用户已明确不采用该功能削减方案，不能将其通过结果计为当前工作区修复完成或政策批准。

| 隔离候选 JDK | doctor | format | verify | fixtures | HTTP smoke | compile-only |
|--------------|--------|--------|--------|----------|------------|--------------|
| 8 | 0 | 0 | 0 | 0 | 0 | — |
| 11 | 0 | 0 | 0 | 0 | 0 | — |
| 17 | 0 | 0 | 0 | 0 | 0 | — |
| 21 | 0 | 0 | 0 | 0 | 0 | — |
| 25 | — | — | — | 0 | — | 0 |

候选的四个 verify 每次仍是 39 项 Python 测试、33 项 Java 测试；没有失败或跳过，所有 class 均为 major 52。
候选 fixtures 是 7 个 Checkstyle 正反例加 Java 9 API 负例，在 8/11/17/21/25 全部通过。
候选 JDK 21 的 HTTP 使用同一轮成功构建的 JAR。

额外阻断试验：在隔离副本的 `Task.java` 中临时加入未使用的 `java.util.BitSet` 导入，
完整 `verify` 在策略门禁处以退出码 1 拒绝，原始报告保留 `UnusedImports` error。
随后逐字节恢复文件并再次运行 JDK 21 verify。这是诊断变异，不是豁免或允许提交的生产源码。
证据为 `proposal-unused-imports-hard-gate/`、`proposal/negative-gate-result.json` 和
`proposal-jdk21-verify-restored/`。正向矩阵证据为 `proposal-jdk*/`。

本轮只试验一个修复候选；未修改实际工作区的 POM、工具、配置、Java 源码、测试或 CI，未新增或续期例外，未提交或合并。

## 格式化比较

- 使用同一份初始源码和一个包含中文、泛型、lambda、注释与换行的未格式化探针，在隔离副本分别运行
  JDK 8 和 JDK 25 的原配置 `format`。25 个 Java 文件输出逐字节一致。
  证据：`formatter8-apply/`、`formatter25-apply/`、`formatter-comparison.json`。
- 已定位本机实际安装的 IDEA 插件 `EclipseCodeFormatter`，版本为
  `23.5.241.000.0-Eclipse_2024-09`，其内置 Eclipse 引擎不同于项目固定的 JDT 4.12.0。
- 直接加载该已安装插件的 `eclipse.jar`，使用同一份 `eclipse-codestyle.xml` 对上述 25 个输出再次格式化，
  全部逐字节不变；每个文件还验证了引擎输出非空及二次格式化幂等。
  证据：`plugin-engine-all.json`、`plugin-engine-all.log`、`PluginEngineProbe.java`。
- **IDEA 内实际操作仍为 NOT_RUN**。Computer Use 首次报 `failed to activate captured window`，
  重新选择窗口后的状态捕获报 `FrameArrived timed out: timed out waiting on channel`，已停止界面控制。
  引擎样本一致不证明 IDE 插件的实际启用、保存钩子、导入整理或所有未来源码都一致。

## 保留的 warning、豁免与后续要求

- domain-core 原有 `BASE-001` 在每轮成功构建中仍产生 1 条可见 warning：
  `LegacyCustomerRow.java:5` 的 `MemberName`，到期日 2027-02-03。原始报告不删除 error。
  本轮未修改其范围、内容哈希或到期日，也未核验历史独立审批凭据。
- Maven Checkstyle 报 `inputEncoding` 为只读参数；ArchUnit 测试输出 SLF4J 缺少 binder 的提示。
  JDK 25 还有 Maven 所带 Jansi 的 native-access 及 Guava Unsafe 弃用告警；均原样保留，不以关闭告警处理。
- 当前工作区仍不能声明完整矩阵通过。后续应寻找保留自动清理能力的兼容修复，按政策独立审查后重跑完整验收。
- IDE 内实际比较、远程 CI、服务器分支保护、CODEOWNERS 与环境审批均为 **NOT_RUN**。
  本轮本机结果不能证明这些服务器控制存在或不可绕过。

## 2026-11-06 差异记录与副本清理

用户决定保留现有自动清理要求，不采用移除步骤的候选；本次不申请应用该补丁。
计划清理三个隔离项目副本及已归档的重复源码快照、活动候选补丁、临时缓存和重复下载 ZIP。
自动审批检查拒绝删除操作，仅返回 `blocked by policy`，无更具体原因；本轮尚未删除任何副本，清理为 **NOT_RUN_POLICY_REJECTED**。
原始日志、报告、最小复现、初始工作区快照、便携 JDK 和官方元数据保留。
清单见 `.lab/acceptance-20261105/cleanup-20261106.json`。
`evidence.zip` 及其 SHA-256 保持不变，属于本次决定之前的原始历史归档；其中旧的“待审候选”状态以本文和 TOOLCHAIN-001 为准。

## 历史静态修订与离线记录

以下保留的是首次真实验收之前的记录；“只有 JDK 21、没有 Maven”指当时的执行容器，不是本轮开发机。

日期：2026-11-05。修订目标：将原先的 `app-modern` / `app-legacy` 双应用结构收敛为**单一 Spring Boot 应用，所有代码与工具链最低兼容
Java 8+**。

### 当时完成的静态修订

- 删除 `app-modern`、`app-legacy` 两套应用，建立唯一 `app` 模块。
- `domain-core` 与 `app` 统一 `maven.compiler.release=8`。
- Spring Boot 统一为 2.7.18；不再出现 Boot 3.x / Java 17 的应用模块。
- 工具链降到 Java 8 可运行的兼容版本线：Spotless Maven 2.30.0、Eclipse JDT 4.12.0、Checkstyle 9.3、Maven Checkstyle Plugin
  3.6.0、Compiler 3.13.0、Surefire 3.2.5、Enforcer 3.5.0、ArchUnit 1.3.0、JaCoCo 0.8.14、Exec Maven Plugin 3.5.1。
- Maven Enforcer 下限为 JDK 8 / Maven 3.6.3；根 POM 固定 Java 8 编译目标。
- CI 改为 JDK 8 / 11 / 17 / 21 完整验证，JDK 25 compile-only。
- `audit_results.py` 检查生产和测试字节码均不超过 major 52。
- 取消双应用/Java8 Toolchain Profile；用 CI 的真实 JDK 矩阵运行同一应用。

### 当时未执行的项目

- 尚未执行真实 Maven 构建、真实 Spotless/Checkstyle/ArchUnit/JaCoCo 测试、Spring Boot 启动或 JDK 8/25 矩阵。
- 当前执行容器只有 JDK 21，没有 Maven；因此不能声称上述修订已经在 Java 8 和 JDK 25 上跑通。
- 本轮应先执行 Python 策略自测、XML/JSON 结构校验、Java 源码静态扫描和 JDK 21 `javac --release 8` 核心编译；这些只能算部分验证。

### 当时列出的目标环境命令

在 JDK 8、11、17、21 分别执行：

```bash
python tools/lab.py doctor
python tools/lab.py format
python tools/lab.py verify
python tools/lab.py fixtures
python tools/http_smoke.py --jar app/target/app-0.2.0-SNAPSHOT.jar
```

在 JDK 25 执行：

```bash
python tools/lab.py compile
```

只有完整矩阵通过后，才能声明 Java 8+ 工具链兼容。JDK 25 只做 compile-only，不声明 Spring Boot 2.7.18 官方支持在 JDK 25 运行。

### 当时实际执行的离线验证

| 检查                  | 结果                                      |
|---------------------|-----------------------------------------|
| Python 策略与受保护路径测试   | 39 项通过                                  |
| 无 Maven 的核心离线 smoke | 79 次断言通过，运行于本环境 JDK 21.0.12.1           |
| 核心模块 Java 8 字节码     | `javac --release 8` 实测 major version 52 |
| Java 9 API 负例       | `List.of` 在 Java 8 编译目标下被拒绝             |
| POM / XML / JSON 结构 | 通过                                      |
| Java package 与目录结构  | 22 个 Java 源文件通过                         |
| Java 8 API 简单静态扫描   | 通过                                      |

这些结果不能替代 Maven、真实静态检查器、Spring Boot HTTP、JDK 8 运行时或 JDK 25 compile-only 验证。
