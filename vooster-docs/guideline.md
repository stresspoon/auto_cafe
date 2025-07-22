# Project Code Guidelines

## 1. Project Overview

This document outlines the coding standards and best practices for the automated challenge mission status tracking service. The service automatically verifies challenge mission completion from Naver Cafe and updates Google Sheets daily. Key architectural decisions involve using Python for scripting, Playwright for web automation, Google Sheets API v4 for data synchronization, Cron for scheduling, and Docker for environment consistency and deployment. The system is designed for high accuracy, stability, and scalability, handling up to 50,000 posts.

## 2. Core Principles

*   **Readability & Maintainability**: Prioritize clear, self-documenting code that is easy to understand and modify by any team member.
*   **Modularity & Separation of Concerns**: Design components with single responsibilities, minimizing coupling and maximizing reusability.
*   **Robustness & Error Handling**: Implement comprehensive error handling, retry mechanisms, and logging to ensure system resilience and operational visibility.
*   **Security & Data Integrity**: Safeguard sensitive information through encryption and secure handling, ensuring data accuracy in Google Sheets.
*   **Performance & Efficiency**: Optimize critical paths to meet the 2-minute processing time for crawling and sheet updates, avoiding unnecessary resource consumption.

## 3. Language-Specific Guidelines (Python)

### File Organization and Directory Structure

The project adheres to a domain-centric organization strategy, placing related functionalities within dedicated modules.

*   **MUST**: Organize code into logical domains (e.g., `naver_crawler`, `google_sheets`, `parser`, `scheduler`) under the `src/` directory.
*   **MUST**: Place shared utilities, exceptions, and logging configuration in `src/core/` and `src/shared/`.
*   **MUST**: Use `__init__.py` files in all package directories to mark them as Python packages.

```
src/
├── main.py
├── config.py
├── core/
│   ├── exceptions.py
│   ├── logger.py
│   └── security.py
├── naver_crawler/
│   ├── __init__.py
│   ├── service.py
│   └── models.py
└── ...
```

### Import/Dependency Management

*   **MUST**: Use absolute imports for internal modules (e.g., `from src.naver_crawler import service`).
*   **MUST**: Group imports in the following order, separated by a blank line:
    1.  Standard library imports
    2.  Third-party library imports
    3.  Local application/library imports
*   **MUST**: Use `requirements.txt` for managing all project dependencies.
*   **MUST NOT**: Use relative imports (e.g., `from . import service`) within sub-packages, as this can lead to ambiguity and refactoring issues.

```python
# MUST: Correct import order and style
import logging
import os

import playwright
from google.oauth2 import service_account

from src.core.exceptions import CrawlerError
from src.naver_crawler.models import NaverPost
```

```python
# MUST NOT: Incorrect relative import or unorganized imports
import os
from .models import NaverPost # Relative import
import logging
from google.oauth2 import service_account
```

### Error Handling Patterns

*   **MUST**: Define custom exceptions for domain-specific errors in `src/core/exceptions.py`.
*   **MUST**: Catch specific exceptions rather than broad `Exception` where possible.
*   **MUST**: Log errors with appropriate severity levels (e.g., `logging.error`, `logging.exception`).
*   **MUST**: Implement retry logic with exponential backoff for transient errors (e.g., network issues, API rate limits).
*   **MUST NOT**: Suppress exceptions silently or use bare `except:` clauses.

```python
# MUST: Specific exception handling with logging and retry
import logging
import time

from src.core.exceptions import GoogleSheetsAPIError

logger = logging.getLogger(__name__)

def update_sheet_with_retry(data, max_retries=3):
    for attempt in range(max_retries):
        try:
            # Simulate API call
            if attempt < 1: # Simulate failure on first attempt
                raise GoogleSheetsAPIError("API rate limit exceeded.")
            logger.info("Sheet updated successfully.")
            return True
        except GoogleSheetsAPIError as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {2**attempt} seconds...")
            time.sleep(2**attempt)
    logger.error(f"Failed to update sheet after {max_retries} attempts.")
    return False
```

```python
# MUST NOT: Broad exception handling or silent suppression
def update_sheet_bad(data):
    try:
        # Some API call
        pass
    except: # Catches all exceptions, hides specific issues
        print("An error occurred.") # No logging, no specific error handling
```

## 4. Code Style Rules

### MUST Follow:

*   **PEP 8 Compliance**: Adhere strictly to PEP 8 for naming conventions, line length (max 120 chars), whitespace, and overall code formatting.
    *   **Rationale**: Ensures consistency and readability across the codebase.
*   **Meaningful Naming**: Use descriptive names for variables, functions, classes, and modules.
    *   **Rationale**: Improves code comprehension and reduces the need for extensive comments.
    ```python
    # MUST: Clear and descriptive names
    def get_naver_posts_by_week(board_id: str, week_number: int) -> list[NaverPost]:
        """Fetches Naver posts for a specific week."""
        pass
    ```
    ```python
    # MUST NOT: Ambiguous names
    def get_data(id, num): # What data? What id? What num?
        pass
    ```
*   **Type Hinting**: Use type hints for function arguments, return values, and variables.
    *   **Rationale**: Enhances code readability, enables static analysis, and improves maintainability.
    ```python
    # MUST: Use type hints
    def parse_post_content(content: str) -> tuple[int, str]:
        """Extracts week number and author from post content."""
        week_match = re.search(r'\*(\d+)주차', content)
        author_match = re.search(r'작성자: (\S+)', content)
        week = int(week_match.group(1)) if week_match else 0
        author = author_match.group(1) if author_match else "Unknown"
        return week, author
    ```
    ```python
    # MUST NOT: Lack of type hints
    def parse_post_content(content): # Unclear input/output types
        # ...
        return week, author
    ```
*   **Docstrings**: Provide comprehensive docstrings for all modules, classes, methods, and functions following Google or NumPy style.
    *   **Rationale**: Documents purpose, arguments, and return values, aiding understanding and API generation.
*   **Logging**: Use the Python `logging` module for all application logs. Configure log levels appropriately.
    *   **Rationale**: Centralized and configurable logging is crucial for debugging, monitoring, and auditing.
    ```python
    # MUST: Use the logging module
    import logging
    logger = logging.getLogger(__name__)

    def process_challenge_status():
        logger.info("Starting challenge status processing.")
        try:
            # ...
            logger.debug("Successfully processed challenge data.")
        except Exception as e:
            logger.error(f"Error during processing: {e}", exc_info=True)
    ```
    ```python
    # MUST NOT: Use print statements for logging
    def process_challenge_status_bad():
        print("Starting challenge status processing.") # Not configurable, not structured
        # ...
        print("Successfully processed challenge data.")
    ```
*   **Configuration Management**: Load configurations from `config/settings.ini` or environment variables, especially for sensitive data.
    *   **Rationale**: Separates configuration from code, making the application more flexible and secure.
    ```python
    # MUST: Load sensitive info from environment variables
    import os
    NAVER_ID = os.getenv("NAVER_ID")
    NAVER_PW = os.getenv("NAVER_PW")
    ```
    ```python
    # MUST NOT: Hardcode sensitive information
    NAVER_ID = "my_naver_id" # Security risk
    NAVER_PW = "my_naver_password"
    ```

### MUST NOT Do:

*   **Huge, Multi-Responsibility Modules**: Avoid creating single files or classes that handle multiple, unrelated responsibilities.
    *   **Rationale**: Violates the Single Responsibility Principle (SRP), making code harder to test, maintain, and understand.
*   **Complex State Management**: Avoid overly complex state machines or global mutable states that are difficult to track and debug.
    *   **Rationale**: Increases complexity, potential for bugs, and makes concurrent operations challenging.
*   **Magic Numbers/Strings**: Do not use hardcoded literal values without explanation. Define them as constants.
    *   **Rationale**: Improves readability and maintainability; changes only need to be made in one place.
    ```python
    # MUST: Use named constants
    MAX_RETRIES = 3
    DEFAULT_TIMEOUT_SECONDS = 60
    ```
    ```python
    # MUST NOT: Use magic numbers
    time.sleep(5) # What does 5 mean?
    if count > 100: # What does 100 represent?
        pass
    ```
*   **Direct Browser Interaction in Core Logic**: Do not embed Playwright browser interactions directly within data parsing or sheet update logic.
    *   **Rationale**: Maintains clear separation of concerns; the crawler service should handle browser interaction, passing raw data to the parser.

## 5. Architecture Patterns

### Component/Module Structure Guidelines

*   **Service Layer**: Each top-level domain (e.g., `naver_crawler`, `google_sheets`, `parser`, `scheduler`) will have a `service.py` file containing the core business logic for that domain.
    *   **Rationale**: Encapsulates domain-specific operations, making them reusable and testable.
*   **Model Layer**: Data structures (e.g., `NaverPost`, `SheetRow`) will be defined in `models.py` within their respective domain packages. Use `dataclasses` or `pydantic` for structured data.
    *   **Rationale**: Provides clear data contracts and facilitates data validation.
*   **Utility Modules**: Common, generic functions that can be used across multiple domains will reside in `src/shared/utils.py`.
    *   **Rationale**: Prevents code duplication and promotes reusability.

### Data Flow Patterns

*   **Unidirectional Data Flow**: Data should generally flow in one direction: Scheduler -> Crawler -> Parser -> Google Sheets API Service.
    *   **Rationale**: Simplifies debugging and understanding of data transformations.
*   **Input/Output Contracts**: Each major function or service method should clearly define its expected inputs and guaranteed outputs using type hints and docstrings.
    *   **Rationale**: Enforces clear interfaces between components.

### State Management Conventions

*   **Stateless Services (where possible)**: Design services to be largely stateless, processing inputs and returning outputs without retaining internal state across multiple calls.
    *   **Rationale**: Improves scalability, testability, and reduces side effects.
*   **Limited State for Automation**: Playwright browser instances will manage their own session state (cookies, local storage) within the `naver_crawler.service`. This state should be explicitly managed (e.g., `browser.close()`).
    *   **Rationale**: Necessary for web automation, but requires careful resource management.

### API Design Standards (Internal Module APIs)

*   **Clear Function Signatures**: Functions should have clear, concise names and parameters.
*   **Single Responsibility**: Each function or method should ideally do one thing and do it well.
*   **Return Values**: Functions should return meaningful values or raise specific exceptions. Avoid returning `None` to indicate failure without clear documentation.

```python
# MUST: Clear API for a service function
from src.naver_crawler.models import NaverPost

class NaverCrawlerService:
    def __init__(self, browser_context):
        self.context = browser_context

    async def crawl_board_page(self, url: str, page_num: int) -> list[NaverPost]:
        """
        Crawls a specific page of a Naver Cafe board and extracts post data.

        Args:
            url: The base URL of the Naver Cafe board.
            page_num: The page number to crawl.

        Returns:
            A list of NaverPost objects containing extracted data.
        """
        page = await self.context.new_page()
        # ... crawling logic ...
        await page.close()
        return [] # Placeholder
```