# Agent Quality Lab

一个渐进式 Java / Spring Boot / Maven Agent 质量试验田。**全项目唯一最低 Java 基线为 Java 8**；不是 Java 17+ 项目，也不拆分
modern/legacy 两套应用。

> 当前默认链路：JDK 21 构建、Spotless 3.11.0、Checkstyle 14.4.0；应用与测试保持 Java 8。
> Java 8/11/17/21 是测试和 HTTP 运行时，JDK 25 仅为额外编译宿主。实际结果与未验证项见 `docs/DELIVERY-VALIDATION.md`。

## 1. Java 8 基线与 JDK 25

| 项目          | 选择                   | 说明                                                        |
|-------------|----------------------|-----------------------------------------------------------|
| Spring Boot | 2.7.18               | Java 8 起，官方兼容至 Java 21；已结束开源维护，仅作试验/迁移样例                  |
| Java 源码/API | Java 8               | 生产和测试代码统一 `release=8`，class major version 不得超过 52         |
| Maven       | 3.9.11–3.x            | 本项目固定 Maven 3.9.11，构建宿主使用 JDK 21+                      |
| 构建 JDK      | 21 默认、25 编译可选                | JDK 25 用于编译/打包 Java 8 字节码，不代表 Boot 2.7.18 官方支持在 JDK 25 运行 |
| 完整运行验证      | JDK 8 / 11 / 17 / 21 | CI 对四个运行时执行全量测试与 HTTP smoke                               |
| JDK 25 验证   | compile-only         | 格式、静态规则、编译、打包和 Java 8 字节码审计，不启动应用                         |
| Python      | 3.10+                | 仅用于质量策略与实验脚本，不进入 Java 应用运行时                               |

Spring Boot 3.x/4.x 的最低 Java 版本是 17，不符合本项目目标。Boot 2.7.18 是 Java 8 兼容的最后一代 Boot
2.x，但已结束开源维护；真实旧系统迁移时必须另行评估商业支持、依赖安全和升级路线，不能把 Demo 版本直接照搬到生产。

**构建 JDK 与应用最低版本分离。** 默认 JDK 21 启动 Maven、格式化器、检查器及编译器；Compiler 3.13.0 使用
`--release 8`。Surefire 通过显式 JVM 路径在 Java 8/11/17/21 执行全部测试；JDK 25 仅编译和审计。

## 2. 项目结构

```text
agent-quality-lab/
├── AGENTS.md
├── pom.xml
├── .editorconfig
├── app/                         # 唯一 Spring Boot 应用，Java 8
├── domain-core/                 # 无 Spring 生产依赖的领域核心，Java 8
├── config/formatter/            # Eclipse JDT XML
├── config/checkstyle/           # Checkstyle 规则
├── config/quality/              # policy / baseline / waivers
├── experiments/                 # 正例、反例、Codex 固定任务集
├── tools/                       # 门禁适配器、审计和实验工具
├── docs/                        # 架构、规则、迁移、路线与 ADR
└── .github/workflows/quality.yml
```

## 3. 首次运行

已初始化项目级 mise 任务入口，可复现安装、可选本地覆盖及完整任务说明见 [docs/MISE.md](docs/MISE.md)。
mise 需 2026.11.2；默认构建使用 JDK 21，产物保持 Java 8。
`mise run check` 执行配置检查及 Java 8 全量测试、fixtures 和 HTTP；`mise run matrix` 覆盖四个运行时并执行 JDK 25 compile-only。
日常入口为 `mise run format`、`mise run check`、`mise run dev`。没有 modern profile 或 modern 任务别名。

前置：构建 JDK 21+、Maven 3.9.11–3.x、Python 3.10+，并能访问所需 Maven 仓库。
mise 固定 Maven 3.9.11 和完整厂商 JDK 版本；Python 声明 3.12 系列，由锁文件固定已验签的 3.12.x 补丁及下载构件。
本机覆盖可分别复用构建与运行时 JDK。

```bash
python tools/lab.py doctor
python tools/lab.py selftest
python tools/lab.py format       # 自动格式化，会修改文件
python tools/lab.py verify      # 完整测试和质量门禁
python tools/lab.py fixtures    # Checkstyle 14.4.0 正/反例 + Java 8 API 反例
python tools/lab.py check --runtime 8 # 在 JDK 21 构建，使用显式选择的 Java 8 测试和 HTTP
python tools/lab.py compile     # JDK 25 编译/打包与 Java 8 字节码审计，不跑测试
```

Mac/Linux 如果没有 `python` 命令，使用 `python3`。Windows 使用 `python`。统一入口会记录真实命令、退出码和耗时到
`.lab/runs/`。

启动唯一应用：

```bash
java -jar app/target/app-0.2.0-SNAPSHOT.jar
```

服务默认只监听 `127.0.0.1:8080`。HTTP 示例：

```bash
curl -i -X POST http://127.0.0.1:8080/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Add a regression test"}'
# 将响应中的 id 替换到下面请求
curl http://127.0.0.1:8080/api/tasks/<id>
curl -X POST http://127.0.0.1:8080/api/tasks/<id>/complete
```

真实可执行 JAR 冒烟（自动选端口、启动、验证并清理）：

```bash
python tools/http_smoke.py --jar app/target/app-0.2.0-SNAPSHOT.jar
```

应用使用内存 Map；重启丢失、没有认证、容量控制或生产级持久化。**只用于本机实验，不部署公网或生产。**

## 4. 工具链版本

| 工具                      |   固定版本 | 作用                 | 运行环境与兼容边界                            |
|-------------------------|-------:|--------------------|-----------------------------------------|
| Maven Enforcer          |  3.5.0 | 强制 Maven / JDK 下限  | 插件最低 JDK 8                              |
| Maven Compiler          | 3.13.0 | Java 8 API / 字节码目标 | JDK 21 构建，使用 --release 8         |
| Spotless Maven          | 3.11.0 | 格式化与 check         | 随构建宿主在 JDK 21 运行                   |
| Eclipse JDT Formatter   | 4.12.0 | 复用 Eclipse XML     | Eclipse 4.12 最低 JRE 8                   |
| Maven Checkstyle Plugin |  3.6.0 | Checkstyle 集成      | 插件最低 JDK 8                              |
| Checkstyle              | 14.4.0 | Java 编码规则          | 引擎要求 Java 21+   |
| ArchUnit                |  1.3.0 | 架构规则测试             | 选用 1.x 兼容线，CI 实际验证                      |
| JaCoCo                  | 0.8.14 | 覆盖率                | Agent 最低 JRE 低于 8，正式支持 Java 25 class 文件 |
| Surefire                |  3.2.5 | JUnit 执行           | 插件最低 JDK 8                              |
| Exec Maven Plugin       |  3.5.1 | 调用 Python 策略适配器    | 插件最低 JDK 8                              |

Spotless 与 Checkstyle 属于构建依赖。它们的 JDK 下限不等于应用最低 Java 版本。
当前保留 Eclipse JDT 4.12.0、现有 codestyle XML 与自动清理无用导入；升级不能删除检查或降低应用兼容验证。

## 5. 质量门禁与例外机制

| 层次   | 工具 / 机制                               | 首版处理                                    |
|------|---------------------------------------|-----------------------------------------|
| 格式   | Spotless + Eclipse JDT XML            | 必须一致；自动修复；不可豁免                          |
| 编码规范 | Checkstyle 14.4.0                        | 原始 XML 完整保留，由策略适配器裁决 error/warning      |
| 架构   | ArchUnit                              | Controller 不直接依赖 Repository/Adapter；硬失败 |
| 行为   | JUnit 5 + MockMvc                     | 状态机、HTTP 契约、并发行为；硬失败                    |
| 覆盖率  | JaCoCo                                | `domain-core` 行覆盖率 70%、分支覆盖率 60% 硬门槛    |
| 兼容性  | Compiler `release=8` + 字节码审计 + JDK 矩阵 | 所有生产/测试 class 不超过 major 52              |
| 持续治理 | baseline / waiver / policy review     | 精确、限时、可见；Agent 只能提案不能审批                 |

第一版不堆叠 P3C/PMD、SpotBugs、Error Prone 或 TCA。IDEA 的 P3C 插件可以继续作为开发反馈，但 P3C 规则尚未作为本项目构建硬门禁。后续加入前必须验证
Java 8 运行时兼容、规则增量覆盖和误报。

### Warning 与例外

- `MethodLength` 是唯一全局 advisory 规则，仍保留在报告中。
- 特定命名问题可以申请精确 waiver / baseline；只允许 `MemberName`、`MethodName`、`TypeName`、`ConstantName`、`ParameterName`、
  `LocalVariableName`。
- waiver 最长 30 天；baseline 最长 90 天。
- 每条记录绑定文件 SHA-256、规则、行号、负责人、原因、问题记录和到期日。
- 原始报告不删除 finding；策略报告把具体命中降为 warning，并保留原始 severity。
- 内容变动、过期、finding 消失、重复命中、报告缺失或漏扫都会失败。
- 格式、编译、测试、架构、空 catch、治理工具执行失败不可豁免。

唯一示例 baseline 是 `domain-core/.../LegacyCustomerRow.java` 中故意保留的 public 字段命名问题 `BASE-001`
，用于演示旧调用方迁移期间如何冻结一个历史问题。它不是全局放宽规则，过期后必须修复或重新人工审批。

## 6. Codex 工作流程

`AGENTS.md` 是工作合同，不是最终质量判定器。Agent 修改后必须：

1. 明确影响模块，不顺手改无关代码。
2. 缺陷先增加失败回归测试；新规则同时增加正例和负例。
3. `python tools/lab.py format` 修复格式。
4. `python tools/lab.py verify` 执行完整门禁。
5. `python tools/lab.py fixtures` 验证检查器没有失效。
6. HTTP 行为变更再运行 `tools/http_smoke.py`。
7. 最多自行修复 3 轮；无法收敛时交付证据和人工决策点。

Agent 不得删除测试、修改阈值、扩大 excludes、自动刷新 baseline、增加/续期 waiver
或修改门禁来制造绿色结果。规则、POM、CI、测试和抑制清单的变更需要独立人类审查，并在服务器端配置分支保护。

## 7. 旧项目迁移

不要把 Demo 直接复制进旧项目，也不要顺便升级 JDK / Spring Boot / 数据库。先选择一个模块：记录旧项目工具链 → 复用 Eclipse
XML 接 Spotless → 引入少量高确定性 Checkstyle 规则 → 建立经人工审查的存量 baseline → CI 只阻断新增问题 → 再逐步增加
ArchUnit / SpotBugs / P3C。

完整方案见 [docs/MIGRATION.md](docs/MIGRATION.md)。

## 8. CI 与可信边界

GitHub Actions 对 JDK 8 / 11 / 17 / 21 执行全量验证与 HTTP smoke；JDK 25 单独执行编译、打包和 Java 8 字节码审计，不把 Boot
2.7.18 的 JDK 25 运行时写成官方支持。

最终稳定检查名为 `quality-gate`。但文件存在不等于合并保护已启用：上传 GitHub 后仍须配置 Ruleset、required status check、真实
CODEOWNERS、独立人工审批 Environment，并禁止 Agent/Bot bypass。细节见 [docs/CI-SETUP.md](docs/CI-SETUP.md)。

## 9. 持续进化

真实失误 → 最小反例/正例 → 选择最低层有效约束 → 评估误报 → 人工审查规则变更 → 固化回归 → 使用相同 Agent 任务集复测。

“自进化”不是 Agent 自己放宽门槛，而是 Agent 可以发现并提出规则改进，维护者审批后才纳入质量体系。每次实验记录模型、Harness、任务、工具版本、基线
commit、首次通过率、修复轮数、误报和无关 Diff。
