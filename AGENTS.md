# AGENTS.md

本仓库的操作说明在 **[README.md](README.md)**,请先完整读它再动手。

最短路径(三条命令):

    python3 doctor.py                                  # 环境自检,缺什么按提示装
    python3 plan.py   <plan.json>                      # 校验《出图清单》
    python3 build.py  <plan.json>                      # 逐图:校验 → 渲染 → 验收

人的使用说明在 `使用说明.md`(给用户,不用读给 agent 听)。
