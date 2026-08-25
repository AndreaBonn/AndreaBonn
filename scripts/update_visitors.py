"""Keep assets/visitors.json up to date with the komarev profile view counter.

The counter is persisted daily so the 14-day window and the cumulative total
keep accumulating even though no widget renders them.
"""

import logging

from common.visitors import fetch_visitor_count

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    views_14d, total_views = fetch_visitor_count()
    logger.info("Visitors: %d views in the last 14 days, %d total", views_14d, total_views)


if __name__ == "__main__":
    main()
