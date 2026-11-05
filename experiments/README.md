# 实验目录

本目录不是生产源码根目录。故意违规的输入以 `.java.txt` 保存，避免正常构建永远红灯。

## 机器确定性回归

`python tools/lab.py selftest`：策略适配器的合成报告测试，不等于运行真实 Checkstyle。
`python tools/lab.py fixtures`：将输入复制到 `target/fixture-checkstyle`，调用真实、锁定版本的 Checkstyle，
逐一校验正例、负例与 warning；然后验证 Java 9 API 在 `--release 8` 下被拒绝。
业务/架构测试通过 `python tools/lab.py verify` 执行。

## Agent 行为评估

使用 tasks/ 中同一组任务，在独立 Git worktree 或临时克隆中运行，不要污染主分支。
先固定任务版本、模型、Harness、工具版本、基线 commit 和上下文，再比较：
仅文档指导、格式/静态门禁、完整门禁。每组至少重复运行；不能用一次成功宣称模型总体可靠。

每次任务的记录使用 `run-record.example.json`，命令证据来自真实工具输出，而非 Agent 的完成声明。
第一版不自动调用付费模型、不保存账号令牌、不承诺自动运行 Agent。
修复最多 3 轮，仍失败应输出根因、影响和人工决策点；不得削弱检查以结束任务。

状态：schema 和任务已经提供；尚无真实 Agent 对照实验数据。
