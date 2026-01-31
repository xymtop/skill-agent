# pytest 单元测试模板

## 基础结构
```python
# test_example.py
import pytest

def test_function_returns_expected():
    assert my_func(2, 3) == 5

def test_raises_on_invalid_input():
    with pytest.raises(ValueError):
        my_func(-1, 0)
```

## 常用装饰器
- `@pytest.mark.parametrize("a,b,expected", [(1,2,3), (0,0,0)])` → 参数化测试
- `@pytest.mark.skip(reason="WIP")` / `@pytest.mark.xfail` → 跳过或预期失败
- `@pytest.fixture` → 复用测试资源（如临时文件、mock session）

## 运行建议
- `pytest -v`：详细输出
- `pytest test_module.py::test_name`：运行单个测试
- `pytest --cov=my_module`：代码覆盖率（需安装 pytest-cov）
