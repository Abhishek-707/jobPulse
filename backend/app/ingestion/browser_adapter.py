from typing import List, Optional
from app.ingestion.base import JobSource, RawJob
from playwright.async_api import async_playwright
import logging

logger = logging.getLogger(__name__)


class BrowserAdapter(JobSource):
    """Adapter for browser-based extraction using Playwright."""
    
    def __init__(self, source_id: int, source_name: str, base_url: str, timeout: int = 30000):
        super().__init__(source_id, source_name)
        self.base_url = base_url
        self.timeout = timeout  # milliseconds
    
    async def fetch(self) -> List[RawJob]:
        """Fetch jobs using browser automation."""
        try:
            logger.info(f"Fetching from {self.base_url} using browser")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                try:
                    await page.goto(self.base_url, timeout=self.timeout, wait_until="domcontentloaded")
                    jobs = await self._extract_jobs(page)
                    logger.info(f"Extracted {len(jobs)} jobs from browser")
                    return jobs
                finally:
                    await browser.close()
        
        except Exception as e:
            logger.error(f"Error fetching via browser: {e}")
            raise
    
    async def _extract_jobs(self, page) -> List[RawJob]:
        """Extract job data from page. Override in subclasses for specific selectors."""
        # Generic implementation - looks for common job listing patterns
        jobs = []
        
        # Try common CSS selectors for job listings
        job_elements = await page.query_selector_all(
            '[class*="job"], [class*="listing"], article, [data-job-id]'
        )
        
        logger.info(f"Found {len(job_elements)} job elements")
        
        for element in job_elements:
            try:
                # Try to extract common fields
                title = await self._safe_text_content(element, '[class*="title"], h2, h3')
                company = await self._safe_text_content(element, '[class*="company"], [class*="employer"]')
                location = await self._safe_text_content(element, '[class*="location"], [class*="place"]')
                description = await self._safe_text_content(element, '[class*="description"], [class*="summary"]')
                url = await element.get_attribute('href')
                
                if title and company:  # Minimum required fields
                    job = RawJob(
                        title=title,
                        company=company,
                        location=location,
                        description=description,
                        url=url,
                    )
                    jobs.append(job)
            except Exception as e:
                logger.debug(f"Error extracting job element: {e}")
                continue
        
        return jobs
    
    @staticmethod
    async def _safe_text_content(element, selector: str) -> Optional[str]:
        """Safely extract text content from element."""
        try:
            sub_element = await element.query_selector(selector)
            if sub_element:
                text = await sub_element.text_content()
                return text.strip() if text else None
        except Exception:
            pass
        return None
