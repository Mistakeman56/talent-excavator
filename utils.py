from flask import jsonify

# 业务错误码
ERR_NOT_LOGGED_IN = 1001      # 未登录
ERR_PERMISSION_DENIED = 1002  # 权限不足
ERR_NOT_FOUND = 1004          # 资源不存在
ERR_INVALID_PARAMS = 1005     # 参数无效

def api_error(code, message, http_status=200):
    return jsonify({"success": False, "error_code": code, "error": message}), http_status
