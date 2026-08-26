"""Tests for QBittorrentClient rename behaviour."""

from unittest.mock import MagicMock

import pytest
import qbittorrentapi

from nemorosa.clients.qbittorrent import QBittorrentClient

pytestmark = pytest.mark.anyio


def make_client() -> QBittorrentClient:
    """Build a client with no configuration, to exercise one method alone."""
    client = QBittorrentClient.__new__(QBittorrentClient)
    client.client = MagicMock()
    return client


def conflict() -> qbittorrentapi.Conflict409Error:
    """The error qBittorrent raises when a rename cannot be applied."""
    return qbittorrentapi.Conflict409Error("Conflict")


class TestRenameTorrent:
    """Tests for QBittorrentClient._rename_torrent."""

    async def test_renames_display_name_and_folder(self) -> None:
        """Should rename both the display name and the root folder."""
        client = make_client()

        await client._rename_torrent("hash", "old name", "new name")

        client.client.torrents_rename.assert_called_once_with(
            torrent_hash="hash", new_torrent_name="new name"
        )
        client.client.torrents_rename_folder.assert_called_once_with(
            torrent_hash="hash", old_path="old name", new_path="new name"
        )

    async def test_renames_folder_even_when_display_name_conflicts(self) -> None:
        """Should still rename the folder when the display name is refused.

        The display name is cosmetic; the folder rename is what points the
        torrent at the data already on disk. A conflict on the first must not
        skip the second, or the torrent is left unable to find its files.
        """
        client = make_client()
        client.client.torrents_rename.side_effect = conflict()

        await client._rename_torrent("hash", "old name", "new name")

        client.client.torrents_rename_folder.assert_called_once_with(
            torrent_hash="hash", old_path="old name", new_path="new name"
        )

    async def test_survives_a_folder_conflict(self) -> None:
        """Should not raise when the folder itself cannot be renamed."""
        client = make_client()
        client.client.torrents_rename_folder.side_effect = conflict()

        await client._rename_torrent("hash", "old name", "new name")

        client.client.torrents_rename_folder.assert_called_once()
