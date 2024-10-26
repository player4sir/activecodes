
# 激活码 API 文档

**版本:** 1.0.0  
**描述:** 提供生成、验证和检查特定产品激活码的 API。

## 基础 URL

```plaintext
http://your-domain.com
```

## 认证

- `/admin` 路由需要通过 `verify_api_key` 依赖进行 API 密钥认证。
- 客户端路由不需要 API 密钥。

---

## 接口

### 健康检查

#### `GET /health`

检查 API 的健康状态。

**响应:**

- **状态码:** `200 OK`
- **响应体:**
  ```json
  {
    "status": "healthy"
  }
  ```

---

### 管理端接口 (需要 API Key)

#### `POST /admin/generate`

生成一个新的激活码，用于指定产品。

- **请求体** (`ActivationCodeCreate`):
  ```json
  {
    "product_type": "string",
    "price": "float"
  }
  ```

- **响应** (`ActivationCodeResponse`):
  - **状态码:** `201 Created`
  - **响应体:**
    ```json
    {
      "code": "string",
      "product_type": "string",
      "price": "float",
      "expiry": "datetime",
      "created_at": "datetime"
    }
    ```

#### `GET /admin/status/{code}`

检查特定激活码的状态。

- **路径参数:**
  - `code` (string): 要检查的激活码。

- **响应:**
  - **状态码:** `200 OK`
  - **响应体:**
    ```json
    {
      "code": "string",
      "product_type": "string",
      "used": "boolean",
      "expired": "boolean"
    }
    ```
  - **错误响应:**
    - **404 Not Found:** 如果激活码不存在。
      ```json
      {
        "detail": "Code not found"
      }
      ```

---

### 客户端接口 (不需要 API Key)

#### `POST /validate`

验证并兑换指定产品类型的激活码。

- **请求体** (`ActivationRequest`):
  ```json
  {
    "code": "string",
    "product_type": "string"
  }
  ```

- **响应:**
  - **状态码:** `200 OK`
  - **响应体:**
    ```json
    {
      "message": "Activation code is valid",
      "status": "success",
      "product_type": "string",
      "price": "float"
    }
    ```

  - **错误响应:**
    - **404 Not Found:** 如果激活码对指定产品无效。
      ```json
      {
        "detail": "Invalid activation code for this product"
      }
      ```

    - **400 Bad Request:** 如果激活码已过期或已使用。
      ```json
      {
        "detail": "Activation code has expired"
      }
      ```

      ```json
      {
        "detail": "Activation code has already been used"
      }
      ```
### 启动命令
```bash
uvicorn main:app --reload
```
    