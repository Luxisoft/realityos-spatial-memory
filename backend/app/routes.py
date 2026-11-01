"""Stable route entry point; implementations live in app.http."""

from fastapi import APIRouter

from app.http import captures, identity, media, objects, queries, tts

router = APIRouter()
router.include_router(identity.router)
router.include_router(captures.router)
router.include_router(objects.router)
router.include_router(queries.router)
router.include_router(media.router)

_ROUTE_ORDER = {
    "bootstrap_virtual_device": 0,
    "list_device_zones": 1,
    "login": 2,
    "refresh": 3,
    "me": 4,
    "list_workspaces": 5,
    "create_workspace": 6,
    "list_devices": 7,
    "enroll_device": 8,
    "rotate_device_credential": 9,
    "revoke_device": 10,
    "list_device_assignments": 11,
    "assign_device": 12,
    "list_zones": 13,
    "create_zone": 14,
    "create_session": 15,
    "get_session": 16,
    "close_session": 17,
    "create_device_session": 18,
    "close_device_session": 19,
    "create_capture": 20,
    "create_device_capture": 21,
    "get_capture": 22,
    "process_capture": 23,
    "process_device_capture": 24,
    "get_device_job": 25,
    "get_job": 26,
    "list_objects": 27,
    "get_object": 28,
    "create_object_alias": 29,
    "object_history": 30,
    "object_facts": 31,
    "verify_fact": 32,
    "object_tracks": 33,
    "track_frames": 34,
    "inventory_analytics": 35,
    "verify_observation": 36,
    "request_observation_segmentation": 37,
    "query": 38,
    "image_query": 39,
    "classify_search_probe": 40,
    "route_search_text": 41,
    "device_query": 42,
    "audio_query": 43,
    "get_media": 44,
    "highlighted_observation": 45,
    "device_highlighted_observation": 46,
    "display_highlighted_observation": 47,
    "highlighted_media": 48,
}
router.routes.sort(key=lambda route: _ROUTE_ORDER[route.endpoint.__name__])
router.include_router(tts.router)
