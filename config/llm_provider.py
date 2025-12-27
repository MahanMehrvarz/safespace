"""LLM provider configuration supporting multiple backends."""
import os
from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
) -> BaseChatModel:
    """
    Get configured LLM based on provider.

    Args:
        provider: LLM provider (openai, anthropic, google, ollama)
        model: Specific model name (overrides env default)
        temperature: Model temperature

    Returns:
        Configured LLM instance
    """
    provider = provider or os.getenv("LLM_PROVIDER", "openai")
    provider = provider.lower()

    if provider == "openai":
        return _get_openai_llm(model, temperature)
    elif provider == "anthropic":
        return _get_anthropic_llm(model, temperature)
    elif provider == "google":
        return _get_google_llm(model, temperature)
    elif provider == "ollama":
        return _get_ollama_llm(model, temperature)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def _get_openai_llm(model: Optional[str], temperature: float) -> ChatOpenAI:
    """Get OpenAI LLM."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")

    model = model or os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
    )


def _get_anthropic_llm(model: Optional[str], temperature: float) -> ChatAnthropic:
    """Get Anthropic LLM."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in environment")

    model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    return ChatAnthropic(
        model=model,
        temperature=temperature,
        api_key=api_key,
    )


def _get_google_llm(model: Optional[str], temperature: float) -> ChatGoogleGenerativeAI:
    """Get Google Gemini LLM."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set in environment")

    model = model or os.getenv("GOOGLE_MODEL", "gemini-1.5-pro")

    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=api_key,
    )


def _get_ollama_llm(model: Optional[str], temperature: float) -> ChatOpenAI:
    """Get Ollama LLM (uses OpenAI-compatible interface)."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = model or os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    # Ollama uses OpenAI-compatible API
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        base_url=f"{base_url}/v1",
        api_key="ollama",  # Ollama doesn't need real API key
    )
