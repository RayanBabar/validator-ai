import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.agents.base import LLMService


@pytest.mark.asyncio
async def test_llm_service_provider_routing():
    # Mock the module-level LLM instances
    with (
        patch("src.agents.base.llm_fast", new_callable=AsyncMock) as mock_gpt_fast,
        patch(
            "src.agents.base.llm_complex", new_callable=AsyncMock
        ) as mock_gpt_complex,
        patch(
            "src.agents.base.claude_fast", new_callable=AsyncMock
        ) as mock_claude_fast,
        patch(
            "src.agents.base.claude_complex", new_callable=AsyncMock
        ) as mock_claude_complex,
    ):
        # Setup mocks to return a dummy response
        mock_gpt_fast.ainvoke.return_value = "GPT Fast Response"
        mock_gpt_complex.ainvoke.return_value = "GPT Complex Response"
        mock_claude_fast.ainvoke.return_value = "Claude Fast Response"
        mock_claude_complex.ainvoke.return_value = "Claude Complex Response"

        # We need a dummy chain behavior since the code does `prompt | model`
        # Using a simple mock that returns the model itself when piped
        # This mocks the LangChain piping behavior `prompt | model`

        mock_prompt = MagicMock()

        # When prompt | model is called, return a mock chain
        # The chain.ainvoke() should be called

        # Mocking the pipe behavior is complex, so let's mock the internal logic path directly if possible
        # However, LLMService constructs chain = prompt | primary
        # We can mock the prompt's __or__ method to return our mock chain

        # Define separate chains for GPT and Claude to control behavior independently
        mock_gpt_chain = AsyncMock()
        mock_gpt_chain.ainvoke.return_value = {"key": "gpt_value"}

        mock_claude_chain = AsyncMock()
        mock_claude_chain.ainvoke.return_value = {"key": "claude_value"}

        mock_prompt.__or__.side_effect = lambda other: other

        with patch("src.agents.base.JsonOutputParser") as MockParser:
            mock_parser_instance = MockParser.return_value

            # When model | parser is called, return the respective chain
            # We need to distinguish based on WHICH model is being piped

            # Since we can't easily condition the return value of __or__ based on self instance
            # in this simple mock setup without complex side_effects,
            # let's assume LLMService logic:
            # chain = prompt | primary -> returns primary (via mock_prompt.__or__)
            # chain = primary | parser -> returns primary_chain

            mock_gpt_fast.__or__.return_value = mock_gpt_chain
            mock_gpt_complex.__or__.return_value = mock_gpt_chain
            mock_claude_fast.__or__.return_value = mock_claude_chain
            mock_claude_complex.__or__.return_value = mock_claude_chain

            # --- TEST 2: Fallback Logic (Auto) ---
            # GPT Chain Fails
            mock_gpt_chain.ainvoke.side_effect = Exception("GPT Failed")
            # Claude Chain Succeeds
            mock_claude_chain.ainvoke.side_effect = None
            mock_claude_chain.ainvoke.return_value = "Claude Fallback Response"

            # This should trigger fallback and succeed
            await LLMService.invoke(mock_prompt, {}, use_complex=False, provider="auto")

            # --- TEST 3: No Fallback for Forced Provider ---
            # GPT Chain Fails
            mock_gpt_chain.ainvoke.side_effect = Exception("GPT Failed")

            # Even if we use provider="openai", it should NOT fall back to Claude
            with pytest.raises(Exception) as excinfo:
                await LLMService.invoke(
                    mock_prompt, {}, use_complex=False, provider="openai"
                )
            assert "GPT Failed" in str(excinfo.value)

            # Test Claude failure with provider="claude"
            mock_claude_chain.ainvoke.side_effect = Exception("Claude Failed")
            with pytest.raises(Exception) as excinfo:
                await LLMService.invoke(
                    mock_prompt, {}, use_complex=False, provider="claude"
                )
            assert "Claude Failed" in str(excinfo.value)


@pytest.mark.asyncio
async def test_module_variables_updated():
    from src.agents import base

    # Check if model names were updated in the module
    assert base.llm_fast.model_name == "gpt-5-mini"
    assert base.llm_complex.model_name == "gpt-5.2"

    # Check Claude if mocked/instantiated
    if base.claude_fast:
        assert base.claude_fast.model == "claude-sonnet-4-5-20250929"
        assert base.claude_complex.model == "claude-sonnet-4-5-20250929"
