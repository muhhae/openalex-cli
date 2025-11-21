#!/usr/bin/env python3
import argparse
import json
import requests
import re

# OpenAlex API configuration
BASE_URL = "https://api.openalex.org/works"
PER_PAGE = 25  # OpenAlex default page size


def format_bibtex(work):
    """Convert OpenAlex work to BibTeX format"""
    pub_date = work.get("publication_date", "")
    year = pub_date[:4] if pub_date else "n.d."

    first_author = (
        work["authorships"][0]["author"]["display_name"].split()[-1]
        if work.get("authorships")
        and work["authorships"][0].get("author", {}).get("display_name")
        else "Unknown"
    )
    title_first_word = (
        re.sub(r"[^a-zA-Z0-9]", "", work["title"].split()[0])
        if work.get("title")
        else "Untitled"
    )
    citation_key = f"{first_author}{year}{title_first_word}"

    authors = " and ".join(
        [
            a["author"]["display_name"]
            for a in work.get("authorships", [])
            if a.get("author", {}).get("display_name")
        ]
    )

    return f"""@article{{{citation_key},
  author = {{{authors}}},
  title = {{{{{work.get("title", "")}}}}},
  journal = {{{work.get("host_venue", {}).get("display_name", "")}}},
  year = {{{year}}},
  doi = {{{work.get("doi", "")}}},
  url = {{{work.get("primary_location", {}).get("landing_page_url") or work.get("id", "")}}}
}}"""


def display_work(work, idx):
    title = work.get("title", "Untitled")[:80] + (
        "..." if len(work.get("title", "")) > 80 else ""
    )
    authors = ", ".join(
        [
            a["author"]["display_name"]
            for a in work.get("authorships", [])
            if a.get("author", {}).get("display_name")
        ][:3]
    )
    if len(work.get("authorships", [])) > 3:
        authors += " et al."
    year = work.get("publication_date", "")[:4] or "n.d."
    return f"[{idx}] {title} - {authors} ({year})"


def main():
    parser = argparse.ArgumentParser(description="Interactive OpenAlex Query Engine")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "bibtex"],
        default="json",
        help="Output format: json or bibtex (default: json)",
    )
    parser.add_argument(
        "-p",
        "--per-page",
        type=int,
        default=25,
        help="Per-page (default: 25)",
    )
    args = parser.parse_args()

    try:
        while True:
            query = input("\nEnter OpenAlex search query (type 'exit' to quit): ")
            if query.lower() == "exit":
                break

            cursor = "*"  # Start cursor for pagination
            page = 1
            total_saved = 0

            while True:
                params = {
                    "search": query,
                    "per-page": args.per_page,
                    "cursor": cursor,
                }
                response = requests.get(BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])
                meta = data.get("meta")
                next_cursor = meta.get("next_cursor")
                total_count = data.get("meta", {}).get("count", 0)

                if not results:
                    if page == 1:
                        print("No results found for your query.")
                    else:
                        print("No more results.")
                    break

                print(
                    f"\nPage {page} - Showing {len(results)} of {total_count} results for '{query}':"
                )
                for i, work in enumerate(results):
                    print(display_work(work, i + 1))

                selection = input(
                    "\nSelect papers to save (e.g., 1,3,5 or 'all'): "
                ).strip()

                selected_works = []
                if selection.lower() == "all":
                    selected_works = results
                elif selection:
                    try:
                        indices = [int(idx.strip()) - 1 for idx in selection.split(",")]
                        selected_works = [
                            results[i] for i in indices if 0 <= i < len(results)
                        ]
                    except ValueError:
                        print("Invalid selection. No papers saved from this page.")

                if selected_works:
                    with open(args.output, "a") as f:
                        if args.format == "json":
                            json.dump(selected_works, f, indent=2)
                            f.write("\n")
                        else:
                            for work in selected_works:
                                f.write(format_bibtex(work) + "\n\n")
                        f.flush()
                        saved_count = len(selected_works)
                        total_saved += saved_count
                        print(f"✓ Saved {saved_count} papers to {args.output}")

                if not next_cursor or next_cursor == "*":
                    print(f"End of results. Total saved: {total_saved}")
                    break

                # SIMPLE CONTINUE PROMPT
                action = input("\nContinue to next page? (Y/n): ").lower()
                if action == "n":
                    print(f"Query complete. Total saved: {total_saved}")
                    break
                else:
                    print("Continuing to next page...")

                cursor = next_cursor
                page += 1

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
