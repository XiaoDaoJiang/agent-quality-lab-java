# 下一步交给 Codex 的任务

先阅读 `AGENTS.md`、`README.md`、`docs/TOOLCHAIN.md` 和 `docs/DELIVERY-VALIDATION.md`。

## 任务

在真实开发机上完成 Agent Quality Lab 的首次工具链验收，不升级 Java 最低版本，不拆分 Spring Boot 应用，不放宽任何门禁。

1. 在 JDK 8、11、17、21 环境分别执行 `python tools/lab.py doctor`、`verify`、`fixtures` 和 `http_smoke.py`。
2. 在 JDK 25 执行 `python tools/lab.py compile`，确认所有生产和测试字节码不超过 major 52。
3. 验证 Spotless 2.30.0 + Eclipse JDT 4.12.0 在 JDK 8 与 JDK 25 上行为一致；与 IDEA EclipseCodeFormatter 对比。
4. 验证 Checkstyle 9.3 在所有 CI JDK 上能正常运行，真实负例能被检出。
5. 如果某个工具版本无法在 Java 8 启动，先定位最小原因，寻找仍支持 Java 8 的兼容版本；不得通过升级应用最低 Java 版本解决。
6. 所有修复必须附命令、退出码、原始日志、测试报告和 Diff；更新 `docs/DELIVERY-VALIDATION.md`。

## 不允许

- 不允许将 `maven.compiler.release` 改为 17。
- 不允许增加 app-modern / app-legacy 双应用。
- 不允许把 JDK 25 compile-only 描述为 Boot 2.7.18 的官方运行时支持。
- 不允许跳过测试、删除检查、扩大 excludes、自动更新 baseline/waiver。
- 不允许仅凭编译成功就宣称 Java 8 运行时兼容。
