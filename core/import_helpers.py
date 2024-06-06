def goodreads_status(shelf):
    # Using a dictionary as a case/switch statement.
    try:
        return {
            "to-read": "wishlist",
            "currently-reading": "reading",
            "read": "finished",
            "abandoned": "dnf",
        }[shelf]
    except KeyError:
        return "wishlist"
