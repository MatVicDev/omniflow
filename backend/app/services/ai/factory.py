import logging
from functools import lru_cache

from app.core.config import get_settings
from app.services.ai.base import LLMProvider
from app.services.ai.offline import OfflineProvider

log = logging.getLogger(__name__)


@lru_cache
def get_provider() -> LLMProvider:
    settings = get_settings()
    provider = settings.resolved_provider
    if provider == "anthropic" and settings.anthropic_api_key:
        from app.services.ai.anthropic_provider import AnthropicProvider

        log.info("Motor de IA: Anthropic (%s)", settings.anthropic_model)
        return AnthropicProvider(settings.anthropic_api_key, settings.anthropic_model)
    if provider == "openai" and settings.openai_api_key:
        from app.services.ai.openai_provider import OpenAIProvider

        log.info("Motor de IA: OpenAI (%s)", settings.openai_model)
        return OpenAIProvider(settings.openai_api_key, settings.openai_model)
    log.info("Motor de IA: offline (NLU + RAG local)")
    return OfflineProvider()


@lru_cache
def get_offline_provider() -> OfflineProvider:
    return OfflineProvider()
