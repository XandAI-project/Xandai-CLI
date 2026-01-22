"""
Postman Collection Generator Tool
Scans route files and generates Postman collections from API endpoints
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class PostmanTool:
    """Generate Postman collections by scanning route files."""

    # HTTP methods to detect
    HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]

    # File extensions to scan for routes
    ROUTE_EXTENSIONS = {".js", ".ts", ".py", ".php", ".rb", ".java", ".cs", ".go"}

    # Common route file patterns
    ROUTE_PATTERNS = [
        r".*route.*",
        r".*api.*",
        r".*controller.*",
        r".*endpoint.*",
        r".*handler.*",
        r".*main.*",
        r".*app.*",
        r".*server.*",
        r".*index.*",
        r".*views.*",
    ]

    @staticmethod
    def get_name():
        """Return the tool's name."""
        return "postman_tool"

    @staticmethod
    def get_description():
        """Return description of what the tool does."""
        return "Generate Postman collections by scanning route files in a project directory"

    @staticmethod
    def get_parameters():
        """Return the parameters this tool accepts."""
        return {
            "root_path": "string (optional) - Root directory to scan (default: current directory)",
            "output_file": "string (optional) - Output file path for Postman collection (default: postman_collection.json)",
            "collection_name": "string (optional) - Name for the Postman collection (default: API Collection)",
            "base_url": "string (optional) - Base URL for API endpoints (default: http://localhost:3000)",
        }

    def execute(
        self,
        root_path: str = ".",
        output_file: str = "postman_collection.json",
        collection_name: str = "API Collection",
        base_url: str = "http://localhost:3000",
    ):
        """
        Execute the Postman collection generation.

        Args:
            root_path: Root directory to scan for route files
            output_file: Output file path for the collection
            collection_name: Name for the collection
            base_url: Base URL for API endpoints

        Returns:
            Dictionary with generation results
        """
        try:
            root_path = Path(root_path).resolve()

            if not root_path.exists():
                return {
                    "success": False,
                    "error": f"Path does not exist: {root_path}",
                }

            # Scan for route files
            route_files = self._scan_route_files(root_path)

            if not route_files:
                return {
                    "success": False,
                    "error": "No route files found in the specified directory",
                    "scanned_path": str(root_path),
                }

            # Extract endpoints from route files
            endpoints = []
            file_details = []

            for file_path in route_files:
                file_endpoints = self._extract_endpoints(file_path, root_path)
                endpoints.extend(file_endpoints)
                file_details.append(
                    {
                        "file": str(file_path.relative_to(root_path)),
                        "endpoints_found": len(file_endpoints),
                    }
                )

            if not endpoints:
                return {
                    "success": False,
                    "error": "No API endpoints found in route files",
                    "files_scanned": len(route_files),
                    "file_details": file_details,
                }

            # Generate Postman collection
            collection = self._generate_postman_collection(endpoints, collection_name, base_url)

            # Write to file
            output_path = Path(output_file)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(collection, f, indent=2, ensure_ascii=False)

            return {
                "success": True,
                "collection_name": collection_name,
                "output_file": str(output_path.resolve()),
                "total_endpoints": len(endpoints),
                "files_scanned": len(route_files),
                "file_details": file_details,
                "endpoints": [
                    {
                        "method": ep["method"],
                        "path": ep["path"],
                        "name": ep.get("name", "Unnamed"),
                    }
                    for ep in endpoints
                ],
                "base_url": base_url,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error generating Postman collection: {str(e)}",
            }

    def _scan_route_files(self, root_path: Path) -> List[Path]:
        """
        Scan directory for route files.

        Args:
            root_path: Root directory to scan

        Returns:
            List of route file paths
        """
        route_files = []

        # Directories to exclude
        exclude_dirs = {
            "node_modules",
            "venv",
            "env",
            ".git",
            "__pycache__",
            "dist",
            "build",
            "coverage",
            ".vscode",
            ".idea",
            "vendor",
        }

        for file_path in root_path.rglob("*"):
            # Skip if in excluded directory
            if any(excluded in file_path.parts for excluded in exclude_dirs):
                continue

            # Check if file extension matches
            if file_path.suffix.lower() not in self.ROUTE_EXTENSIONS:
                continue

            # Check if filename matches route patterns
            file_name = file_path.name.lower()
            if any(re.match(pattern, file_name) for pattern in self.ROUTE_PATTERNS):
                route_files.append(file_path)

        return route_files

    def _extract_endpoints(self, file_path: Path, root_path: Path) -> List[Dict]:
        """
        Extract API endpoints from a route file.

        Args:
            file_path: Path to the route file
            root_path: Root path for relative path calculation

        Returns:
            List of endpoint dictionaries
        """
        endpoints = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")

            # Detect framework and extract endpoints accordingly
            extension = file_path.suffix.lower()

            if extension in [".js", ".ts"]:
                endpoints.extend(self._extract_js_endpoints(content, lines, file_path))
            elif extension == ".py":
                endpoints.extend(self._extract_python_endpoints(content, lines, file_path))
            elif extension == ".php":
                endpoints.extend(self._extract_php_endpoints(content, lines, file_path))
            elif extension == ".rb":
                endpoints.extend(self._extract_ruby_endpoints(content, lines, file_path))
            elif extension == ".java":
                endpoints.extend(self._extract_java_endpoints(content, lines, file_path))
            elif extension == ".cs":
                endpoints.extend(self._extract_csharp_endpoints(content, lines, file_path))
            elif extension == ".go":
                endpoints.extend(self._extract_go_endpoints(content, lines, file_path))

        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")

        return endpoints

    def _extract_js_endpoints(self, content: str, lines: List[str], file_path: Path) -> List[Dict]:
        """Extract endpoints from JavaScript/TypeScript files (Express, Fastify, etc.)"""
        endpoints = []

        # Express/Fastify patterns: app.get('/path'), router.post('/path'), etc.
        patterns = [
            r"(?:app|router|server|api)\.("
            + "|".join([m.lower() for m in self.HTTP_METHODS])
            + r")\s*\(\s*['\"]([^'\"]+)['\"]",
            r"@(" + "|".join(self.HTTP_METHODS) + r")\s*\(['\"]([^'\"]+)['\"]",  # Decorators
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                method = match.group(1).upper()
                path = match.group(2)

                endpoints.append(
                    {
                        "method": method,
                        "path": path,
                        "name": f"{method} {path}",
                        "file": str(file_path.name),
                    }
                )

        return endpoints

    def _extract_python_endpoints(
        self, content: str, lines: List[str], file_path: Path
    ) -> List[Dict]:
        """Extract endpoints from Python files (Flask, FastAPI, Django)"""
        endpoints = []

        # Flask/FastAPI patterns: @app.route(), @app.get(), etc.
        patterns = [
            r"@(?:app|router|api)\.route\s*\(\s*['\"]([^'\"]+)['\"].*?methods\s*=\s*\[([^\]]+)\]",  # @app.route('/path', methods=['GET'])
            r"@(?:app|router|api)\.("
            + "|".join([m.lower() for m in self.HTTP_METHODS])
            + r")\s*\(\s*['\"]([^'\"]+)['\"]",  # @app.get('/path')
            r"path\s*\(\s*['\"]([^'\"]+)['\"]",  # Django: path('admin/')
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if "methods" in pattern:
                    path = match.group(1)
                    methods_str = match.group(2)
                    methods = re.findall(r"['\"](\w+)['\"]", methods_str)

                    for method in methods:
                        endpoints.append(
                            {
                                "method": method.upper(),
                                "path": path,
                                "name": f"{method.upper()} {path}",
                                "file": str(file_path.name),
                            }
                        )
                elif len(match.groups()) == 2:
                    method = match.group(1).upper()
                    path = match.group(2)

                    endpoints.append(
                        {
                            "method": method,
                            "path": path,
                            "name": f"{method} {path}",
                            "file": str(file_path.name),
                        }
                    )
                else:
                    # Django path (assume GET by default)
                    path = match.group(1)
                    endpoints.append(
                        {
                            "method": "GET",
                            "path": f"/{path}" if not path.startswith("/") else path,
                            "name": f"GET /{path}",
                            "file": str(file_path.name),
                        }
                    )

        return endpoints

    def _extract_php_endpoints(self, content: str, lines: List[str], file_path: Path) -> List[Dict]:
        """Extract endpoints from PHP files (Laravel, Symfony)"""
        endpoints = []

        # Laravel patterns: Route::get(), Route::post(), etc.
        pattern = (
            r"Route::("
            + "|".join([m.lower() for m in self.HTTP_METHODS])
            + r")\s*\(\s*['\"]([^'\"]+)['\"]"
        )

        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            method = match.group(1).upper()
            path = match.group(2)

            endpoints.append(
                {
                    "method": method,
                    "path": path,
                    "name": f"{method} {path}",
                    "file": str(file_path.name),
                }
            )

        return endpoints

    def _extract_ruby_endpoints(
        self, content: str, lines: List[str], file_path: Path
    ) -> List[Dict]:
        """Extract endpoints from Ruby files (Rails)"""
        endpoints = []

        # Rails patterns: get '/path', post '/path', etc.
        pattern = (
            r"(" + "|".join([m.lower() for m in self.HTTP_METHODS]) + r")\s+['\"]([^'\"]+)['\"]"
        )

        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            method = match.group(1).upper()
            path = match.group(2)

            endpoints.append(
                {
                    "method": method,
                    "path": path,
                    "name": f"{method} {path}",
                    "file": str(file_path.name),
                }
            )

        return endpoints

    def _extract_java_endpoints(
        self, content: str, lines: List[str], file_path: Path
    ) -> List[Dict]:
        """Extract endpoints from Java files (Spring Boot)"""
        endpoints = []

        # Spring Boot patterns: @GetMapping, @PostMapping, @RequestMapping
        patterns = [
            r"@(" + "|".join(self.HTTP_METHODS) + r")Mapping\s*\(\s*['\"]([^'\"]+)['\"]",
            r"@RequestMapping\s*\([^)]*value\s*=\s*['\"]([^'\"]+)['\"].*?method\s*=\s*RequestMethod\.(\w+)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if "RequestMapping" in pattern and "method" in pattern:
                    path = match.group(1)
                    method = match.group(2).upper()
                else:
                    method = match.group(1).upper()
                    path = match.group(2)

                endpoints.append(
                    {
                        "method": method,
                        "path": path,
                        "name": f"{method} {path}",
                        "file": str(file_path.name),
                    }
                )

        return endpoints

    def _extract_csharp_endpoints(
        self, content: str, lines: List[str], file_path: Path
    ) -> List[Dict]:
        """Extract endpoints from C# files (ASP.NET Core)"""
        endpoints = []

        # ASP.NET Core patterns: [HttpGet], [HttpPost], [Route]
        patterns = [
            r"\[Http(" + "|".join(self.HTTP_METHODS) + r")\s*\(\s*['\"]([^'\"]+)['\"]",
            r"\[Http(" + "|".join(self.HTTP_METHODS) + r")\]",  # Attribute without route
        ]

        for i, line in enumerate(lines):
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    method = match.group(1).upper()

                    # Try to find route from attribute or method name
                    path = match.group(2) if len(match.groups()) > 1 else None

                    if not path:
                        # Look for [Route] attribute or extract from method name
                        route_match = re.search(r'\[Route\s*\(\s*[\'"]([^\'\"]+)[\'"]', line)
                        if route_match:
                            path = route_match.group(1)
                        else:
                            # Try to get from next lines
                            for next_line in lines[i + 1 : i + 3]:
                                if "public" in next_line or "async" in next_line:
                                    method_name_match = re.search(
                                        r"(?:async\s+)?(?:\w+\s+)?(\w+)\s*\(", next_line
                                    )
                                    if method_name_match:
                                        path = f"/{method_name_match.group(1).lower()}"
                                    break

                    if path:
                        endpoints.append(
                            {
                                "method": method,
                                "path": path,
                                "name": f"{method} {path}",
                                "file": str(file_path.name),
                            }
                        )

        return endpoints

    def _extract_go_endpoints(self, content: str, lines: List[str], file_path: Path) -> List[Dict]:
        """Extract endpoints from Go files (Gin, Echo, etc.)"""
        endpoints = []

        # Go patterns: router.GET("/path"), r.Post("/path"), etc.
        pattern = (
            r"(?:router|r|e|mux)\.(" + "|".join(self.HTTP_METHODS) + r")\s*\(\s*['\"]([^'\"]+)['\"]"
        )

        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            method = match.group(1).upper()
            path = match.group(2)

            endpoints.append(
                {
                    "method": method,
                    "path": path,
                    "name": f"{method} {path}",
                    "file": str(file_path.name),
                }
            )

        return endpoints

    def _generate_postman_collection(
        self, endpoints: List[Dict], collection_name: str, base_url: str
    ) -> Dict:
        """
        Generate a Postman collection from extracted endpoints.

        Args:
            endpoints: List of endpoint dictionaries
            collection_name: Name for the collection
            base_url: Base URL for requests

        Returns:
            Postman collection dictionary
        """
        # Group endpoints by path prefix for better organization
        grouped_endpoints = {}

        for endpoint in endpoints:
            path = endpoint["path"]
            # Extract first path segment as folder name
            parts = [p for p in path.split("/") if p]
            folder = parts[0] if parts else "Root"

            if folder not in grouped_endpoints:
                grouped_endpoints[folder] = []

            grouped_endpoints[folder].append(endpoint)

        # Build Postman collection structure
        items = []

        for folder_name, folder_endpoints in grouped_endpoints.items():
            folder_items = []

            for endpoint in folder_endpoints:
                request = {
                    "name": endpoint.get("name", f"{endpoint['method']} {endpoint['path']}"),
                    "request": {
                        "method": endpoint["method"],
                        "header": [],
                        "url": {
                            "raw": f"{base_url}{endpoint['path']}",
                            "protocol": base_url.split("://")[0],
                            "host": base_url.split("://")[1].split("/")[0].split(":"),
                            "port": (
                                base_url.split(":")[2].split("/")[0]
                                if ":" in base_url.split("://")[1]
                                else ""
                            ),
                            "path": [p for p in endpoint["path"].split("/") if p],
                        },
                        "description": f"Endpoint from {endpoint.get('file', 'unknown file')}",
                    },
                    "response": [],
                }

                # Add body for POST/PUT/PATCH
                if endpoint["method"] in ["POST", "PUT", "PATCH"]:
                    request["request"]["body"] = {
                        "mode": "raw",
                        "raw": "{}",
                        "options": {"raw": {"language": "json"}},
                    }
                    request["request"]["header"].append(
                        {
                            "key": "Content-Type",
                            "value": "application/json",
                            "type": "text",
                        }
                    )

                folder_items.append(request)

            # Create folder
            items.append({"name": folder_name.title(), "item": folder_items})

        # Postman Collection v2.1 format
        collection = {
            "info": {
                "name": collection_name,
                "_postman_id": self._generate_uuid(),
                "description": f"Auto-generated API collection with {len(endpoints)} endpoints",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": items,
            "variable": [
                {
                    "key": "base_url",
                    "value": base_url,
                    "type": "string",
                }
            ],
        }

        return collection

    @staticmethod
    def _generate_uuid() -> str:
        """Generate a simple UUID for Postman collection"""
        import uuid

        return str(uuid.uuid4())
