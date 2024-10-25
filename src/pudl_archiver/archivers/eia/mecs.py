"""Archive EIA Manufacturing Energy Consumption Survey (MECS)."""

import re

from pudl_archiver.archivers.classes import (
    AbstractDatasetArchiver,
    ArchiveAwaitable,
    ResourceInfo,
)

BASE_URL = "https://www.eia.gov/consumption/manufacturing/data"


class EiaMECSArchiver(AbstractDatasetArchiver):
    """EIA MECS archiver."""

    name = "mecs"

    async def get_resources(self) -> ArchiveAwaitable:
        """Download EIA-MECS resources."""
        for year in [2018]:
            yield self.get_year_resources(year)

    async def get_year_resources(self, year: int) -> list[ResourceInfo]:
        """Download all excel tables for a year."""
        table_link_pattern = re.compile(r"[Tt]able(\d)_(\d).xlsx")

        # Loop through all download links for tables
        tables = []
        for table_link in await self.get_hyperlinks(BASE_URL, table_link_pattern):
            # Get table major/minor number from links
            match = table_link_pattern.search(table_link)
            major_num, minor_num = match.group(1), match.group(2)

            # Download file
            download_path = (
                self.download_directory
                / f"eia-mecs-{year}-table-{major_num}-{minor_num}.xlsx"
            )
            await self.download_zipfile(table_link, download_path)

            tables.append(
                ResourceInfo(
                    local_path=download_path,
                    partitions={"year": year, "table": f"{major_num}_{minor_num}"},
                )
            )
