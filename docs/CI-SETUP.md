# CI 与合并保护：必须手工完成的部分

项目包含 GitHub Actions 工作流，但文件存在不等于仓库保护已启用。CI 使用只读 token，不使用有写权限的 `pull_request_target`
。最终稳定检查名为 `quality-gate`。

## 上传 GitHub 后

1. 设置 main Ruleset：必须 PR、必须通过 `quality-gate`，禁止 Agent 直接 push；不给 Bot bypass 权限。
2. 将 `.github/CODEOWNERS.example` 复制为真实 `.github/CODEOWNERS`，替换团队占位符并开启 required code owner review。
3. 创建 `quality-policy-review` Environment，配置独立人类审批者和 prevent self-review。
4. 开启提交后旧 approval 失效；规则、POM、测试、CI 或豁免不能由同一个 Agent 自批。
5. 通过故意违规 PR 验证门禁确实不能合并，再验证过期豁免、受保护变更和正常 PR。

政策范围判断使用 base commit 中的 `policy_guard.py`，而不是信任 PR 新改写的脚本。Environment 没有设置 required reviewers
时不会产生真正审批；CODEOWNERS 示例也不会自动生效。必须在仓库设置中完成这些步骤。

## 验证矩阵

- JDK 8 / 11 / 17 / 21：完整 `verify`、真实 Checkstyle 正反例、Java 8 API 负例、HTTP JAR smoke。
- JDK 25：`compile`，即 Maven validate、Spotless、Checkstyle、Java 8 编译、package 和字节码审计；不运行 Boot 2.7.18 应用。
- 无 `continue-on-error`。缺产物、缺测试、测试跳过、警告之外的违规，都不能获得总门禁成功。

## Jenkins / 自托管 GitLab

Jenkinsfile.example 展示一个 Java 8 worker 的 POSIX 示例。生产中建议为 JDK 8/11/17/21 建完整运行矩阵，并为 JDK 25 单独建立
compile-only job。Jenkins 构建失败本身不等于 GitLab MR 禁止合并：需要把 Job 状态接入 MR 必需检查、保护目标分支并限制 Bot
权限。

## 供应链强化

Actions 当前使用官方 major tag。正式上线前固定审查过的 commit SHA。若生成 Maven Wrapper，必须核验发行包 SHA-256 并固定
`distributionSha256Sum`。不自动安装未知远程脚本、不上传业务源码到第三方分析服务、不自动调用模型计费接口。
