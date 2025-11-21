#!/usr/bin/env python3
import argparse
import json
import requests
import re
from datetime import datetime

# OpenAlex API configuration
BASE_URL = "https://api.openalex.org/works"
PER_PAGE = 25  # OpenAlex default page size

def format_bibtex(work):
    """Convert OpenAlex work to BibTeX format"""
    # Extract year from publication date
    pub_date = work.get('publication_date', '')
    year = pub_date[:4] if pub_date else 'n.d.'
    
    # Generate citation key: first author + year + first word of title
    first_author = work['authorships'][0]['author']['display_name'].split()[-1] if work.get('authorships') else 'Unknown'
    title_first_word = re.sub(r'[^a-zA-Z0-9]', '', work['title'].split()[0]) if work.get('title') else 'Untitled'
    citation_key = f"{first_author}{year}{title_first_word}"
    
    # Format authors
    authors = " and ".join([a['author']['display_name'] for a in work.get('authorships', [])])
    
    # Create BibTeX entry
    return f"""@article{{{citation_key},
  author = {{{authors}}},
  title = {{{{{work.get('title', '')}}}}},
  journal = {{{work.get('host_venue', {}).get('display_name', '')}}},
  year = {{{year}}},
  doi = {{{work.get('doi', '')}}},
  url = {{{work.get('id', '')}}}
}}"""

def display_work(work, idx):
    """Display work summary for selection"""
    title = work.get('title', 'Untitled')[:80] + ('...' if len(work.get('title', '')) > 80 else '')
    authors = ', '.join([a['author']['display_name'] for a in work.get('authorships', [])][:3])
    if len(work.get('authorships', [])) > 3:
        authors += ' et al.'
    year = work.get('publication_date', '')[:4] or 'n.d.'
    return f"[{idx}] {title} - {authors} ({year})"

def main():
    parser = argparse.ArgumentParser(description='Interactive OpenAlex Query Engine')
    parser.add_argument('-o', '--output', required=True, help='Output file path')
    parser.add_argument('-f', '--format', choices=['json', 'bibtex'], default='json',
                        help='Output format: json or bibtex (default: json)')
    args = parser.parse_args()

    try:
        with open(args.output, 'a') as f:
            while True:
                query = input("\nEnter OpenAlex search query (type 'exit' to quit): ")
                if query.lower() == 'exit':
                    break
                
                page = 1
                cursor = '*'  # Start cursor for pagination
                total_results = 0
                
                while True:
                    params = {
                        'search': query,
                        'per-page': PER_PAGE,
                        'cursor': cursor
                    }
                    response = requests.get(BASE_URL, params=params)
                    response.raise_for_status()
                    
                    data = response.json()
                    results = data.get('results', [])
                    cursor = data.get('next_cursor')
                    
                    if not results:
                        print("No results found.")
                        break
                    
                    print(f"\nPage {page} - {len(results)} results:")
                    for i, work in enumerate(results):
                        print(display_work(work, i+1))
                    
                    # Paper selection
                    selection = input("\nSelect papers to save (e.g., 1,3,5 or 'all'): ").strip()
                    
                    selected_works = []
                    if selection.lower() == 'all':
                        selected_works = results
                    elif selection:
                        try:
                            indices = [int(idx.strip()) - 1 for idx in selection.split(',')]
                            selected_works = [results[i] for i in indices if 0 <= i < len(results)]
                        except ValueError:
                            print("Invalid selection. No papers saved from this page.")
                    
                    # Save selected works
                    if selected_works:
                        if args.format == 'json':
                            json.dump(selected_works, f, indent=2)
                            f.write('\n')  # Add newline between entries
                        else:  # bibtex
                            for work in selected_works:
                                f.write(format_bibtex(work) + '\n\n')  # Two newlines between entries
                        f.flush()
                        print(f"✓ Saved {len(selected_works)} papers to {args.output}")
                        total_results += len(selected_works)
                    
                    # Continue pagination?
                    if not cursor:
                        print(f"No more results for '{query}'. Total saved: {total_results}")
                        break
                    
                    next_action = input("\nContinue to next page? (y/n) or start new query? (q): ").lower()
                    if next_action == 'n':
                        print(f"Query complete. Total saved: {total_results}")
                        break
                    elif next_action == 'q':
                        print(f"Starting new query. Total saved: {total_results}")
                        break
                    
                    page += 1
                
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
