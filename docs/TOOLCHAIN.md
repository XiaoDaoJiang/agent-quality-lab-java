# 工具版本与 Java 8+ 兼容

版本以根 `pom.xml` 为准，禁止使用 LATEST 或动态版本范围。Checkstyle 9.3 官方兼容页确认最低 JRE 8，已确认 JDK 8–17；JDK 25
可能兼容但需 CI 实测。

## 基线

- 应用：Spring Boot 2.7.18，最低 Java 8，官方兼容至 Java 21；已结束开源维护，仅作实验与旧系统迁移样例。
- 所有源码和测试：`maven.compiler.release=8`；在 JDK 8 上 Maven Compiler Plugin 3.13.0 自动使用 source/target 1.8，在 JDK
  9+ 使用 `--release 8`。
- Maven：3.6.3–3.x，推荐 3.9.11；Maven 4 不纳入 Java 8 兼容线。
- 完整运行测试：JDK 8、11、17、21。
- JDK 25：仅 compile/package + bytecode audit；不在 JDK 25 启动 Boot 2.7.18 应用。
- Python 3.10+ 是独立仓库治理工具，不进入 Java 应用运行时。

## 固定工具

| 组件                      |     版本 | Java 8+ 兼容说明                              |
|-------------------------|-------:|-------------------------------------------|
| Maven Enforcer          |  3.5.0 | 最低 JDK 8                                  |
| Maven Compiler          | 3.13.0 | 最低 JDK 8；JDK 8 回退 source/target           |
| Spotless Maven          | 2.30.0 | JRE 8 兼容线；更新版本需 JRE 17                    |
| Eclipse JDT             | 4.12.0 | Eclipse 4.12 最低 JRE 8                     |
| Maven Checkstyle Plugin |  3.6.0 | 最低 JDK 8                                  |
| Checkstyle              |    9.3 | 最低 JRE 8；官方确认 JDK 8–17，JDK 25 待 CI 实测     |
| ArchUnit                |  1.3.0 | 1.x Java 8 兼容线，仍须由 CI 真实验证                |
| JaCoCo                  | 0.8.14 | Agent/工具最低 JRE 低于 8，正式支持 Java 25 class 文件 |
| Surefire                |  3.2.5 | 最低 JDK 8                                  |
| Exec Maven Plugin       |  3.5.1 | 最低 JDK 8                                  |

## 验证矩阵

```bash
# 在 JDK 8 / 11 / 17 / 21 环境分别执行
python tools/lab.py verify
python tools/lab.py fixtures
python tools/http_smoke.py --jar app/target/app-0.2.0-SNAPSHOT.jar

# 在 JDK 25 环境只编译、打包并审计 Java 8 字节码
python tools/lab.py compile
```

Maven 3.9.11 本身可运行于 Java 8+。如果企业镜像要求固定 Maven 发行包，需生成官方 Wrapper 并核验 SHA-256 后提交；当前仓库不伪造
Wrapper 脚本。

升级工具时分别核对：插件自身运行 JDK、Maven 最低版本、Formatter/Analyzer 的语言解析能力、应用目标 Java 版本。`--release 8`
只能证明编译器 API/字节码目标，不代表第三方工具链也能在 Java 8 上运行。
