"""Compatibility interface for social models and feature routers."""

from fastapi import APIRouter

from app.social_features.assistant import assistant as assistant
from app.social_features.assistant import router as assistant_router
from app.social_features.chat import chat_append as chat_append
from app.social_features.chat import chat_audio_download as chat_audio_download
from app.social_features.chat import chat_audio_upload as chat_audio_upload
from app.social_features.chat import chat_history as chat_history
from app.social_features.chat import merge_notes as merge_notes
from app.social_features.chat import router as chat_router
from app.social_features.chat_localization import router as chat_languages_router
from app.social_features.classification import router as classification_router
from app.social_features.display_media import router as display_media_router
from app.social_features.evidence import router as evidence_router
from app.social_features.evidence_information import router as information_router
from app.social_features.facebook import facebook_login as facebook_login
from app.social_features.facebook import guest_login as guest_login
from app.social_features.facebook import logout as logout
from app.social_features.facebook import own_facebook_profile as own_facebook_profile
from app.social_features.facebook import router as facebook_router
from app.social_features.facebook_import import _create_import_asset as _create_import_asset
from app.social_features.facebook_import import (
    _ensure_import_publication as _ensure_import_publication,
)
from app.social_features.facebook_import import _facebook_published_at as _facebook_published_at
from app.social_features.facebook_import import _graph_get as _graph_get
from app.social_features.facebook_import import _graph_total as _graph_total
from app.social_features.facebook_import import _store_chunked_bytes as _store_chunked_bytes
from app.social_features.facebook_import import _upsert_facebook_media as _upsert_facebook_media
from app.social_features.facebook_import import import_facebook_media as import_facebook_media
from app.social_features.facebook_import import sync_facebook_profile as sync_facebook_profile
from app.social_features.gallery import _chunked_slice as _chunked_slice
from app.social_features.gallery import _decode_gallery_cursor as _decode_gallery_cursor
from app.social_features.gallery import _encode_gallery_cursor as _encode_gallery_cursor
from app.social_features.gallery import _gallery_page as _gallery_page
from app.social_features.gallery import _parse_range as _parse_range
from app.social_features.gallery import _publication_payload as _publication_payload
from app.social_features.gallery import boxed_thumbnail as boxed_thumbnail
from app.social_features.gallery import capture_profile as capture_profile
from app.social_features.gallery import comments as comments
from app.social_features.gallery import gallery_page as gallery_page
from app.social_features.gallery import get_post as get_post
from app.social_features.gallery import interact as interact
from app.social_features.gallery import media as media
from app.social_features.gallery import merge_transcript_chunks as merge_transcript_chunks
from app.social_features.gallery import publish as publish
from app.social_features.gallery import remove_publication as remove_publication
from app.social_features.gallery import router as gallery_router
from app.social_features.gallery import share as share
from app.social_features.gallery import thumbnail as thumbnail
from app.social_features.gallery import visible as visible
from app.social_features.gallery_filters import router as gallery_filters_router
from app.social_features.groups import _new_join_pin as _new_join_pin
from app.social_features.groups import _require_inviter as _require_inviter
from app.social_features.groups import create_group as create_group
from app.social_features.groups import delete_group as delete_group
from app.social_features.groups import group_pin as group_pin
from app.social_features.groups import hide as hide
from app.social_features.groups import invite as invite
from app.social_features.groups import join as join
from app.social_features.groups import join_by_pin as join_by_pin
from app.social_features.groups import members as members
from app.social_features.groups import remove_member as remove_member
from app.social_features.groups import reports as reports
from app.social_features.groups import rotate_group_pin as rotate_group_pin
from app.social_features.groups import router as groups_router
from app.social_features.groups import set_invite_permission as set_invite_permission
from app.social_features.language_preferences import router as preferences_router
from app.social_features.models import ChatAudio as ChatAudio
from app.social_features.models import ChatMessage as ChatMessage
from app.social_features.models import Comment as Comment
from app.social_features.models import FacebookFriend as FacebookFriend
from app.social_features.models import FacebookIdentity as FacebookIdentity
from app.social_features.models import FacebookMedia as FacebookMedia
from app.social_features.models import FacebookPost as FacebookPost
from app.social_features.models import FacebookProfile as FacebookProfile
from app.social_features.models import GroupInvite as GroupInvite
from app.social_features.models import Publication as Publication
from app.social_features.models import Reaction as Reaction
from app.social_features.models import Report as Report
from app.social_features.models import UserProfile as UserProfile
from app.social_features.profiles import _checked_note as _checked_note
from app.social_features.profiles import _extract_cv_text as _extract_cv_text
from app.social_features.profiles import _guest_may_view_profile as _guest_may_view_profile
from app.social_features.profiles import _note_audio_to_wav as _note_audio_to_wav
from app.social_features.profiles import _own_profile_payload as _own_profile_payload
from app.social_features.profiles import _process_current_cv as _process_current_cv
from app.social_features.profiles import _profile_search_text as _profile_search_text
from app.social_features.profiles import _public_profile_payload as _public_profile_payload
from app.social_features.profiles import _safe_web_url as _safe_web_url
from app.social_features.profiles import _user_profile as _user_profile
from app.social_features.profiles import delete_cv as delete_cv
from app.social_features.profiles import own_profile as own_profile
from app.social_features.profiles import profile_avatar as profile_avatar
from app.social_features.profiles import public_profile as public_profile
from app.social_features.profiles import retry_cv as retry_cv
from app.social_features.profiles import router as profiles_router
from app.social_features.profiles import search_profiles as search_profiles
from app.social_features.profiles import transcribe_note as transcribe_note
from app.social_features.profiles import update_profile as update_profile
from app.social_features.profiles import upload_cv as upload_cv
from app.social_features.schemas import AssistantCommand as AssistantCommand
from app.social_features.schemas import ChatAppend as ChatAppend
from app.social_features.schemas import ChatGalleryItem as ChatGalleryItem
from app.social_features.schemas import ChatQuickReplyItem as ChatQuickReplyItem
from app.social_features.schemas import FacebookLogin as FacebookLogin
from app.social_features.schemas import GroupAction as GroupAction
from app.social_features.schemas import GuestLogin as GuestLogin
from app.social_features.schemas import Interaction as Interaction
from app.social_features.schemas import InvitePermission as InvitePermission
from app.social_features.schemas import MergeTexts as MergeTexts
from app.social_features.schemas import PinJoin as PinJoin
from app.social_features.schemas import ProfileLinkInput as ProfileLinkInput
from app.social_features.schemas import ProfileSearchRequest as ProfileSearchRequest
from app.social_features.schemas import ProfileUpdate as ProfileUpdate
from app.social_features.schemas import Publish as Publish
from app.social_features.schemas import Share as Share
from app.social_features.uploads import router as uploads_router

router = APIRouter()
router.include_router(preferences_router)
router.include_router(chat_languages_router)
router.include_router(information_router)
router.include_router(evidence_router)
router.include_router(uploads_router)
router.include_router(display_media_router)
router.include_router(assistant_router)
router.include_router(chat_router)
router.include_router(facebook_router)
router.include_router(gallery_router)
router.include_router(groups_router)
router.include_router(classification_router)
router.include_router(gallery_filters_router)
router.include_router(profiles_router)

_ROUTE_ORDER = {
    "members": 2,
    "set_invite_permission": 4,
    "remove_member": 5,
    "create_group": 25,
    "group_pin": 26,
    "rotate_group_pin": 27,
    "delete_group": 28,
    "join_by_pin": 30,
    "chat_append": 34,
    "chat_history": 35,
    "chat_audio_upload": 36,
    "chat_audio_download": 37,
    "merge_notes": 39,
    "invite": 40,
    "join": 41,
    "remove_publication": 43,
    "assistant": 45,
    "share": 46,
    "reports": 47,
    "hide": 48,
    "logout": 59,
    "facebook_login": 60,
    "guest_login": 62,
    "own_facebook_profile": 63,
    "own_profile": 71,
    "update_profile": 72,
    "public_profile": 74,
    "profile_avatar": 75,
    "upload_cv": 78,
    "transcribe_note": 80,
    "retry_cv": 84,
    "delete_cv": 85,
    "search_profiles": 87,
    "gallery_page": 95,
    "publish": 98,
    "capture_profile": 99,
    "media": 102,
    "thumbnail": 103,
    "boxed_thumbnail": 104,
    "interact": 106,
    "comments": 107,
}
router.routes.sort(key=lambda route: _ROUTE_ORDER.get(route.endpoint.__name__, 1000))
