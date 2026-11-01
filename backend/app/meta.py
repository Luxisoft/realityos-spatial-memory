"""Stable public interface for Meta inference providers."""

from app.config import Settings
from app.providers.contracts import MetaModelClient as MetaModelClient
from app.providers.contracts import MetaProviderError as MetaProviderError
from app.providers.contracts import MetaProviderUncertainError as MetaProviderUncertainError
from app.providers.contracts import ProfileAnswer as ProfileAnswer
from app.providers.contracts import ProfileContext as ProfileContext
from app.providers.contracts import SegmentationResult as SegmentationResult
from app.providers.contracts import Transcription as Transcription
from app.providers.contracts import VideoTrackFrame as VideoTrackFrame
from app.providers.contracts import VideoTrackingResult as VideoTrackingResult
from app.providers.contracts import VideoTrackPrompt as VideoTrackPrompt
from app.providers.contracts import _raster_rle as _raster_rle
from app.providers.contracts import _rectangle_rle as _rectangle_rle
from app.providers.live import LiveMetaModelClient as LiveMetaModelClient
from app.providers.mock import MockMetaModelClient as MockMetaModelClient


def build_meta_client(settings: Settings) -> MetaModelClient:
    if settings.meta_mode == "mock":
        return MockMetaModelClient()
    if settings.meta_mode == "live":
        return LiveMetaModelClient(settings)
    raise MetaProviderError("META_MODE must be either 'mock' or 'live'.")
