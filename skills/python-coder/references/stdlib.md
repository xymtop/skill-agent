# Python 标准库速查（高频模块）

| 模块 | 典型用途 | 示例 |
|------|----------|------|
| `os` / `pathlib` | 路径操作 | `Path("data/").glob("*.csv")` |
| `sys` | 程序参数、退出 | `sys.argv[1:]`, `sys.exit(1)` |
| `argparse` | CLI 参数解析 | `parser.add_argument("--input", type=str)` |
| `json` | JSON 读写 | `json.load(f)`, `json.dumps(obj, indent=2)` |
| `csv` | CSV 处理 | `csv.DictReader`, `csv.writer` |
| `datetime` | 时间处理 | `datetime.now().strftime("%Y-%m-%d")` |
| `logging` | 日志记录 | `logging.info("Started")`, `%(levelname)s` |
| `itertools` | 迭代器工具 | `chain()`, `groupby()` |
| `functools` | 高阶函数 | `@lru_cache`, `partial()` |
