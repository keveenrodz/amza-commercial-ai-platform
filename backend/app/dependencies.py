from __future__ import annotations

from functools import lru_cache

from app.config import settings
from app.services.conversation_context_assembler import ConversationContextAssembler
from app.services.conversation_summarization_service import ConversationSummarizationService
from app.use_cases.activate_internal_user import ActivateInternalUserUseCase
from app.use_cases.add_contact_note import AddContactNoteUseCase
from app.use_cases.add_contact_tag import AddContactTagUseCase
from app.use_cases.assign_to_advisor import AssignToAdvisorUseCase
from app.use_cases.authenticate_with_provider import AuthenticateUseCase
from app.use_cases.create_internal_user import CreateInternalUserUseCase
from app.use_cases.deactivate_internal_user import DeactivateInternalUserUseCase
from app.use_cases.get_conversation_history import GetConversationHistoryUseCase
from app.use_cases.list_advisors import ListAdvisorsUseCase
from app.use_cases.list_contact_notes import ListContactNotesUseCase
from app.use_cases.list_internal_users import ListInternalUsersUseCase
from app.use_cases.list_open_opportunities import ListOpenOpportunitiesUseCase
from app.use_cases.receive_incoming_message import ReceiveIncomingMessageUseCase
from app.use_cases.remove_contact_tag import RemoveContactTagUseCase
from app.use_cases.resolve_follow_up import ResolveFollowUpUseCase
from app.use_cases.return_to_ai import ReturnToAIUseCase
from app.use_cases.schedule_follow_up import ScheduleFollowUpUseCase
from app.use_cases.search_opportunities import SearchOpportunitiesUseCase
from app.use_cases.send_advisor_reply import SendAdvisorReplyUseCase
from app.use_cases.set_opportunity_unread import SetOpportunityUnreadUseCase
from app.use_cases.toggle_contact_favorite import ToggleContactFavoriteUseCase
from core.interfaces.auth import AuthProvider
from core.interfaces.providers import AIProvider, ChannelProvider
from infrastructure.ai.openrouter import OpenRouterAIProvider
from infrastructure.auth.google import GoogleOAuthProvider
from infrastructure.channels.telegram import TelegramChannelProvider
from infrastructure.database.session import AsyncSessionFactory


@lru_cache
def get_ai_provider() -> AIProvider:
    return OpenRouterAIProvider(
        session_factory=AsyncSessionFactory,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )


@lru_cache
def get_channel_provider() -> ChannelProvider:
    return TelegramChannelProvider(bot_token=settings.telegram_bot_token)


@lru_cache
def get_context_assembler() -> ConversationContextAssembler:
    return ConversationContextAssembler(working_memory_size=settings.working_memory_size)


@lru_cache
def get_summarization_service() -> ConversationSummarizationService:
    return ConversationSummarizationService(
        ai_provider=get_ai_provider(),
        summarization_model=settings.summarization_model,
    )


@lru_cache
def get_receive_incoming_message_use_case() -> ReceiveIncomingMessageUseCase:
    return ReceiveIncomingMessageUseCase(
        session_factory=AsyncSessionFactory,
        ai_provider=get_ai_provider(),
        channel_provider=get_channel_provider(),
        context_assembler=get_context_assembler(),
        summarization_service=get_summarization_service(),
        summary_trigger_messages=settings.summary_trigger_messages,
    )


@lru_cache
def get_assign_to_advisor_use_case() -> AssignToAdvisorUseCase:
    return AssignToAdvisorUseCase(
        session_factory=AsyncSessionFactory,
        summarization_service=get_summarization_service(),
    )


@lru_cache
def get_return_to_ai_use_case() -> ReturnToAIUseCase:
    return ReturnToAIUseCase(
        session_factory=AsyncSessionFactory,
        summarization_service=get_summarization_service(),
    )


@lru_cache
def get_send_advisor_reply_use_case() -> SendAdvisorReplyUseCase:
    return SendAdvisorReplyUseCase(
        session_factory=AsyncSessionFactory,
        channel_provider=get_channel_provider(),
    )


@lru_cache
def get_get_conversation_history_use_case() -> GetConversationHistoryUseCase:
    return GetConversationHistoryUseCase(session_factory=AsyncSessionFactory)


@lru_cache
def get_list_open_opportunities_use_case() -> ListOpenOpportunitiesUseCase:
    return ListOpenOpportunitiesUseCase(session_factory=AsyncSessionFactory)


@lru_cache
def get_add_contact_tag_use_case() -> AddContactTagUseCase:
    return AddContactTagUseCase(session_factory=AsyncSessionFactory)


@lru_cache
def get_remove_contact_tag_use_case() -> RemoveContactTagUseCase:
    return RemoveContactTagUseCase(session_factory=AsyncSessionFactory)


@lru_cache
def get_toggle_contact_favorite_use_case() -> ToggleContactFavoriteUseCase:
    return ToggleContactFavoriteUseCase(session_factory=AsyncSessionFactory)


@lru_cache
def get_list_contact_notes_use_case() -> ListContactNotesUseCase:
    return ListContactNotesUseCase(session_factory=AsyncSessionFactory)


@lru_cache
def get_add_contact_note_use_case() -> AddContactNoteUseCase:
    return AddContactNoteUseCase(session_factory=AsyncSessionFactory)


@lru_cache
def get_schedule_follow_up_use_case() -> ScheduleFollowUpUseCase:
    return ScheduleFollowUpUseCase(session_factory=AsyncSessionFactory)


@lru_cache
def get_resolve_follow_up_use_case() -> ResolveFollowUpUseCase:
    return ResolveFollowUpUseCase(session_factory=AsyncSessionFactory)


@lru_cache
def get_set_opportunity_unread_use_case() -> SetOpportunityUnreadUseCase:
    return SetOpportunityUnreadUseCase(session_factory=AsyncSessionFactory)


@lru_cache
def get_list_advisors_use_case() -> ListAdvisorsUseCase:
    return ListAdvisorsUseCase(session_factory=AsyncSessionFactory)


@lru_cache
def get_search_opportunities_use_case() -> SearchOpportunitiesUseCase:
    return SearchOpportunitiesUseCase(session_factory=AsyncSessionFactory)


@lru_cache
def get_google_auth_provider() -> AuthProvider:
    return GoogleOAuthProvider(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
    )


@lru_cache
def get_authenticate_use_case() -> AuthenticateUseCase:
    return AuthenticateUseCase(
        session_factory=AsyncSessionFactory,
        auth_provider=get_google_auth_provider(),
    )


@lru_cache
def get_list_internal_users_use_case() -> ListInternalUsersUseCase:
    return ListInternalUsersUseCase(session_factory=AsyncSessionFactory)


@lru_cache
def get_create_internal_user_use_case() -> CreateInternalUserUseCase:
    return CreateInternalUserUseCase(session_factory=AsyncSessionFactory)


@lru_cache
def get_deactivate_internal_user_use_case() -> DeactivateInternalUserUseCase:
    return DeactivateInternalUserUseCase(session_factory=AsyncSessionFactory)


@lru_cache
def get_activate_internal_user_use_case() -> ActivateInternalUserUseCase:
    return ActivateInternalUserUseCase(session_factory=AsyncSessionFactory)
