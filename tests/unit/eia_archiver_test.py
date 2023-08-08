import pytest

from pudl_archiver.archivers.eia860 import Eia860Archiver
from pudl_archiver.archivers.eia860m import Eia860MArchiver
from pudl_archiver.archivers.eia861 import Eia861Archiver
from pudl_archiver.archivers.eia923 import Eia923Archiver


@pytest.mark.asyncio
async def test_eia860(mocker):
    mock_session = mocker.AsyncMock()
    urls = [
        f"https://www.eia.gov/electricity/data/eia860/xls/eia860{y}.zip"
        for y in range(2000, 2023)
    ]
    get_hyperlinks = mocker.AsyncMock(return_value=urls)
    mocker.patch(
        "pudl_archiver.archivers.eia860.Eia860Archiver.get_hyperlinks",
        get_hyperlinks,
    )
    archiver = Eia860Archiver(mock_session, only_years=[2019, 2022])
    resources = [res async for res in archiver.get_resources()]
    assert len(resources) == 2


@pytest.mark.asyncio
async def test_eia860m(mocker):
    mock_session = mocker.AsyncMock()
    urls = [
        f"https://www.eia.gov/electricity/data/eia860m/xls/{m}_generator{y}.xlsx"
        for y in range(2000, 2023)
        for m in [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ]
    ]
    get_hyperlinks = mocker.AsyncMock(return_value=urls)
    mocker.patch(
        "pudl_archiver.archivers.eia860m.Eia860MArchiver.get_hyperlinks",
        get_hyperlinks,
    )
    archiver = Eia860MArchiver(mock_session, only_years=[2019, 2022])
    resources = [res async for res in archiver.get_resources()]
    assert len(resources) == 24


@pytest.mark.asyncio
async def test_eia861(mocker):
    mock_session = mocker.AsyncMock()
    urls = [
        f"https://www.eia.gov/electricity/data/eia861/zip/f861{y}.zip"
        for y in [95, 96, 11, 12, 2019, 2022]
    ]
    get_hyperlinks = mocker.AsyncMock(return_value=urls)
    mocker.patch(
        "pudl_archiver.archivers.eia861.Eia861Archiver.get_hyperlinks",
        get_hyperlinks,
    )
    archiver = Eia861Archiver(mock_session, only_years=[2019, 2022])
    resources = [res async for res in archiver.get_resources()]
    assert len(resources) == 2


@pytest.mark.asyncio
async def test_eia923(mocker):
    mock_session = mocker.AsyncMock()
    urls = [
        f"https://www.eia.gov/electricity/data/eia923/zip/f923_{y}.zip"
        for y in range(2002, 2023)
    ]
    get_hyperlinks = mocker.AsyncMock(return_value=urls)
    mocker.patch(
        "pudl_archiver.archivers.eia923.Eia923Archiver.get_hyperlinks",
        get_hyperlinks,
    )
    archiver = Eia923Archiver(mock_session, only_years=[2019, 2022])
    resources = [res async for res in archiver.get_resources()]
    assert len(resources) == 2
