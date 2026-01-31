# PEP8 精要（供 python-coder 参考）

- 行宽 ≤ 79 字符（文档字符串/注释可 ≤ 72）
- 函数/类名：`snake_case`；常量：`UPPER_SNAKE_CASE`；类名：`PascalCase`
- 每个导入独占一行：`import os`、`from sys import argv` ✅；`import os, sys` ❌
- 顶层函数/类间空 2 行，方法间空 1 行
- 运算符两侧加空格：`x = y + z` ✅；`x=y+z` ❌
- 布尔比较用 `is`/`is not`，不用 `==`/`!=` 判定 `None`
- 字符串拼接优先用 f-string（Python ≥3.6）
- 使用 `if __name__ == "__main__":` 封装可执行入口
