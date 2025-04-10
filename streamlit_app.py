import streamlit as st
from hello_steam.client import SteamClient

def deauth_all(username, password, steam_guard_code, proxy=None):
    client = SteamClient(proxy=proxy)
    client.login(username=username, password=password, steam_guard_code=steam_guard_code)
    result = client.deauth_all_devices()
    return result

st.title("Steam 登出所有设备 hello-steam Online Demo")
st.warning("""
⚠️ 重要提示：
1. 必须已绑定手机令牌才能使用
2. 本程序仅为技术演示，不承担账号安全责任
3. 操作不可逆，请谨慎使用
""")

# 创建输入表单
with st.form("auth_form"):
    username = st.text_input("Steam 用户名")
    password = st.text_input("Steam 密码", type="password")
    steam_guard_code = st.text_input(
        "手机令牌验证码",
        help="Steam Mobile 应用生成的 5 位数字"
    )
    http_proxy = st.text_input("HTTP 代理", help="可选，格式：`http://username:password@host:port`")
    https_proxy = st.text_input("HTTPS 代理", help="可选，格式：`http://username:password@host:port`")
    submitted = st.form_submit_button("立即撤销所有设备授权")

# 表单提交后执行
if submitted:
    if not all([username, password, steam_guard_code]):
        st.error("❌ 请填写所有输入项")
    else:
        try:
            with st.spinner("正在安全撤销设备授权..."):
                if http_proxy or https_proxy:
                    proxy = {
                        "http": http_proxy,
                        "https": https_proxy
                    }
                else:
                    proxy = None
                result = deauth_all(username, password, steam_guard_code, proxy)
                
            if result.get("success"):
                st.success("✅ 所有设备授权已撤销！")
                st.json({
                    "新登录设备": result.get("new_authorized_device"),
                    "剩余授权设备": result.get("remaining_devices", 0)
                })
            else:
                st.error(f"❌ 操作失败: {result.get('message', '未知错误')}")
                
        except Exception as e:
            st.exception(f"⚠️ 发生意外错误: {str(e)}")
            st.error("请检查网络连接或稍后重试")

# 安全警告
st.caption("""
🔒 安全声明：本页面不会存储您的任何凭据，所有操作通过 Steam 官方 API 实时完成。
代码开源于 [GitHub](https://github.com/PaffCream/hello-steam-revoke-demo)
""")