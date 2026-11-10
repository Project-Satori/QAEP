# CAF Release Archive

A static, searchable archive of the historical CodeAurora / Qualcomm Android release table.

**Source snapshot:**  
https://web.archive.org/web/20220207223122/https://wiki.codeaurora.org/xwiki/bin/QAEP/release

This repository intentionally has **no scheduled update job**. The GitHub Actions workflow only builds and deploys data already committed to the repository.

## Features

- Search across release date, tag/build ID, chipset, manifest, and Android version
- Filter by year and chipset
- Year-sharded JSON files
- Original Wayback HTML retained as provenance
- GitHub Pages deployment through GitHub Actions

## 1. Import the snapshot (one-time)

Requires Python 3.10+.

```bash
python -m pip install -r requirements.txt
python scripts/import_snapshot.py
```

The importer downloads the exact archived snapshot and writes:

- `archive/source.html` — downloaded original HTML (`id_` capture, without Wayback toolbar)
- `data/releases.json` — normalized records, retaining original cell values

Review the generated files, then commit them:

```bash
git add archive/source.html data/releases.json
git commit -m "Import archived CodeAurora release table"
```

The importer fails if it cannot find the expected five-column table or if it extracts zero rows. It does not silently publish an empty dataset.

If you already downloaded the snapshot manually, save it as `archive/source.html` and run:

```bash
python scripts/import_snapshot.py --input archive/source.html
```

## 2. Preview locally

```bash
python scripts/build_site.py
python -m http.server 8000 --directory site
```

Open http://localhost:8000

Do not open `site/index.html` directly as a `file://` URL; browsers block the JSON fetch in that mode.

## 3. Enable GitHub Pages

1. Create an empty GitHub repository and push this project.
2. Open **Settings → Pages**.
3. Under **Build and deployment → Source**, select **GitHub Actions**.
4. Push to `main` (or run the workflow manually from the Actions tab).

The workflow builds the site from committed `data/releases.json` and deploys it to GitHub Pages. It does not fetch Wayback or modify the source data.

## Data format

Each record contains:

```json
{
  "date": "February 07, 2022",
  "date_iso": "2022-02-07",
  "tag": "LA.QSSI.12.0.r1-06100-qssi.0",
  "chipset": "qssi",
  "manifest": "LA.QSSI.12.0.r1-06100-qssi.0.xml",
  "android_version": "11.00.00",
  "source_row": 1
}
```

`source_row` preserves the row's order in the source table. Empty Android-version cells remain empty strings. The importer does not infer missing values or rewrite Qualcomm tags.

## Updating / correcting data

There is deliberately no automatic update mechanism. To replace or refresh the snapshot, run the importer explicitly, inspect the diff, and commit the result.

## Attribution and scope

This is an independent archival / indexing project, not an official Qualcomm or CodeAurora service. The archived page is the source of the records. Keep the source URL and snapshot timestamp with redistributed data. Review applicable source-site and Internet Archive terms before redistributing the raw HTML.

## License

Choose a repository license appropriate for your project. The parser and frontend are original project code; the archived release table and its underlying content remain attributable to their original source.
