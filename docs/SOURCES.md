# 技术依据（当前工具链采用日期 2026-11-06）

以下官方资料用于核对工具与 Java 版本边界；它们不代表本 Demo 已在目标环境全部运行通过。

- Spring Boot 2.7.18 系统要求（Java 8 起、兼容至 Java
  21）：https://docs.spring.io/spring-boot/docs/2.7.18/reference/html/getting-started.html
- Spring Boot 2.7.18 发布及开源支持状态：https://spring.io/blog/2023/11/23/spring-boot-2-7-18-available-now/
- Maven Compiler Plugin 3.13.0 与 JDK 8 的 release/source/target
  行为：https://maven.apache.org/plugins-archives/maven-compiler-plugin-3.13.0/examples/set-compiler-release.html
- Maven Plugin Java 8 兼容策略：https://maven.apache.org/developers/compatibility-plan.html
- Maven Checkstyle Plugin 3.6.0 系统要求：https://maven.apache.org/plugins/maven-checkstyle-plugin/plugin-info.html
- Checkstyle 14.x 构建运行时下限 Java 21：https://checkstyle.org/#JRE_and_JDK
- Maven Checkstyle Plugin 3.6.0 最低 JDK 8：https://maven.apache.org/plugins/maven-checkstyle-plugin/plugin-info.html
- Spotless Maven 3.11.0 与历史版本发布记录：https://github.com/diffplug/spotless/blob/main/plugin-maven/CHANGES.md
- Eclipse 4.12 最低 Java SE 8：https://eclipse.dev/eclipse/development/readme_eclipse_4.12.html
- ArchUnit：https://www.archunit.org/userguide/html/000_Index.html
- JaCoCo 0.8.14 / Java 25 支持：https://www.jacoco.org/jacoco/trunk/doc/changes.html
- Maven Surefire 3.2.5
  系统要求：https://maven.apache.org/surefire-archives/surefire-3.2.5/maven-surefire-plugin/plugin-info.html
- Maven Exec Plugin 系统要求：https://www.mojohaus.org/exec-maven-plugin/plugin-info.html

规则配额、TTL、覆盖率门槛、域模型和审批流程是此试验田的设计选择，不声称是任何大厂统一规范。
