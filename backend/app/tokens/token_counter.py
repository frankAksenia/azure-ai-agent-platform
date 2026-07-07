import tiktoken


def count_tokens(text: str, model: str = "gpt-4.1-mini") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("o200k_base")

    return len(encoding.encode(text))


def truncate_system_instruction(instruction: str) -> tuple[str, int]:
    sections = instruction.split("[")
    sections = ["[" + section for section in sections if section]

    truncated_sections = sections[:2]

    for section in sections[2:]:
        if "[TOOL INSTRUCTIONS]" in section and len(truncated_sections) < 4:
            truncated_sections.append(section)

    for section in sections[2:]:
        if "[GROUNDING RULES" in section and len(truncated_sections) < 4:
            truncated_sections.append(section)

    truncated = "".join(truncated_sections)
    return truncated, count_tokens(truncated)
