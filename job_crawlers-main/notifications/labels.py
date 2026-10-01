# Every company belongs to a tier, and its jobs are announced wrapped in that tier's emoji.
# The "Especiales" are the companies the radar was built for, the "Semiespeciales" come right after,
# and every other one is a "normal" job.
SPECIAL_COMPANIES = {"intel", "microsoft", "p&g", "amazon"}
SEMI_SPECIAL_COMPANIES = {"konrad", "cisco", "hp", "moody's", "hpe", "boston scientific", "stryker"}

SPECIAL_EMOJI = "😛"
SEMI_SPECIAL_EMOJI = "🧛‍♀️"
NORMAL_EMOJI = "🦨"


def tier_emoji(company):
    name = (company or "").strip().lower()
    if name in SPECIAL_COMPANIES:
        return SPECIAL_EMOJI
    if name in SEMI_SPECIAL_COMPANIES:
        return SEMI_SPECIAL_EMOJI
    return NORMAL_EMOJI


def label_title(job):
    """Wrap the title in the emoji of its tier: "😛 Software Engineer 😛", "🧛‍♀️ ... 🧛‍♀️" or "🦨 ... 🦨"."""
    emoji = tier_emoji(job.get("company"))
    return f"{emoji} {job['title']} {emoji}"
