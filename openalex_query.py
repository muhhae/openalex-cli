#!/usr/bin/env python3
import argparse
import json
import requests
import re
from datetime import datetime

# OpenAlex API configuration
BASE_URL = "https://api.openalex.org/works"

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
                
                params = {'search': query}
                response = requests.get(BASE_URL, params=params)
                response.raise_for_status()
                
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    print("No results found.")
                    continue
                
                if args.format == 'json':
                    # Write formatted JSON with indentation
                    json.dump(results, f, indent=2)
                    f.write('\n')  # Add newline between entries
                else:  # bibtex
                    for work in results:
                        f.write(format_bibtex(work) + '\n\n')  # Two newlines between entries
                
                f.flush()
                print(f"✓ {len(results)} results for '{query}' written to {args.output} in {args.format} format")
                
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
