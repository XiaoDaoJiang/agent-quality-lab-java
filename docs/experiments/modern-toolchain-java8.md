# 现代构建工具与 Java 8 产物实验

分支：`explore/modern-toolchain-java8`，起点：`db6b386`。日期：2026-11-06。

结论：在本机已跑通“构建工具使用 JDK 21，应用与测试保持 Java 8”的组合；
JDK 25 也完成编译，产物可在 Java 8 上执行 HTTP 冒烟。该结论属于下面列出的实验版本与运行条件。

## 设计与范围

选择显式 Maven profile，保留默认链路作为对照。另一种方案是直接替换默认版本并改造全部 CI；
本轮先验证可行性，默认切换留待独立政策审查。应用最低版本不因构建宿主改变。

| 层次 | 本轮选择 | 验收方式 |
|---|---|---|
| Maven 宿主 | 本机 Oracle JDK 21.0.11；额外编译宿主 25.0.4.1 | 独立环境快照与原始命令 |
| Maven | 3.9.11；实验配置要求 `[3.9.11,4)` | Enforcer；不使用 Maven 4 |
| Spotless | 2.30.0 → **3.11.0**；内置导入清理器使用 google-java-format 2.0.0 | 真实 apply/check、有效/无用导入探针 |
| Checkstyle | 9.3 → **14.4.0** | 原始 XML、策略适配、7 个正反例 |
| 排版引擎 | Eclipse JDT 4.12.0 与现有 codestyle XML | 本轮 Java 文件零变更 |
| 其余插件、应用与测试依赖 | 保持既有版本，包括 Boot 2.7.18、Compiler 3.13.0、Surefire 3.2.5、ArchUnit 1.3.0、JaCoCo 0.8.14 | 全量构建与真实运行 |
| 源码、API、生产/测试字节码 | Java 8，`release=8`，class major 52 | 字节码审计及 Java 9 API 反例 |
| Surefire 测试 JVM | 8u202、11.0.24、17.0.10、21.0.11 | 各 33 项 Java 测试、报告中的实际 JVM 属性 |
| HTTP JVM | 同上四个运行时 | 各执行 6 项 HTTP 断言 |

Spotless 3.x 的插件运行时下限升为 Java 17，Checkstyle 14.x 要求 Java 21；
因此本轮实验构建下限取 21，而不是继续要求新版检查器在 Java 8 上启动。
来源：[Spotless 发布记录](https://github.com/diffplug/spotless/blob/main/plugin-maven/CHANGES.md)、
[Checkstyle JRE 要求](https://checkstyle.org/#JRE_and_JDK)。Maven Central 元数据与下载日志另存于证据目录。

保留 `<removeUnusedImports/>`、全部既有规则、阈值、baseline 内容与豁免策略。
没有采用已撤回的移除导入清理步骤补丁；默认工具链的 TOOLCHAIN-001 仍然开放。

## 执行入口

使用已验证的 mise 2026.11.2，并先完成 `mise install --locked` 或配置本机覆盖。
两个新任务继续复用本机 JDK 21/25 路径；共享配置使用锁定的公开发行版本。

```text
mise run modern:check
mise run modern:compile:25
```

`modern:check` 在 JDK 21 执行完整 verify 与新版 fixtures，再用 Java 8 冒烟刚生成的 JAR。
`modern:compile:25` 只编译、打包与审计；不在 JDK 25 上执行应用测试或启动应用。

进入已正确设置 JAVA_HOME、PATH、LAB_EXPECTED_JAVA 等变量的 JDK 21 构建环境后，可直接使用统一 Python 入口：

```text
python tools/lab.py format --profile modern-toolchain
python tools/lab.py verify --profile modern-toolchain --test-java "<JDK8>/bin/java"
python tools/lab.py fixtures --profile modern-toolchain
```

Windows 的 `--test-java` 需填写实际 `java.exe`。更换该路径即可测试 11/17/21。
该参数只用于 verify：探测实际 JVM、拒绝缺失/无效 JVM 及 Java 25，然后传入 Surefire 的显式 JVM 路径和预期运行时。
测试源码仍由构建宿主通过 `--release 8` 编译；`BytecodeCompatibilityTest` 比较实际测试 JVM 与预期运行时。
配置依据：[Surefire 不同 JVM 执行测试](https://maven.apache.org/surefire/maven-surefire-plugin/examples/toolchains.html)。

fixtures 必须带同一个 profile，否则只代表默认 Checkstyle 9.3。新增回归保证未知或缺失版本的 profile 硬失败，
避免用旧引擎的结果冒充新版验收。真实输出包含 engine 与 profile。

## 实测结果

| 构建宿主 | 测试/HTTP JVM | verify | fixtures（宿主上） | 字节码 | HTTP |
|---|---|---|---|---|---|
| 21.0.11 | 8u202 | 0；33 项 Java 测试 | 0；7 个正反例 + Java 8 API 反例 | 52 | 0；6 项断言 |
| 21.0.11 | 11.0.24 | 0；33 项 Java 测试 | 0；同上 | 52 | 0；6 项断言 |
| 21.0.11 | 17.0.10 | 0；33 项 Java 测试 | 0；同上 | 52 | 0；6 项断言 |
| 21.0.11 | 21.0.11 | 0；33 项 Java 测试 | 0；同上 | 52 | 0；6 项断言 |
| 25.0.4.1 | 不执行测试；HTTP 使用 8u202 | compile=0 | 构建内检查通过 | 52 | 0；6 项断言 |

每个完整 verify 还执行 56 项 Python 治理回归。保留 BASE-001 的既有 scoped warning；没有扩大例外。
`mise run modern:check` 实际退出 0；原有默认 `mise run check:8` 也退出 0，覆盖默认 POM 行为与新增导入 fixtures。
额外负例：JDK 17 执行实验 profile 在 Enforcer 被拒绝（退出 1）；`--test-java` 指向 Java 25 被入口拒绝（退出 1）。
隔离导入探针中，新版 Spotless 删除无用 `List` 导入并保留实际使用的 `List` 导入，命令退出 0。

本轮第一条格式化命令被本机企业 Maven mirror 的 HTTP 401 阻断（退出 1），不是插件兼容性通过。
随后显式指定独立 Maven Central settings 执行；未改用户的全局 Maven 配置。
该 settings、MAVEN_ARGS、所有真实命令、退出码、环境快照、报告与 JAR SHA-256 保存在
`.lab/modern-toolchain-20261106/`。企业镜像使用者需要确保新发行包可获取，或显式选择自己的有效 settings；
本轮仓库下载条件不代表企业 mirror 已恢复。

补收原始报告时，单独执行 `checkstyle:checkstyle` 曾因 reactor 内 `domain-core` 尚未 install 而在 app 依赖解析阶段失败。
该命令退出 1 的记录保留；随后使用完整 `verify` 重新生成并归档两模块的新版原始报告，没有把这次工具执行失败记作规则通过。

## 交付边界

这是可复现命令及本机运行证据，不代表已切换默认版本、完成远程 CI 或通过独立人类政策审查。
Linux/macOS、全新机器初始化、IDE 内格式化比较为 NOT_RUN。既有 CI 仍运行默认配置，不能用本实验宣称 CI 全绿。
提高构建宿主无法使 Boot 2.7.18 自动获得新的维护或安全支持；生产迁移需要另行评估。

下一步应先独立审查本分支，在 CI 中复制“现代构建宿主 × 旧测试运行时”矩阵；
随后再决定是否把实验 profile 变为默认，或继续维护两条构建方式。
