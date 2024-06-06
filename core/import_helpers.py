def goodreads_status(shelf):
    # Using a dictionary as a case/switch statement.
    return {
        "to-read": "wishlist",
        "currently-reading": "reading",
        "read": "finished",
        "abandoned": "dnf",
    }[shelf]
