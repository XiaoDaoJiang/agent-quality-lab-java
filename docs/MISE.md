# mise：可复现环境与项目生命周期

共享配置以 `mise.toml` 为准，工具下载来源及校验值以 `mise.lock` 为准。任务继续使用现有 Python/Maven 门禁。

## 新机器初始化

支持目标为 Windows x64 和 Linux x64（glibc）；macOS、ARM、musl 尚未纳入验收。
先安装 **mise 2026.11.2**。旧版 2026.4.20 不满足本项目锁文件能力要求，配置会明确拒绝它。
本轮未覆盖系统 mise；本机验证使用经官方 SHA-256 校验的隔离版本，位于：
`.lab/mise-portability-20261106/bootstrap/mise/mise/bin/`。可将该目录临时置于当前终端 PATH 首位，或升级系统 mise。

```text
mise --version
mise trust mise.toml
mise install --locked
mise tasks validate
mise run config:check
mise run doctor
mise run check
```

`auto_install=false` 只禁止执行任务时隐式下载；新机器显式运行 `mise install --locked` 完成安装。
缺少工具、锁条目或校验失败应停止，不能改成非锁定安装来获得通过。
所有 Java 版本都在共享 tools 中显式列出：第一个 JDK 17 是默认值，任务单独选择 8/11/17/21/25。
配置不使用本机别名、磁盘路径或 latest。

共享版本为 Temurin 17.0.10+7、Temurin 11.0.24+8、Zulu 8.94.0.17（Java 8u492）、
Zulu 21.54.109.0、Zulu 25.38.109.0、Python 3.12.0 和 Maven 3.9.11。
相对于此前本机方案，Java 8 验收环境由 Oracle 8u202 改为可公开获取的 Zulu 8u492，Maven 从 3.9.6 统一为 CI 已使用的 3.9.11。
应用语法、API 和字节码目标仍为 Java 8；POM、格式化引擎和检查规则没有升级。

Maven 使用官方 Maven Central 发行包及官方 SHA-512，通过 mise HTTP backend 安装，不依赖本机 PATH 中的 Maven。
发行包保留顶层目录，`bin_path` 指向该目录中的 `bin`，遵循 [HTTP backend 的解包与路径约定](https://mise.jdx.dev/dev-tools/backends/http.html#bin-path)。
Java 的锁条目来自厂商官方发布 URL 和校验值：Temurin 发布附件的 `.sha256.txt`、Azul 包元数据 API。
本机无法访问 mise Java 元数据服务，因此本轮以这些真实厂商数据补齐锁文件，没有关闭校验或伪造缺失条目。
Python 条目保留 mise 解析的固定下载 URL 和校验值。各平台是不同的二进制文件，不要求平台间包哈希相同。

## 可选的本机安装复用

在忽略的 `mise.local.toml` 中使用 mise 的 `{ path = "本机安装目录" }` 复用**相同版本**安装。
共享文件不包含这些路径；`mise.local.toml`、环境本地覆盖和本地锁文件均已加入 Git ignore。
Task 自身的工具选择优先级高于 tools 默认值；复用某个矩阵任务的 JDK 时，应在本地配置中覆盖该任务的 `tools.java`。
环境快照会验证实际版本，不能把其他版本或其他 JDK 偷换成已声明版本。
CI 拒绝加载本地覆盖，必须从共享配置及锁文件安装。更换共享版本或更新锁文件须独立政策审查。

## 任务与失败语义

使用 `mise tasks ls` 查看完整目录。常用入口：

- `mise run config:check`：检查共享声明、锁文件、矩阵完整性和真实 verify 入口。
- `mise run doctor`：工具版本、JVM、环境和例外元数据检查。
- `mise run format`：原有 Spotless 自动格式化，会修改源码。
- `mise run build` / `test` / `verify`：同一完整 clean/verify/package/审计入口。
- `mise run check`：配置检查 → JDK 17 完整门禁 → fixtures → Java 8 冒烟同一个 JAR。
- `mise run start`：Java 8 前台启动已有 JAR，绑定 127.0.0.1:8080；Ctrl+C 停止。
- `mise run dev`：完整 verify 成功后再 start。
- `mise run matrix`：依次运行 check:8、check:11、check:17、check:21、compile:25，遇错即停。

start/smoke 不隐式构建；缺少 JAR 时失败。JDK 25 只编译，不启动应用。
JDK 21 的 TOOLCHAIN-001 保持开放，矩阵不能声明通过；可单独执行 compile:25 获取独立证据。
共用 target 的任务串行执行，没有任务缓存或忽略失败；不要从多个终端同时构建同一工作区。

## 环境证据

执行入口在 task 的工具覆盖生效后采集快照。Java、javac、Maven、Python、mise 的实际路径与版本、
JAVA_HOME、MAVEN_HOME/M2_HOME、OS/架构、预期版本、编译目标、配置摘要和当前 JAR SHA-256 均记录。
控制台打印简明环境信息，完整快照写入 `.lab/runs/<run-id>/environment.json`。
构建子命令的 command-evidence.jsonl 关联该快照；直接调用 Python 入口也会采集环境。
start 和 HTTP smoke 也记录各自环境，不能用 JDK 17 的 doctor 日志证明 Java 8 运行环境。

预期版本不符、JAVA_HOME 与实际 JVM 不符、构建 javac/Maven JVM 不一致时硬失败，失败快照照样保存。
显式 `http_smoke.py --java` 可选择独立运行 JVM；其实际版本仍须满足任务的预期运行时。
selftest 保留离线语义，缺少 Java/Maven 不阻止 Python 治理测试，快照标为 observed 而不是工具链验收通过。
只记录允许的环境变量；JVM/Maven 附加参数仅显示是否设置，不打印其值或全部环境。

## 自动保护与验收边界

mise 配置、锁文件和任务目录纳入 policy_guard。版本漂移、本机路径、缺平台校验值、矩阵缺项和替换真实 verify 的负例进入回归。
新增 Windows/Linux CI 作业执行锁定安装、声明检查、mise check；结果纳入 quality-gate，并保留环境快照。
原有 JDK 8/11/17/21 和 25 通道继续保留，不以入口作业代替它们。
首次纳入保护需要本次独立人审；服务器保护和审批环境仍须由维护者实际配置。

本轮原始命令、日志和验证结果保存在 `.lab/mise-portability-20261106/`。
跨平台锁定不等于各平台已运行通过，也不等于最终 JAR 跨平台逐字节一致。
远程 CI、Linux/macOS 实际运行、人工 Ctrl+C 仍以实际记录为准，未执行项标记 NOT_RUN。

## 2026-11-06 本轮实测

| 命令/检查 | 退出码与结果 | 原始证据（`.lab/mise-portability-20261106/` 下） |
|---|---|---|
| `mise tasks validate`、`mise run config:check` | 0；16 个任务和双平台锁声明有效 | `config-check.log` |
| `mise run selftest` | 0；55 项治理回归通过 | `selftest.log` |
| `mise run check` | 0；JDK 17 完整验证、33 项 Java 测试、fixtures、同一 JAR 在 Java 8 HTTP 冒烟通过 | `check.log` |
| `mise run matrix` 第二次运行 | 1；8/11/17 完整通道通过；21 在 Spotless 失败并停止，21 后续步骤和 25 未执行 | `matrix.log`、`matrix-result.json` |
| `mise run compile:25` 单独执行 | 0；两个模块 class major 均为 52；不执行运行时测试 | `compile25.log`、`compile25-result.json` |
| `mise run start` 启动探测 | Java 8 在 127.0.0.1:8080 启动，预期不存在资源返回 404；测试随后终止该进程树，父进程退出 1，清理退出 0 | `start.log`、`start-result.json` |
| 真实错配 JDK / CI 本地覆盖负例 | 被测入口均退出 1，失败记录保留；断言脚本退出 0 | `negative-version.log`、`negative-ci-local.log` |
| CI YAML 解析及依赖检查、`git diff --check` | 0；Windows/Linux 入口均纳入最终门禁 | `verification.json` |

首次矩阵运行在 8/11 成功后，JDK 17 的 `mvn -version` 发生一次 JVM 原生崩溃：
`classLoader.cpp:374 / jimage file name is null`。原始记录保留为 `matrix-first-attempt.log` 和 `hs_err_pid12436.log`。
随后独立 doctor 和第二次矩阵中的 JDK 17 成功；原生崩溃原因尚未确定，不能宣称已修复，也未加入自动重试掩盖它。

Windows 的 Zulu 8/21/25、Maven 已完成锁定下载安装；Temurin 11/17 和 Python 因 GitHub 下载缓慢，
本机复用了忽略配置中的相同版本安装。**完整无缓存初始化、Linux 实际执行、远程 CI、人审及手工 Ctrl+C 均为 NOT_RUN。**
JDK 21 的 TOOLCHAIN-001 未修复、未应用候选补丁；原有 BASE-001 scoped baseline warning 仍保留。
本轮修改覆盖入口、环境采集、锁声明验证、治理回归、保护范围与 CI；没有修改 Java 业务契约、POM、规则或阈值。
未提交 Git；受保护文件仍需独立人类政策/验收审查。
