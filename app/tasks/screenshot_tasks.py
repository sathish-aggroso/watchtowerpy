import os
import logging
import tempfile

logger = logging.getLogger(__name__)

for key in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
    os.environ.pop(key, None)
    os.environ.pop(key.lower(), None)


async def take_screenshot_async(url: str, output_path: str) -> str:
    from pyppeteer import launch
    import os

    try:
        logger.info(f"[screenshot] Starting screenshot for {url}")
        logger.info(f"[screenshot] Output path: {output_path}")

        executable = os.environ.get("PYPPETEER_EXECUTABLE_PATH")

        browser = await launch(
            headless=True,
            executablePath=executable,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-cache",
                "--disk-cache-size=0",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--allow-running-insecure-content",
                "--ignore-certificate-errors",
                "--proxy-server=direct://",
                "--proxy-bypass-list=*",
            ],
        )

        page = await browser.newPage()
        await page.setViewport({"width": 1920, "height": 1080})

        logger.info(f"[screenshot] Navigating to {url}")
        response = await page.goto(url, waitUntil="networkidle2", timeout=30000)
        logger.info(
            f"[screenshot] Response status: {response.status if response else 'None'}"
        )

        await asyncio.sleep(2)

        logger.info(f"[screenshot] Taking screenshot to {output_path}")
        await page.screenshot(path=output_path, fullPage=True)

        await browser.close()

        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logger.info(
                f"[screenshot] Screenshot saved to {output_path} ({file_size} bytes)"
            )
            return output_path

        logger.warning(f"[screenshot] Screenshot file not found at {output_path}")
        raise Exception("Screenshot file not created")

    except Exception as e:
        logger.error(f"[screenshot] Error: {type(e).__name__}: {e}")
        raise


def take_screenshot_sync(url: str, output_path: str) -> str:
    import asyncio

    try:
        return asyncio.run(take_screenshot_async(url, output_path))
    except Exception as e:
        logger.error(f"[screenshot] Error: {type(e).__name__}: {e}")
        raise


async def fetch_url_async(url: str) -> dict:
    import asyncio
    import os
    from pyppeteer import launch

    try:
        logger.info(f"[pyppeteer] Fetching URL: {url}")

        executable = os.environ.get("PYPPETEER_EXECUTABLE_PATH")

        browser = await launch(
            headless=True,
            executablePath=executable,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-cache",
                "--disk-cache-size=0",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--allow-running-insecure-content",
                "--ignore-certificate-errors",
                "--proxy-server=direct://",
                "--proxy-bypass-list=*",
            ],
        )

        page = await browser.newPage()
        await page.setViewport({"width": 1920, "height": 1080})

        logger.info(f"[pyppeteer] Navigating to {url}")
        response = await page.goto(url, waitUntil="networkidle2", timeout=30000)
        status = response.status if response else "None"
        logger.info(f"[pyppeteer] Response status: {status}")

        await asyncio.sleep(2)

        html = await page.evaluate("document.documentElement.outerHTML")
        logger.info(f"[pyppeteer] HTML length: {len(html)}")

        await browser.close()

        return {"success": True, "content": html}

    except Exception as e:
        logger.error(f"[pyppeteer] Error: {type(e).__name__}: {e}")
        return {"success": False, "error": str(e)}


def fetch_url_sync(url: str) -> dict:
    import asyncio

    try:
        return asyncio.run(fetch_url_async(url))
    except Exception as e:
        logger.error(f"[pyppeteer] Error fetching {url}: {type(e).__name__}: {e}")
        return {"success": False, "error": str(e)}
