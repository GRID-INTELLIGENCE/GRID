#!/usr/bin/env python3
"""
Playwright MCP Server
Provides web automation and browser control capabilities
"""

import asyncio
import json
import logging
import sys
from typing import Any

try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import CallToolRequest, CallToolResult, ListToolsRequest, ListToolsResult, TextContent, Tool
except ImportError:
    print("MCP library not found. Please install: pip install mcp")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlaywrightMCPServer:
    """Playwright MCP Server for web automation"""

    def __init__(self):
        self.server = Server("playwright")
        self.browser = None
        self.context = None
        self.page = None
        self._register_handlers()

    def _register_handlers(self):
        """Register MCP handlers"""

        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available Playwright tools"""
            tools = [
                Tool(
                    name="launch_browser",
                    description="Launch a browser instance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "browser": {
                                "type": "string",
                                "description": "Browser to launch (chromium, firefox, webkit)",
                                "default": "chromium",
                            },
                            "headless": {
                                "type": "boolean",
                                "description": "Run browser in headless mode",
                                "default": True,
                            },
                            "viewport": {
                                "type": "object",
                                "description": "Viewport dimensions",
                                "properties": {
                                    "width": {"type": "integer", "default": 1280},
                                    "height": {"type": "integer", "default": 720},
                                },
                            },
                        },
                    },
                ),
                Tool(
                    name="navigate",
                    description="Navigate to a URL",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL to navigate to"},
                            "wait_until": {
                                "type": "string",
                                "description": "When to consider navigation complete",
                                "default": "domcontentloaded",
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Navigation timeout in milliseconds",
                                "default": 30000,
                            },
                        },
                        "required": ["url"],
                    },
                ),
                Tool(
                    name="screenshot",
                    description="Take a screenshot of the current page",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to save screenshot (optional)"},
                            "full_page": {"type": "boolean", "description": "Capture full page", "default": False},
                            "format": {"type": "string", "description": "Image format (png, jpeg)", "default": "png"},
                            "quality": {
                                "type": "integer",
                                "description": "Image quality for JPEG (0-100)",
                                "default": 80,
                            },
                        },
                    },
                ),
                Tool(
                    name="click",
                    description="Click an element on the page",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "CSS selector for element to click"},
                            "button": {
                                "type": "string",
                                "description": "Mouse button (left, right, middle)",
                                "default": "left",
                            },
                            "modifiers": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Modifier keys (Alt, Control, Shift, Meta)",
                            },
                            "timeout": {"type": "integer", "description": "Timeout in milliseconds", "default": 30000},
                        },
                        "required": ["selector"],
                    },
                ),
                Tool(
                    name="type",
                    description="Type text into an element",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "CSS selector for element to type into"},
                            "text": {"type": "string", "description": "Text to type"},
                            "clear": {"type": "boolean", "description": "Clear field before typing", "default": True},
                            "delay": {
                                "type": "integer",
                                "description": "Delay between keystrokes in milliseconds",
                                "default": 0,
                            },
                            "timeout": {"type": "integer", "description": "Timeout in milliseconds", "default": 30000},
                        },
                        "required": ["selector", "text"],
                    },
                ),
                Tool(
                    name="get_text",
                    description="Get text content of an element",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "CSS selector for element"},
                            "timeout": {"type": "integer", "description": "Timeout in milliseconds", "default": 30000},
                        },
                        "required": ["selector"],
                    },
                ),
                Tool(
                    name="get_title", description="Get the page title", inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="get_url", description="Get the current URL", inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="wait_for_selector",
                    description="Wait for a selector to appear",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "CSS selector to wait for"},
                            "timeout": {"type": "integer", "description": "Timeout in milliseconds", "default": 30000},
                            "state": {
                                "type": "string",
                                "description": "Element state (attached, detached, hidden, visible)",
                                "default": "visible",
                            },
                        },
                        "required": ["selector"],
                    },
                ),
                Tool(
                    name="evaluate",
                    description="Execute JavaScript in the page",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "expression": {"type": "string", "description": "JavaScript expression to execute"},
                            "selector": {"type": "string", "description": "CSS selector for element scope (optional)"},
                            "timeout": {"type": "integer", "description": "Timeout in milliseconds", "default": 30000},
                        },
                        "required": ["expression"],
                    },
                ),
                Tool(
                    name="scroll",
                    description="Scroll the page",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "direction": {
                                "type": "string",
                                "description": "Scroll direction (up, down, left, right)",
                                "default": "down",
                            },
                            "pixels": {"type": "integer", "description": "Number of pixels to scroll", "default": 500},
                        },
                    },
                ),
                Tool(
                    name="close_browser",
                    description="Close the browser instance",
                    inputSchema={"type": "object", "properties": {}},
                ),
            ]
            return ListToolsResult(tools=tools)

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            try:
                if name == "launch_browser":
                    return await self._launch_browser(arguments)
                elif name == "navigate":
                    return await self._navigate(arguments)
                elif name == "screenshot":
                    return await self._screenshot(arguments)
                elif name == "click":
                    return await self._click(arguments)
                elif name == "type":
                    return await self._type_text(arguments)
                elif name == "get_text":
                    return await self._get_text(arguments)
                elif name == "get_title":
                    return await self._get_title(arguments)
                elif name == "get_url":
                    return await self._get_url(arguments)
                elif name == "wait_for_selector":
                    return await self._wait_for_selector(arguments)
                elif name == "evaluate":
                    return await self._evaluate(arguments)
                elif name == "scroll":
                    return await self._scroll(arguments)
                elif name == "close_browser":
                    return await self._close_browser(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return CallToolResult(content=[TextContent(text=f"Error: {str(e)}")], isError=True)

    async def _ensure_browser(self):
        """Ensure browser is launched"""
        if not self.browser:
            return CallToolResult(
                content=[TextContent(text="Browser not launched. Use launch_browser first.")], isError=True
            )
        return None

    async def _launch_browser(self, args: dict[str, Any]) -> CallToolResult:
        """Launch browser instance"""
        try:
            from playwright.async_api import async_playwright

            if self.browser:
                await self.browser.close()

            playwright = await async_playwright().start()

            browser_type = args.get("browser", "chromium")
            headless = args.get("headless", True)
            viewport = args.get("viewport", {"width": 1280, "height": 720})

            if browser_type == "chromium":
                self.browser = await playwright.chromium.launch(headless=headless)
            elif browser_type == "firefox":
                self.browser = await playwright.firefox.launch(headless=headless)
            elif browser_type == "webkit":
                self.browser = await playwright.webkit.launch(headless=headless)
            else:
                raise ValueError(f"Unsupported browser: {browser_type}")

            self.context = await self.browser.new_context(viewport=viewport)
            self.page = await self.context.new_page()

            result = {"browser": browser_type, "headless": headless, "viewport": viewport, "launched": True}

            return CallToolResult(content=[TextContent(text=json.dumps(result, indent=2))])
        except ImportError:
            return CallToolResult(
                content=[TextContent(text="Playwright not installed. Install with: pip install playwright")],
                isError=True,
            )
        except Exception as e:
            return CallToolResult(content=[TextContent(text=f"Error launching browser: {str(e)}")], isError=True)

    async def _navigate(self, args: dict[str, Any]) -> CallToolResult:
        """Navigate to URL"""
        check = await self._ensure_browser()
        if check:
            return check

        try:
            url = args["url"]
            wait_until = args.get("wait_until", "domcontentloaded")
            timeout = args.get("timeout", 30000)

            await self.page.goto(url, wait_until=wait_until, timeout=timeout)

            result = {"url": url, "current_url": self.page.url, "title": await self.page.title(), "navigated": True}

            return CallToolResult(content=[TextContent(text=json.dumps(result, indent=2))])
        except Exception as e:
            return CallToolResult(content=[TextContent(text=f"Error navigating: {str(e)}")], isError=True)

    async def _screenshot(self, args: dict[str, Any]) -> CallToolResult:
        """Take screenshot"""
        check = await self._ensure_browser()
        if check:
            return check

        try:
            path = args.get("path")
            full_page = args.get("full_page", False)
            format_type = args.get("format", "png")
            quality = args.get("quality", 80)

            kwargs = {"full_page": full_page, "type": format_type}

            if format_type == "jpeg":
                kwargs["quality"] = quality

            if path:
                kwargs["path"] = path

            screenshot = await self.page.screenshot(**kwargs)

            if not path:
                # Return base64 encoded image
                import base64

                image_data = base64.b64encode(screenshot).decode("utf-8")
                result = {
                    "screenshot": f"data:image/{format_type};base64,{image_data}",
                    "format": format_type,
                    "size": len(screenshot),
                }
            else:
                result = {"path": path, "format": format_type, "size": len(screenshot), "saved": True}

            return CallToolResult(content=[TextContent(text=json.dumps(result, indent=2))])
        except Exception as e:
            return CallToolResult(content=[TextContent(text=f"Error taking screenshot: {str(e)}")], isError=True)

    async def _click(self, args: dict[str, Any]) -> CallToolResult:
        """Click element"""
        check = await self._ensure_browser()
        if check:
            return check

        try:
            selector = args["selector"]
            button = args.get("button", "left")
            modifiers = args.get("modifiers", [])
            timeout = args.get("timeout", 30000)

            await self.page.click(selector, button=button, modifiers=modifiers, timeout=timeout)

            result = {"selector": selector, "clicked": True, "button": button, "modifiers": modifiers}

            return CallToolResult(content=[TextContent(text=json.dumps(result, indent=2))])
        except Exception as e:
            return CallToolResult(content=[TextContent(text=f"Error clicking element: {str(e)}")], isError=True)

    async def _type_text(self, args: dict[str, Any]) -> CallToolResult:
        """Type text into element"""
        check = await self._ensure_browser()
        if check:
            return check

        try:
            selector = args["selector"]
            text = args["text"]
            clear = args.get("clear", True)
            args.get("delay", 0)
            timeout = args.get("timeout", 30000)

            await self.page.fill(selector, text, timeout=timeout)

            result = {"selector": selector, "text": text, "typed": True, "cleared": clear}

            return CallToolResult(content=[TextContent(text=json.dumps(result, indent=2))])
        except Exception as e:
            return CallToolResult(content=[TextContent(text=f"Error typing text: {str(e)}")], isError=True)

    async def _get_text(self, args: dict[str, Any]) -> CallToolResult:
        """Get element text"""
        check = await self._ensure_browser()
        if check:
            return check

        try:
            selector = args["selector"]
            timeout = args.get("timeout", 30000)

            element = await self.page.wait_for_selector(selector, timeout=timeout)
            text = await element.text_content()

            result = {"selector": selector, "text": text, "length": len(text) if text else 0}

            return CallToolResult(content=[TextContent(text=json.dumps(result, indent=2))])
        except Exception as e:
            return CallToolResult(content=[TextContent(text=f"Error getting text: {str(e)}")], isError=True)

    async def _get_title(self, args: dict[str, Any]) -> CallToolResult:
        """Get page title"""
        check = await self._ensure_browser()
        if check:
            return check

        try:
            title = await self.page.title()

            result = {"title": title, "length": len(title)}

            return CallToolResult(content=[TextContent(text=json.dumps(result, indent=2))])
        except Exception as e:
            return CallToolResult(content=[TextContent(text=f"Error getting title: {str(e)}")], isError=True)

    async def _get_url(self, args: dict[str, Any]) -> CallToolResult:
        """Get current URL"""
        check = await self._ensure_browser()
        if check:
            return check

        try:
            url = self.page.url

            result = {"url": url}

            return CallToolResult(content=[TextContent(text=json.dumps(result, indent=2))])
        except Exception as e:
            return CallToolResult(content=[TextContent(text=f"Error getting URL: {str(e)}")], isError=True)

    async def _wait_for_selector(self, args: dict[str, Any]) -> CallToolResult:
        """Wait for selector"""
        check = await self._ensure_browser()
        if check:
            return check

        try:
            selector = args["selector"]
            timeout = args.get("timeout", 30000)
            state = args.get("state", "visible")

            await self.page.wait_for_selector(selector, timeout=timeout, state=state)

            result = {"selector": selector, "state": state, "found": True}

            return CallToolResult(content=[TextContent(text=json.dumps(result, indent=2))])
        except Exception as e:
            return CallToolResult(content=[TextContent(text=f"Error waiting for selector: {str(e)}")], isError=True)

    async def _evaluate(self, args: dict[str, Any]) -> CallToolResult:
        """Execute JavaScript"""
        check = await self._ensure_browser()
        if check:
            return check

        try:
            expression = args["expression"]
            selector = args.get("selector")
            timeout = args.get("timeout", 30000)

            if selector:
                element = await self.page.wait_for_selector(selector, timeout=timeout)
                result = await element.evaluate(expression)
            else:
                result = await self.page.evaluate(expression)

            return CallToolResult(content=[TextContent(text=json.dumps({"result": result}, indent=2))])
        except Exception as e:
            return CallToolResult(content=[TextContent(text=f"Error evaluating JavaScript: {str(e)}")], isError=True)

    async def _scroll(self, args: dict[str, Any]) -> CallToolResult:
        """Scroll page"""
        check = await self._ensure_browser()
        if check:
            return check

        try:
            direction = args.get("direction", "down")
            pixels = args.get("pixels", 500)

            if direction == "up":
                await self.page.evaluate(f"window.scrollBy(0, -{pixels})")
            elif direction == "down":
                await self.page.evaluate(f"window.scrollBy(0, {pixels})")
            elif direction == "left":
                await self.page.evaluate(f"window.scrollBy(-{pixels}, 0)")
            elif direction == "right":
                await self.page.evaluate(f"window.scrollBy({pixels}, 0)")

            result = {"direction": direction, "pixels": pixels, "scrolled": True}

            return CallToolResult(content=[TextContent(text=json.dumps(result, indent=2))])
        except Exception as e:
            return CallToolResult(content=[TextContent(text=f"Error scrolling: {str(e)}")], isError=True)

    async def _close_browser(self, args: dict[str, Any]) -> CallToolResult:
        """Close browser"""
        try:
            if self.page:
                await self.page.close()
                self.page = None

            if self.context:
                await self.context.close()
                self.context = None

            if self.browser:
                await self.browser.close()
                self.browser = None

            return CallToolResult(content=[TextContent(text="Browser closed successfully")])
        except Exception as e:
            return CallToolResult(content=[TextContent(text=f"Error closing browser: {str(e)}")], isError=True)

    async def run(self, read_stream, write_stream, options):
        """Run the MCP server"""
        await self.server.run(read_stream, write_stream, options)


# Create global server instance for MCP CLI
server = PlaywrightMCPServer()


async def run_health_server(host: str = "0.0.0.0", port: int = 8080):
    """Run a minimal HTTP health server in background."""
    from aiohttp import web

    async def health_handler(request):
        return web.Response(text="healthy\n", content_type="text/plain")

    app = web.Application()
    app.router.add_get("/health", health_handler)
    app.router.add_get("/", health_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info(f"Health server started on {host}:{port}")

    # Keep running forever
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        await runner.cleanup()


async def main():
    """Main server function with health endpoint."""
    # In Docker daemon mode, run only the health server
    # MCP stdio transport requires interactive mode
    await run_health_server()


if __name__ == "__main__":
    asyncio.run(main())
