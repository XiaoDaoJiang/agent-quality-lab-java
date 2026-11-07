# 下一步交给 Codex 的任务

先阅读 `AGENTS.md`、`README.md`、`docs/TOOLCHAIN.md` 和 `docs/DELIVERY-VALIDATION.md`。

## 任务

在真实开发机上验收当前默认工具链：JDK 21+ 构建、Java 8 应用与测试目标，不拆分 Spring Boot 应用，不放宽门禁。
旧链首次验收与阻断记录保留在 `docs/DELIVERY-VALIDATION.md`；实验检查点为 `daacc5b`。

1. 在 JDK 21 执行 `mise run matrix`：分别用 Java 8、11、17、21 运行全部 Surefire 测试与 HTTP，每个通道都执行完整构建和 fixtures。
2. 在 JDK 25 执行 `python tools/lab.py compile`，确认所有生产和测试字节码不超过 major 52。
3. 比较当前 Spotless 3.11.0 + Eclipse JDT 4.12.0 在构建 JDK 21/25 的输出，并补完 IDEA EclipseCodeFormatter 实际操作对比；历史引擎探针不代替 IDE 验证。
4. 验证 Checkstyle 14.4.0 在构建宿主正常执行，7 个真实正反例与 Java 8 API 反例通过。
5. 工具启动失败先定位原因；构建工具 JDK 下限与应用 Java 8 下限独立处理，不要求新版检查器在 Java 8 启动。
6. 所有修复必须附命令、退出码、原始日志、测试报告和 Diff；更新 `docs/DELIVERY-VALIDATION.md`。

本机验收已完成：默认矩阵通过；Spotless 3.11.0 + JDT 4.12.0 在 JDK 21/25 的 26 个文件输出逐字节一致。
用户在 IDEA 中手动格式化并保存隔离样例；该文件与 JDK 21 下的 Spotless 输出逐字节一致。证据见 `docs/DELIVERY-VALIDATION.md`。
远程 CI 与独立政策/验收审查仍待完成，合并门禁保持原要求。不得将本文件标记为全部完成。

## 不允许

- 不允许将 `maven.compiler.release` 改为 17。
- 不允许增加 app-modern / app-legacy 双应用。
- 不允许把 JDK 25 compile-only 描述为 Boot 2.7.18 的官方运行时支持。
- 不允许跳过测试、删除检查、扩大 excludes、自动更新 baseline/waiver。
- 不允许仅凭编译成功就宣称 Java 8 运行时兼容。
