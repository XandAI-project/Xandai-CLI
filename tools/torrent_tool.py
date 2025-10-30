#!/usr/bin/env python3
"""
Torrent Tool for XandAI
Downloads torrents from magnet links using libtorrent or transmission
"""

import os
import time
from pathlib import Path
from typing import List, Union


class TorrentTool:
    """
    Tool for downloading torrents from magnet links.

    Supports:
    - Single magnet link or list of magnet links
    - Custom download path (defaults to current directory)
    - Progress tracking
    - Multiple torrent clients (libtorrent, transmission)
    """

    def get_name(self) -> str:
        """Return tool name"""
        return "torrent_tool"

    def get_description(self) -> str:
        """Return tool description"""
        return """Download torrents from magnet links.

Supports:
- Single magnet link or multiple links
- Custom download directory
- Progress tracking
- Automatic torrent client detection (libtorrent or transmission)

Example usage:
- "download this magnet link: magnet:?xt=..."
- "download these torrents: [link1, link2, link3]"
"""

    def get_parameters(self) -> dict:
        """Return parameter schema"""
        return {
            "type": "object",
            "properties": {
                "magnet_links": {
                    "type": ["string", "array"],
                    "description": "Single magnet link (string) or list of magnet links (array)",
                },
                "download_path": {
                    "type": "string",
                    "description": "Optional: Directory to save downloads (defaults to current directory)",
                },
                "wait_for_completion": {
                    "type": "boolean",
                    "description": "Optional: Wait for download to complete (default: False, starts and returns immediately)",
                },
            },
            "required": ["magnet_links"],
        }

    def execute(
        self,
        magnet_links: Union[str, List[str]],
        download_path: str = ".",
        wait_for_completion: bool = False,
    ) -> dict:
        """
        Download torrents from magnet links

        Args:
            magnet_links: Single magnet link or list of magnet links
            download_path: Directory to save downloads (default: current directory)
            wait_for_completion: Wait for download to complete (default: False)

        Returns:
            dict with download information and commands for LLM execution
        """
        try:
            # Normalize magnet_links to a list
            if isinstance(magnet_links, str):
                links_list = [magnet_links]
            else:
                links_list = magnet_links

            # Validate magnet links
            valid_links = []
            invalid_links = []

            for link in links_list:
                link = link.strip()
                if link.startswith("magnet:?"):
                    valid_links.append(link)
                else:
                    invalid_links.append(link)

            if not valid_links:
                return {
                    "success": False,
                    "error": "No valid magnet links provided",
                    "invalid_links": invalid_links,
                    "message": "❌ Please provide valid magnet links starting with 'magnet:?'",
                }

            # Normalize download path
            if download_path == ".":
                download_path = os.getcwd()
            else:
                download_path = os.path.abspath(download_path)

            # Create download directory if it doesn't exist
            os.makedirs(download_path, exist_ok=True)

            # Detect available torrent client
            client = self._detect_torrent_client()

            if not client:
                return {
                    "success": False,
                    "error": "No torrent client available",
                    "message": """❌ No torrent client found. Please install one:

Python (libtorrent):
  pip install libtorrent

Or Transmission CLI:
  Windows: choco install transmission-cli
  Linux:   sudo apt install transmission-cli
  macOS:   brew install transmission-cli

Or qBittorrent (with Web UI):
  Download from: https://www.qbittorrent.org/
""",
                    "suggestion": "Install libtorrent-python or transmission-cli",
                }

            # Generate download commands based on available client
            if client == "libtorrent":
                result = self._download_with_libtorrent(
                    valid_links, download_path, wait_for_completion
                )
            elif client == "transmission":
                result = self._download_with_transmission(valid_links, download_path)
            else:
                return {
                    "success": False,
                    "error": "Unsupported client",
                    "message": f"❌ Client '{client}' is not yet supported",
                }

            # Add invalid links warning if any
            if invalid_links:
                result["warning"] = f"Skipped {len(invalid_links)} invalid link(s)"
                result["invalid_links"] = invalid_links

            return result

        except Exception as e:
            return {"success": False, "error": str(e), "message": f"❌ Error: {e}"}

    def _detect_torrent_client(self) -> str:
        """Detect which torrent client is available"""
        # Try libtorrent (Python library)
        try:
            import libtorrent

            return "libtorrent"
        except ImportError:
            pass

        # Try transmission-cli
        import shutil

        if shutil.which("transmission-cli"):
            return "transmission"

        return None

    def _download_with_libtorrent(
        self, magnet_links: List[str], download_path: str, wait: bool
    ) -> dict:
        """Download using libtorrent Python library"""
        try:
            import libtorrent as lt

            # Create session
            session = lt.session()
            session.listen_on(6881, 6891)

            # Add torrents
            handles = []
            for magnet in magnet_links:
                params = {
                    "save_path": download_path,
                    "storage_mode": lt.storage_mode_t.storage_mode_sparse,
                }
                handle = lt.add_magnet_uri(session, magnet, params)
                handles.append(handle)

            download_info = []

            if wait:
                # Wait for metadata and download
                for i, handle in enumerate(handles, 1):
                    # Wait for metadata
                    while not handle.has_metadata():
                        time.sleep(1)

                    info = handle.get_torrent_info()
                    name = info.name()

                    download_info.append(
                        {
                            "name": name,
                            "magnet": magnet_links[i - 1][:50] + "...",
                            "status": "downloading",
                        }
                    )

                    # Monitor download progress
                    while handle.status().state != lt.torrent_status.seeding:
                        status = handle.status()
                        progress = status.progress * 100

                        if progress > 0:
                            download_info[-1]["progress"] = f"{progress:.1f}%"

                        time.sleep(5)

                    download_info[-1]["status"] = "completed"

                message = f"✅ Downloaded {len(handles)} torrent(s) to {download_path}"
            else:
                # Just start downloads and return immediately
                for i, handle in enumerate(handles, 1):
                    # Wait briefly for metadata to get torrent name
                    timeout = 10
                    while not handle.has_metadata() and timeout > 0:
                        time.sleep(1)
                        timeout -= 1

                    if handle.has_metadata():
                        info = handle.get_torrent_info()
                        name = info.name()
                    else:
                        name = f"Torrent {i}"

                    download_info.append(
                        {
                            "name": name,
                            "magnet": magnet_links[i - 1][:50] + "...",
                            "status": "started",
                        }
                    )

                message = f"🚀 Started downloading {len(handles)} torrent(s) in background\n📂 Download location: {download_path}"

            return {
                "success": True,
                "client": "libtorrent",
                "download_path": download_path,
                "torrents": download_info,
                "count": len(handles),
                "waited": wait,
                "message": message,
                "llm_context": self._build_success_message(
                    "libtorrent", download_info, download_path, wait
                ),
            }

        except ImportError:
            return {
                "success": False,
                "error": "libtorrent not installed",
                "message": "❌ libtorrent not found. Install with: pip install libtorrent",
            }
        except Exception as e:
            return {"success": False, "error": str(e), "message": f"❌ libtorrent error: {e}"}

    def _download_with_transmission(self, magnet_links: List[str], download_path: str) -> dict:
        """Download using transmission-cli"""
        import subprocess

        download_info = []
        commands = []

        for i, magnet in enumerate(magnet_links, 1):
            # Build transmission-cli command
            # Note: transmission-cli doesn't support setting download path directly,
            # so we'll use transmission-remote or suggest using transmission-daemon

            cmd = f'transmission-cli -w "{download_path}" "{magnet}"'
            commands.append(cmd)

            download_info.append(
                {"name": f"Torrent {i}", "magnet": magnet[:50] + "...", "status": "queued"}
            )

        # Build LLM context with commands to execute
        llm_context = f"""🧲 Torrent Download Tool

📂 Download Location: {download_path}
🔢 Torrents: {len(magnet_links)}

⚡ Starting downloads with transmission-cli:

<commands>
{chr(10).join(commands)}
</commands>

Note: Torrents will download in the background.
Check {download_path} for downloaded files.
"""

        return {
            "success": True,
            "client": "transmission-cli",
            "download_path": download_path,
            "torrents": download_info,
            "count": len(magnet_links),
            "commands": commands,
            "message": f"🚀 Starting {len(magnet_links)} torrent(s) with transmission-cli",
            "llm_context": llm_context,
        }

    def _build_success_message(
        self, client: str, torrents: List[dict], path: str, waited: bool
    ) -> str:
        """Build success message for LLM"""
        status_icon = "✅" if waited else "🚀"
        status_text = "Downloaded" if waited else "Started downloading"

        torrent_list = "\n".join(
            [
                f"  {i}. {t['name']} - {t.get('progress', t['status'])}"
                for i, t in enumerate(torrents, 1)
            ]
        )

        return f"""🧲 Torrent Download Tool

{status_icon} {status_text} {len(torrents)} torrent(s) using {client}

📂 Download Location: {path}

📋 Torrents:
{torrent_list}

{'✓ Downloads completed successfully!' if waited else '💡 Tip: Downloads are running in the background. Check the folder for progress.'}
"""


# Export the tool class
__all__ = ["TorrentTool"]
