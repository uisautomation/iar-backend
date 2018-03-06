from django.core.cache import cache


def clear_cached_person_for_user(user):
    """Explicitly clear the cached lookup response for a user."""
    if not user.is_anonymous:
        cache.delete("{user.username}:lookup".format(user=user))


def set_cached_person_for_user(user, person):
    """Explicitly set the cached lookup response for a user."""
    if not user.is_anonymous:
        cache.set("{user.username}:lookup".format(user=user), person)
