# TOOLCHAIN-001：Spotless 未使用导入清理器在 JDK 21 失败

状态：旧链问题已复现；当前默认链已通过版本升级修复本机兼容性，IDEA 实操样例通过；独立人审与远程 CI 以 PR 状态为准。
2026-11-06 用户先要求记录差异、撤回移除清理步骤的候选；随后明确要求提交实验并采用新版默认工具链。

## 当前处理

实验检查点 `daacc5b` 验证 JDK 21 构建、Spotless 3.11.0、Checkstyle 14.4.0，应用与测试保持 Java 8。
当前已将该组合设为唯一默认，保留 `<removeUnusedImports/>`、规则、阈值和 baseline。
普通 `check`/`matrix` 不再需要 profile；JDK 21 构建与 Java 8/11/17/21 测试、HTTP 分离。
实测证据见 DELIVERY-VALIDATION.md 当前章节；下文保留旧版本故障及撤回决定，不能据此认为旧版本已修复。

## 现象与范围

2026-11-05 至 2026-11-06 的本机验收中，原工作区在 Oracle JDK 8u202、Temurin 11.0.24 和
17.0.10 上完整通过；Zulu 21.0.13.0.3 的 `format` 和 `verify` 均以退出码 1 失败。
Zulu 25.0.5.0.3 的 compile-only 通过。这不构成 Java 8–21 完整矩阵通过。

原始错误来自 Spotless 2.30.0 的 `removeUnusedImports` 步骤，而非 Eclipse JDT 4.12.0 排版引擎：

```text
java.lang.NoSuchMethodError:
  'com.sun.tools.javac.tree.JCTree
   com.sun.tools.javac.tree.JCTree$JCImport.getQualifiedIdentifier()'
at com.google.googlejavaformat.java.RemoveUnusedImports.getSimpleName
```

使用本机 `javap -p` 检查 `JCTree$JCImport`：JDK 17 有返回 `JCTree` 的方法；JDK 21
只有返回 `JCFieldAccess` 和 `Tree` 的方法；JDK 25 又包含返回 `JCTree` 的桥接方法。
这与本轮 17/21/25 的实际运行结果一致，不应通过提高应用 Java 基线解决。

## 最小复现

隔离样例只配置 Spotless 2.30.0 的 `<java><removeUnusedImports/></java>`，输入为：

```java
import java.util.List;
class Probe { List<String> values; }
```

在 JDK 21 下执行以下命令，退出码 1，并出现同一个 `NoSuchMethodError`：

```powershell
$env:JAVA_HOME = (Resolve-Path '.lab/acceptance-20261105/toolchains/zulu21.54.109-ca-jdk21.0.13.0.3-win_x64').Path
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
mvn -B -f .lab/acceptance-20261105/minimal-jdk21/pom.xml spotless:apply
```

原始证据：`.lab/acceptance-20261105/jdk21-minimal-repro/`、`jdk21-format/`、`jdk21-verify/`，
以及 `javac-{17,21,25}-JCImport.txt`。日志和退出码分开保留，预期复现失败不计为门禁通过。

## 差异处理决定

2026-11-06 用户明确要求：先记录这项差异，不直接绕过。

- 保留实际工作区的 `<removeUnusedImports/>`、Checkstyle 规则和原有质量门槛。
- 不通过移除自动清理步骤、关闭检查、扩大排除范围或新增豁免来制造通过结果。
- 当前 JDK 21 的 format/verify 继续视为失败，本问题保持开放。
- 后续应寻找保留自动清理能力、同时满足 Java 8 基线的兼容方案，再独立审查与验证。

此前移除清理步骤的隔离实验仅提供故障定位证据，不再作为待采用的修复。
其矩阵和阻断试验结果保留在 [DELIVERY-VALIDATION.md](../DELIVERY-VALIDATION.md)，
原补丁及源码快照保存在 `.lab/acceptance-20261105/evidence.zip` 中。
该归档是决定之前的历史快照，其中“待审候选”等状态已由本文取代。

## 副本清理（待执行）

保留原始失败日志、命令与退出码、报告、最小复现、初始工作区快照和完整证据归档。
计划清理三个可重建的隔离项目副本（formatter-jdk8、formatter-jdk25、proposal/workspace），
以及已收录归档的重复候选源码快照、未采用补丁的活动副本和临时缓存。
便携 JDK 21/25 及下载元数据保留，便于继续复现；重复下载 ZIP 可清理。
自动审批检查拒绝删除命令（`blocked by policy`，无更具体原因），尚未删除任何副本。
待清理清单和字节数见 `.lab/acceptance-20261105/cleanup-20261106.json`。

## 关闭条件

1. 明确不削减自动清理能力的兼容修复方案，遵循 Java 8 基线和独立人类政策/验收审查。
2. 在实际工作区以 JDK 21 执行全部构建门禁，将全量测试与 HTTP 交给 Java 8/11/17/21，并完成 JDK 25 compile-only。
3. 补完 IDE 内实际格式化比较，更新真实命令、退出码和报告；历史隔离实验不能替代这些验收。
