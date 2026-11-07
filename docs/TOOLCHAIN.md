# 工具版本与 Java 8+ 兼容

默认工具链现为 Spotless 3.11.0、Checkstyle 14.4.0、构建 JDK 21+、Maven 3.9.11–3.x；应用和测试仍使用 `release=8`。
不再使用版本选择 profile。采用依据保留在提交 `daacc5b` 和 [历史实验报告](experiments/modern-toolchain-java8.md)。

版本以根 `pom.xml` 为准，禁止使用 LATEST 或动态版本范围。Checkstyle 14.x 要求 Java 21+；
构建工具的运行下限与应用 Java 8 基线分别验证。

## 基线

- 应用：Spring Boot 2.7.18，最低 Java 8，官方兼容至 Java 21；已结束开源维护，仅作实验与旧系统迁移样例。
- 所有源码和测试：`maven.compiler.release=8`；Compiler 3.13.0 在 JDK 21+ 使用 `--release 8`。
- Maven：3.9.11–3.x；构建宿主默认 JDK 21；不使用 Maven 4。
- 完整运行测试：Java 8、11、17、21；通过 Surefire 显式 JVM 路径与构建宿主分离。
- JDK 25：仅 compile/package + bytecode audit；不在 JDK 25 启动 Boot 2.7.18 应用。
- Python 3.10+ 是独立仓库治理工具，不进入 Java 应用运行时。

## 固定工具

| 组件                      |     版本 | Java 8+ 兼容说明                              |
|-------------------------|-------:|-------------------------------------------|
| Maven Enforcer          |  3.5.0 | 最低 JDK 8                                  |
| Maven Compiler          | 3.13.0 | 构建 JDK 21，API 和字节码目标为 8                 |
| Spotless Maven          | 3.11.0 | 插件 3.x 要求 Java 17+；本项目使用 JDK 21/25       |
| Eclipse JDT             | 4.12.0 | Eclipse 4.12 最低 JRE 8                     |
| Maven Checkstyle Plugin |  3.6.0 | 最低 JDK 8                                  |
| Checkstyle              | 14.4.0 | 要求 Java 21+；只在构建宿主执行                    |
| ArchUnit                |  1.3.0 | 1.x Java 8 兼容线，仍须由 CI 真实验证                |
| JaCoCo                  | 0.8.14 | Agent/工具最低 JRE 低于 8，正式支持 Java 25 class 文件 |
| Surefire                |  3.2.5 | 最低 JDK 8                                  |
| Exec Maven Plugin       |  3.5.1 | 最低 JDK 8                                  |

## 验证矩阵

```bash
# 在 JDK 21 构建，分别使用 Java 8 / 11 / 17 / 21 执行全量测试和 HTTP
mise run matrix

# 在 JDK 25 环境只编译、打包并审计 Java 8 字节码
python tools/lab.py compile
```

统一入口显式使用 `config/maven/settings.xml` 中的公共 Maven Central；不依赖实验目录或用户企业镜像。
企业仓库可通过 `LAB_MAVEN_SETTINGS` 指定有效 settings，文件缺失硬失败。用户全局配置不会被改写。
直接执行 Maven 时也应显式传入该 settings 或自己的有效配置；不伪造 Wrapper 脚本。

升级工具时分别核对：插件自身运行 JDK、Maven 最低版本、Formatter/Analyzer 的语言解析能力、应用目标 Java 版本。`--release 8`
只能证明编译器 API/字节码目标，仍须验证 Java 8 的真实测试和 HTTP；不要求新版构建工具在 Java 8 启动。
