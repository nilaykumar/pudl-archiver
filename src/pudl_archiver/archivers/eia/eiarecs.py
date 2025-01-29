"""Archive EIA Residential Energy Consumption Survey (RECS)."""

import logging
import re
from dataclasses import dataclass
from io import BytesIO
from urllib.parse import urljoin

from pudl_archiver.archivers.classes import (
    AbstractDatasetArchiver,
    ArchiveAwaitable,
    ResourceInfo,
)
from pudl_archiver.frictionless import ZipLayout


@dataclass
class LinkSet:
    """Information a set of links in one tab of the RECS viewer.

    See https://www.eia.gov/consumption/residential/data/2020/.
    """

    view: str
    short_name: str
    extension: str
    pattern: re.Pattern
    skip_if_html: bool = True


def _url_for(year: int, view: str):
    """Get the URL for a specific RECS year/tab combo."""
    return (
        f"https://www.eia.gov/consumption/residential/data/{year}/index.php?view={view}"
    )


YEAR_LINK_SETS = {
    2020: {
        "housing_characteristics": LinkSet(
            view="characteristics",
            short_name="hc",
            pattern=re.compile(r"HC (\d{1,2}\.\d{1,2})\.xlsx"),
            extension="xlsx",
        ),
        "consumption & expenditures": LinkSet(
            view="consumption",
            short_name="ce",
            pattern=re.compile(r"ce(\d\.\d{1,2}[a-z]?)\.xlsx"),
            extension="xlsx",
        ),
        "state data (housing characteristics)": LinkSet(
            view="state",
            short_name="state-hc",
            pattern=re.compile(r"State (.*)\.xlsx"),
            extension="xlsx",
        ),
        "state data (consumption & expenditures)": LinkSet(
            view="state",
            short_name="state-ce",
            pattern=re.compile(r"ce(\d\.\d{1,2}\..*)\.xlsx"),
            extension="xlsx",
        ),
        "microdata": LinkSet(
            view="microdata",
            short_name="microdata",
            pattern=re.compile(r"(recs.*public.*)\.csv"),
            extension="csv",
        ),
        "microdata-codebook": LinkSet(
            view="microdata",
            short_name="microdata",
            pattern=re.compile(r"(RECS 2020 Codebook.*v.)\.xlsx"),
            extension="xlsx",
        ),
        "methodology": LinkSet(
            view="methodology",
            short_name="methodology",
            pattern=re.compile(r"pdf/(.+)\.pdf"),
            extension="pdf",
        ),
    },
    2015: {
        "housing_characteristics": LinkSet(
            view="characteristics",
            short_name="hc",
            pattern=re.compile(r"hc(\d{1,2}\.\d{1,2})\.xlsx"),
            extension="xlsx",
        ),
        "consumption & expenditures": LinkSet(
            view="consumption",
            short_name="ce",
            pattern=re.compile(r"ce(\d\.\d{1,2}[a-z]?)\.xlsx"),
            extension="xlsx",
        ),
        "microdata": LinkSet(
            view="microdata",
            short_name="microdata",
            pattern=re.compile(r"(recs.*public.*)\.csv"),
            extension="csv",
        ),
        "microdata-codebook": LinkSet(
            view="microdata",
            short_name="microdata",
            pattern=re.compile(r"(codebook.*)\.xlsx"),
            extension="xlsx",
        ),
        "methodology": LinkSet(
            view="methodology",
            short_name="methodology",
            pattern=re.compile(r"/consumption/residential/reports/2015/(.+)(\.php)?"),
            extension="html",
            skip_if_html=False,
        ),
    },
}
logger = logging.getLogger(f"catalystcoop.{__name__}")


class EiaRECSArchiver(AbstractDatasetArchiver):
    """EIA RECS archiver."""

    name = "eiarecs"

    async def get_resources(self) -> ArchiveAwaitable:
        """Download EIA-RECS resources."""
        for year in [2020, 2015]:
            yield self.get_year_resources(year)

    def __is_html_file(self, fileobj: BytesIO) -> bool:
        header = fileobj.read(30).lower().strip()
        fileobj.seek(0)
        return b"<!doctype html" in header

    async def get_year_resources(self, year: int) -> list[ResourceInfo]:
        """Download all excel tables for a year."""
        # Loop through all download links for tables
        tables = []
        zip_path = self.download_directory / f"eia-recs-{year}.zip"
        data_paths_in_archive = set()
        # Loop through different categories of data (all .xlsx)
        link_sets = YEAR_LINK_SETS[year]
        for link_set in link_sets.values():
            url = _url_for(year, link_set.view)
            for table_link in await self.get_hyperlinks(url, link_set.pattern):
                table_link = urljoin(url, table_link).strip("/")
                logger.info(f"Fetching {table_link}")
                match = link_set.pattern.search(table_link)
                matched_filename = (
                    match.group(1)
                    .replace(".", "-")
                    .replace(" ", "_")
                    .replace("/", "-")
                    .lower()
                )
                output_filename = f"eia-recs-{year}-{link_set.short_name}-{matched_filename}.{link_set.extension}"

                # Download file
                download_path = self.download_directory / output_filename
                await self.download_file(table_link, download_path)
                with download_path.open("rb") as f:
                    if link_set.skip_if_html and self.__is_html_file(f):
                        continue
                    self.add_to_archive(
                        zip_path=zip_path,
                        filename=output_filename,
                        blob=f,
                    )
                data_paths_in_archive.add(output_filename)
                download_path.unlink()

        tables.append(
            ResourceInfo(
                local_path=zip_path,
                partitions={"year": year},
                layout=ZipLayout(file_paths=data_paths_in_archive),
            )
        )
        return tables
