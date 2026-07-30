# vNext Repair Evidence

每个修复任务只允许保存一份由`mode_p_vnext.rebuild_control`绑定的Evidence JSON。

最低结构：

~~~json
{
  "task_id": "R0.1",
  "changed_paths": [
    "01_调度器/mode_p_vnext/rebuild_control.py"
  ],
  "checks": [
    {
      "name": "task_graph",
      "command": "python -m pytest ...",
      "exit_code": 0
    }
  ]
}
~~~

`complete`会验证task_id、允许路径、required_checks、退出码和Evidence内容hash。禁止手写状态完成后再补证据。
