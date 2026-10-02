#!/usr/bin/env python3
"""
SKOS JSON-LD to Schema.org JSON-LD exporter

Converts SKOS taxonomy concepts to Schema.org DefinedTerm format
for web publishing and SEO purposes.

Usage:
    python3 scripts/export/skos-to-schema-jsonld.py [input.jsonld] [output.jsonld]

If no arguments provided, processes all taxonomy files.
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def load_jsonld(filepath):
    """Load a JSON-LD file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_concepts(jsonld_data):
    """Extract SKOS Concepts from JSON-LD graph."""
    graph = jsonld_data.get('@graph', [jsonld_data])
    concepts = []
    
    for item in graph:
        if item.get('@type') == 'skos:Concept':
            concepts.append(item)
    
    return concepts


def get_pref_label(concept, language='en'):
    """Get preferred label for a language."""
    pref_labels = concept.get('skos:prefLabel', [])
    if isinstance(pref_labels, dict):
        pref_labels = [pref_labels]
    
    for label in pref_labels:
        if isinstance(label, dict) and label.get('@language') == language:
            return label.get('@value', '')
        elif isinstance(label, str):
            return label
    
    return ''


def get_alt_labels(concept, language='en'):
    """Get alternative labels for a language."""
    alt_labels = concept.get('skos:altLabel', [])
    if isinstance(alt_labels, dict):
        alt_labels = [alt_labels]
    
    labels = []
    for label in alt_labels:
        if isinstance(label, dict) and label.get('@language') == language:
            labels.append(label.get('@value', ''))
        elif isinstance(label, str):
            labels.append(label)
    
    return labels


def get_notation(concept):
    """Get SKOS notation."""
    notation = concept.get('skos:notation', '')
    return notation


def get_scope_note(concept, language='en'):
    """Get scope note for a language."""
    scope_notes = concept.get('skos:scopeNote', [])
    if isinstance(scope_notes, dict):
        scope_notes = [scope_notes]
    
    for note in scope_notes:
        if isinstance(note, dict) and note.get('@language') == language:
            return note.get('@value', '')
    
    return ''


def concept_to_schema_defined_term(concept, context_base='https://japan-cannabinoid-trends.routeflags.com/taxonomy/'):
    """Convert a SKOS Concept to Schema.org DefinedTerm."""
    
    concept_id = concept.get('@id', '')
    # Create a clean ID for Schema.org
    schema_id = f"{context_base}{get_notation(concept) or concept_id.split(':')[-1]}"
    
    # Get labels
    pref_label_en = get_pref_label(concept, 'en')
    pref_label_ja = get_pref_label(concept, 'ja')
    alt_labels = get_alt_labels(concept, 'en')
    scope_note = get_scope_note(concept, 'en')
    
    # Build DefinedTerm
    defined_term = {
        "@type": "schema:DefinedTerm",
        "@id": schema_id,
        "schema:name": pref_label_en or pref_label_ja,
        "schema:inDefinedTermSet": {
            "@type": "schema:DefinedTermSet",
            "@id": f"{context_base}{concept.get('@id', '').split(':')[-1]}-scheme"
        }
    }
    
    # Add Japanese name as alternate name
    if pref_label_ja and pref_label_ja != pref_label_en:
        defined_term["schema:alternateName"] = pref_label_ja
    
    # Add alt labels as additional alternate names
    if alt_labels:
        existing = defined_term.get("schema:alternateName", [])
        if isinstance(existing, str):
            existing = [existing]
        defined_term["schema:alternateName"] = existing + alt_labels
    
    # Add description from scope note
    if scope_note:
        defined_term["schema:description"] = scope_note
    
    # Add term code (SKOS notation)
    notation = get_notation(concept)
    if notation:
        defined_term["schema:termCode"] = notation
    
    return defined_term


def concept_to_schema_thing(concept, base_uri='https://japan-cannabinoid-trends.routeflags.com/taxonomy/'):
    """Convert a SKOS Concept to Schema.org Thing (for use as about/keywords)."""
    
    notation = get_notation(concept)
    concept_id = concept.get('@id', '')
    thing_id = f"{base_uri}{notation or concept_id.split(':')[-1]}"
    
    pref_label_en = get_pref_label(concept, 'en')
    pref_label_ja = get_pref_label(concept, 'ja')
    
    thing = {
        "@type": "schema:Thing",
        "@id": thing_id,
        "schema:name": pref_label_en or pref_label_ja
    }
    
    if pref_label_ja and pref_label_ja != pref_label_en:
        thing["schema:alternateName"] = pref_label_ja
    
    return thing


def convert_taxonomy_to_schema(jsonld_data, output_type='defined_terms'):
    """
    Convert SKOS taxonomy to Schema.org format.
    
    Args:
        jsonld_data: SKOS JSON-LD data
        output_type: 'defined_terms' for DefinedTermSet, 'things' for Thing list
    """
    concepts = extract_concepts(jsonld_data)
    
    # Get scheme info
    graph = jsonld_data.get('@graph', [])
    scheme = None
    for item in graph:
        if item.get('@type') == 'skos:ConceptScheme':
            scheme = item
            break
    
    scheme_id = scheme.get('@id', '') if scheme else 'taxonomy'
    scheme_name = ''
    if scheme:
        titles = scheme.get('dct:title', [])
        if isinstance(titles, dict):
            titles = [titles]
        for title in titles:
            if isinstance(title, dict) and title.get('@language') == 'en':
                scheme_name = title.get('@value', '')
    
    if output_type == 'defined_terms':
        # Create DefinedTermSet
        defined_terms = [concept_to_schema_defined_term(c) for c in concepts]
        
        result = {
            "@context": {
                "schema": "https://schema.org/",
                "skos": "http://www.w3.org/2004/02/skos/core#"
            },
            "@type": "schema:DefinedTermSet",
            "@id": f"https://japan-cannabinoid-trends.routeflags.com/taxonomy/{scheme_id.split(':')[-1]}",
            "schema:name": scheme_name,
            "schema:description": "Cannabinoid research taxonomy for social media content classification",
            "schema:dateCreated": "2026-10-02",
            "schema:license": "https://creativecommons.org/licenses/by/4.0/",
            "schema:hasDefinedTerm": defined_terms
        }
    else:
        # Create list of Things
        things = [concept_to_schema_thing(c) for c in concepts]
        
        result = {
            "@context": {
                "schema": "https://schema.org/"
            },
            "@graph": things
        }
    
    return result


def main():
    """Main entry point."""
    if len(sys.argv) >= 2:
        input_files = [sys.argv[1]]
        output_file = sys.argv[2] if len(sys.argv) >= 3 else None
    else:
        repo_root = Path(__file__).parent.parent.parent
        taxonomy_dir = repo_root / 'metadata' / 'taxonomy'
        
        input_files = []
        for f in taxonomy_dir.glob('*.skos.jsonld'):
            input_files.append(str(f))
        
        if not input_files:
            print("No .skos.jsonld files found in metadata/taxonomy/")
            sys.exit(1)
        
        output_file = None
    
    for input_file in input_files:
        print(f"\nProcessing: {input_file}")
        
        jsonld_data = load_jsonld(input_file)
        
        # Convert to Schema.org DefinedTermSet
        schema_data = convert_taxonomy_to_schema(jsonld_data, 'defined_terms')
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(schema_data, f, ensure_ascii=False, indent=2)
            print(f"Written: {output_file}")
        else:
            input_path = Path(input_file)
            output_path = input_path.parent / (input_path.stem.replace('.skos.jsonld', '') + '.schema.jsonld')
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(schema_data, f, ensure_ascii=False, indent=2)
            print(f"Written: {output_path}")


if __name__ == '__main__':
    main()
