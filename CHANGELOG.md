# Changelog

## [0.1.0] — 2026-05-17

- Initial project structure extracted from original monorepo
- Dual-process body/brain architecture via LCM
- 6 skills: navigate, stop, turn, look, get_position, navigate_to_object
- LLM task planning (DeepSeek) + VLM visual perception (Qwen/DeepSeek/OpenAI)
- CLI REPL interface replacing Gradio Web UI
- pydantic-based configuration validation
- pytest test suite with mocked external dependencies
- rich-powered colored terminal output
