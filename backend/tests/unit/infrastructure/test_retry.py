import pytest
from unittest.mock import AsyncMock

from app.core.retry import RetryEngine


@pytest.mark.asyncio
async def test_retry_engine_success_on_first_try() -> None:
    mock_func = AsyncMock(return_value="success")

    result = await RetryEngine.retry_async(
        mock_func,
        max_retries=3,
        strategy="fixed",
        base_delay_seconds=0.001,
        operation_name="test_first_try"
    )

    assert result == "success"
    assert mock_func.call_count == 1


@pytest.mark.asyncio
async def test_retry_engine_success_after_failure() -> None:
    call_count = 0

    async def mock_func() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Temporary failure")
        return "recovered"

    result = await RetryEngine.retry_async(
        mock_func,
        max_retries=3,
        strategy="fixed",
        base_delay_seconds=0.001,
        operation_name="test_after_failure"
    )

    assert result == "recovered"
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_engine_raises_after_max_retries() -> None:
    mock_func = AsyncMock(side_effect=ValueError("Fatal error"))

    with pytest.raises(ValueError, match="Fatal error"):
        await RetryEngine.retry_async(
            mock_func,
            max_retries=2,
            strategy="fixed",
            base_delay_seconds=0.001,
            operation_name="test_raises"
        )

    assert mock_func.call_count == 3  # Initial execution + 2 retries
