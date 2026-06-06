from config.settings import settings
from skills.registry_impl import register


@register("execute_python")
def execute_python(code: str) -> str:
    """在 E2B 云沙箱中执行 Python 代码"""
    # 延迟导入：未安装 e2b 时不影响其他 Skill 加载
    try:
        from e2b_code_interpreter import Sandbox
    except ImportError:
        return "ERROR: e2b-code-interpreter 未安装，无法执行代码沙箱"

    with Sandbox(api_key=settings.e2b_api_key) as sbx:
        execution = sbx.run_code(code)
        output_parts = []
        if execution.logs.stdout:
            output_parts.append("".join(execution.logs.stdout))
        if execution.logs.stderr:
            output_parts.append(f"[stderr] {''.join(execution.logs.stderr)}")
        if execution.error:
            output_parts.append(f"ERROR: {execution.error.name}: {execution.error.value}")
        return "\n".join(output_parts) if output_parts else "(无输出)"
