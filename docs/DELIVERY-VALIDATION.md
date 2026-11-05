# 本次修订的验证边界

日期：2026-11-05。修订目标：将原先的 `app-modern` / `app-legacy` 双应用结构收敛为**单一 Spring Boot 应用，所有代码与工具链最低兼容 Java 8+**。

## 已完成的静态修订

- 删除 `app-modern`、`app-legacy` 两套应用，建立唯一 `app` 模块。
- `domain-core` 与 `app` 统一 `maven.compiler.release=8`。
- Spring Boot 统一为 2.7.18；不再出现 Boot 3.x / Java 17 的应用模块。
- 工具链降到 Java 8 可运行的兼容版本线：Spotless Maven 2.30.0、Eclipse JDT 4.12.0、Checkstyle 9.3、Maven Checkstyle Plugin 3.6.0、Compiler 3.13.0、Surefire 3.2.5、Enforcer 3.5.0、ArchUnit 1.3.0、JaCoCo 0.8.14、Exec Maven Plugin 3.5.1。
- Maven Enforcer 下限为 JDK 8 / Maven 3.6.3；根 POM 固定 Java 8 编译目标。
- CI 改为 JDK 8 / 11 / 17 / 21 完整验证，JDK 25 compile-only。
- `audit_results.py` 检查生产和测试字节码均不超过 major 52。
- 取消双应用/Java8 Toolchain Profile；用 CI 的真实 JDK 矩阵运行同一应用。

## 本次实际执行并通过

- 尚未执行真实 Maven 构建、真实 Spotless/Checkstyle/ArchUnit/JaCoCo 测试、Spring Boot 启动或 JDK 8/25 矩阵。
- 当前执行容器只有 JDK 21，没有 Maven；因此不能声称上述修订已经在 Java 8 和 JDK 25 上跑通。
- 本轮应先执行 Python 策略自测、XML/JSON 结构校验、Java 源码静态扫描和 JDK 21 `javac --release 8` 核心编译；这些只能算部分验证。

## 必须在目标环境完成

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

## 本次修订后已实际执行的离线验证

| 检查 | 结果 |
|---|---|
| Python 策略与受保护路径测试 | 39 项通过 |
| 无 Maven 的核心离线 smoke | 79 次断言通过，运行于本环境 JDK 21.0.12.1 |
| 核心模块 Java 8 字节码 | `javac --release 8` 实测 major version 52 |
| Java 9 API 负例 | `List.of` 在 Java 8 编译目标下被拒绝 |
| POM / XML / JSON 结构 | 通过 |
| Java package 与目录结构 | 22 个 Java 源文件通过 |
| Java 8 API 简单静态扫描 | 通过 |

这些结果不能替代 Maven、真实静态检查器、Spring Boot HTTP、JDK 8 运行时或 JDK 25 compile-only 验证。
