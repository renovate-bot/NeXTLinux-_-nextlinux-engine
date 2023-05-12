import datetime
from abc import ABC, abstractmethod
from typing import Optional

from nextlinux_engine.db import DistroNamespace, session_scope
from nextlinux_engine.db.db_govulners_db_feed_metadata import (
    NoActiveGovulnersDB,
    get_most_recent_active_govulnersdb,
)
from nextlinux_engine.services.policy_engine.engine.feeds.db import (
    get_feed_group_detached,
)
from nextlinux_engine.services.policy_engine.engine.feeds.feeds import (
    feed_registry,
    have_vulnerabilities_for,
)
from nextlinux_engine.subsys import logger


class GateUtilProvider(ABC):
    """
    This abstraction is intended to encapsulate all gate-specific logic for the VulnerabilityProviders.

    Note:
    Any logic that is used in the gates that changes by provider should go here until further refactor is deemed
    necessary. It is possible that you may need information from the VulnerabilityProvider in order to add a specific
    function. If that is the case, avoid importing the VulnerabilityProvider and pass the information that you need in
    via the constructor call for this class in VulnerabilityProvider.get_gate_util_provider()
    """

    @abstractmethod
    def oldest_namespace_feed_sync(
        self, namespace: DistroNamespace
    ) -> datetime.datetime:
        """
        Get the oldest feed sync time for the namespace.

        :param namespace: the namespace for which to fetch the oldest sync time
        :type namespace: DistroNamespace
        :return: the time of the oldest feed sync
        :rtype: datetime.datetime
        """
        ...

    @abstractmethod
    def have_vulnerabilities_for(self, distro_namespace: DistroNamespace) -> bool:
        """
        Return whether the feed groups have vulnerability data for the provided DistroNamespace
        """
        ...


class LegacyGateUtilProvider(GateUtilProvider):
    """
    Gate-specific logic for the LegacyProvider.
    """

    def oldest_namespace_feed_sync(
        self, namespace: DistroNamespace
    ) -> datetime.datetime:
        """
        Get the oldest feed sync time for the namespace.

        :param namespace: the namespace for which to fetch the oldest sync time
        :type namespace: DistroNamespace
        :return: the time of the oldest feed sync
        :rtype: datetime.datetime
        """
        oldest_update = None
        if not namespace:
            raise ValueError(
                "must have valid DistroNamespace object for namespace parameter"
            )

        for namespace_name in namespace.like_namespace_names:
            # Check feed names
            for feed in feed_registry.registered_vulnerability_feed_names():
                # First match, assume only one matches for the namespace
                group = get_feed_group_detached(feed, namespace_name)
                if group:
                    # No records yet, but we have the feed, so may just not have any data yet
                    oldest_update = group.last_sync
                    logger.debug(
                        "Found date for oldest update in feed %s group %s date = %s",
                        feed,
                        group.name,
                        oldest_update,
                    )
                    break
        return oldest_update

    def have_vulnerabilities_for(self, distro_namespace: DistroNamespace) -> bool:
        return have_vulnerabilities_for(distro_namespace)


class GovulnersGateUtilProvider(GateUtilProvider):
    """
    Gate-specific logic for the GovulnersProvider.
    """

    def oldest_namespace_feed_sync(
        self, namespace: DistroNamespace
    ) -> Optional[datetime.datetime]:
        """
        Get the namespace values using the govulners feed metadata, returns the value for the whole grypdb, since it is synced
        atomically, and the returned date is the build date of the db, not the sync date

        :param namespace: the namespace for which to fetch the oldest sync time
        :type namespace: DistroNamespace
        :return: the time of the oldest feed sync
        :rtype: datetime.datetime
        """
        with session_scope() as session:
            try:
                govulnersdb = get_most_recent_active_govulnersdb(session)
                return govulnersdb.built_at
            except NoActiveGovulnersDB:
                return None

    def have_vulnerabilities_for(self, distro_namespace_obj: DistroNamespace) -> bool:
        with session_scope() as session:
            try:
                govulnersdb = get_most_recent_active_govulnersdb(session)
            except NoActiveGovulnersDB:
                logger.info(
                    "No vulnerabilities for image distro found because no active govulners db found"
                )
                return False

            if not govulnersdb or not govulnersdb.groups:
                return False

            groups = [
                group["name"] for group in govulnersdb.groups if group["record_count"] > 0
            ]

        for namespace_name in distro_namespace_obj.like_namespace_names:
            if namespace_name in groups:
                return True
        else:
            return False