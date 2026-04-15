from pathlib import Path

import pytest
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic

from skillkit import build_skill_catalog, load_skills_from_dir, make_skill_tools

SKILLS_DIR = Path(__file__).parent / "skills"


@pytest.fixture(scope="module")
def agent():
    skills = load_skills_from_dir(SKILLS_DIR)
    tools = make_skill_tools(skills, SKILLS_DIR)
    catalog = build_skill_catalog(skills)
    system_prompt = (
        f"You are a helpful assistant with access to specialized skills.\n\n{catalog}"
    )
    llm = ChatAnthropic(model_name="claude-sonnet-4-6", temperature=0, timeout=None, stop=None)
    return create_agent(llm, tools, system_prompt=system_prompt)


def _ask(agent, query: str) -> str:
    result = agent.invoke({"messages": [("human", query)]})
    return result["messages"][-1].content


def test_inline_token_count(agent):
    answer = _ask(agent, "How many tokens is the text 'Hello, world!'?")
    assert answer


def test_file_token_count(agent):
    answer = _ask(
        agent,
        "How many tokens are in the token-counter skill's SKILL.md file, using the claude-sonnet-4 model?",
    )
    assert "token" in answer.lower()


def test_model_context_window(agent):
    answer = _ask(agent, "What is the context window limit for gemini-2.5-pro?")
    assert "1" in answer  # 1M / 1,048,576
