import logging
from typing import Optional

from django.core.cache import cache

from apps.auths.models import CustomUser


class PreferredLanguageCacheAccessor:

    KEY_PREFIX = "preferred_language"

    PREFERRED_LANGUAGE_TTL_HOURS = 24 