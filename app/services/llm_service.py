from llm import chat

def execute_analysis(prompt):
    try:
        result = chat(prompt)
        return result
    except Exception as e:
        print(f"[LLM分析] 执行出错: {e}")
        return f"分析失败: {str(e)}"
