# requests 最佳实践

✅ 推荐模式：
- 总是设置 `timeout=(3, 10)`（连接+读取）
- 使用 `session` 复用连接（尤其多请求时）
- 检查 `response.raise_for_status()` 或显式判断 `status_code`
- JSON 响应优先用 `.json()`，避免手动 `json.loads(response.text)`
- 上传文件用 `files={"file": open(...)}`, 自动设 `Content-Type`

⚠️ 避免：
- 不设 timeout → 可能永久阻塞
- 忽略 SSL 验证（`verify=False`）→ 仅调试时临时启用
- 直接拼接 URL 参数 → 应用 `params=` 字典

🔧 示例模板：
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def get_with_retry(url, params=None, timeout=(3, 10)):
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session.get(url, params=params, timeout=timeout)
```
