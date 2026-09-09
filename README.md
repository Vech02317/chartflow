# chartflow — 契约驱动的图表流水线

一句话目标:把「模型代码 → schema.json 数据契约 → 确定性渲染 → 自动验收」做成一条可复用链路,先打通 ER 图。

运行方式(在项目根):

    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # 首次
    python3 run.py                                                         # 校验 → 渲染 → 验收

产出在 out/,验收结果在 out/check_report.txt。

当前范围:v1 只做 ER 一条链路(源 = 样本 Django models);用例图/流程图后续加渲染器扩展。
