from llm.prompt.setting_prompt import identity,identity_desgin,chat_style,tool


system_prompt = f"""
""你的身份是""：{identity}
""角色设定""：{identity_desgin}
""回复风格""：{chat_style}
""可以使用的工具有""：{tool}
"""
