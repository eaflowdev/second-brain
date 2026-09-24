def build_system_prompt(role: str, instructions: list[str], constraints: list[str], output_format: str) -> str:
    """Common template for every agent's system prompt: a clear persona, a list
    of what to do, a list of what never to do, and the expected output shape.
    Structured sections (vs one dense paragraph) are easier to audit, easier to
    extend, and models follow them more reliably as prompts grow."""
    instructions_block = "\n".join(f"- {item}" for item in instructions)
    constraints_block = "\n".join(f"- {item}" for item in constraints)
    return (
        f"<role>\n{role}\n</role>\n\n"
        f"<instructions>\n{instructions_block}\n</instructions>\n\n"
        f"<constraints>\n{constraints_block}\n</constraints>\n\n"
        f"<output_format>\n{output_format}\n</output_format>"
    )
