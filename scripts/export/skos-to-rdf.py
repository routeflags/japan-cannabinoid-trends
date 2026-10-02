#!/usr/bin/env python3
"""
SKOS JSON-LD to RDF/Turtle exporter

Converts SKOS taxonomy files from JSON-LD to RDF/Turtle format.

Usage:
    python3 scripts/export/skos-to-rdf.py [input.jsonld] [output.ttl]

If no arguments provided, processes all taxonomy files:
    - metadata/taxonomy/content-taxonomy.skos.jsonld
    - metadata/taxonomy/compound-taxonomy.skos.jsonld
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime


def load_jsonld(filepath):
    """Load a JSON-LD file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def resolve_curie(curie, context):
    """Resolve a CURIE (prefix:local) to a full URI."""
    if ':' not in curie:
        return curie
    
    prefix, local = curie.split(':', 1)
    
    if prefix in context:
        base = context[prefix]
        # Handle hash-based vocabularies
        if base.endswith('#') or base.endswith('/'):
            return base + local
        else:
            return base + '/' + local
    
    # Try to resolve as URI
    if curie.startswith('http://') or curie.startswith('https://'):
        return curie
    
    return curie


def serialize_value(value, context, indent=0):
    """Serialize a JSON-LD value to Turtle literal."""
    if isinstance(value, dict):
        if '@value' in value:
            # Language literal
            lang = value.get('@language', '')
            val = value['@value']
            escaped = val.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            if lang:
                return f'"{escaped}"@{lang}'
            else:
                return f'"{escaped}"'
        elif '@id' in value:
            # Reference
            return resolve_curie(value['@id'], context)
        elif '@type' in value:
            # Typed literal
            val = value.get('@value', '')
            dtype = resolve_curie(value['@type'], context)
            escaped = val.replace('\\', '\\\\').replace('"', '\\"')
            return f'"{escaped}"^^<{dtype}>'
    elif isinstance(value, list):
        # Multiple values
        serialized = [serialize_value(v, context, indent) for v in value]
        return ', '.join(serialized)
    elif isinstance(value, str):
        # Try to resolve as URI
        if ':' in value and not value.startswith('"'):
            resolved = resolve_curie(value, context)
            if resolved.startswith('http://') or resolved.startswith('https://'):
                return f'<{resolved}>'
        # String literal
        escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        return f'"{escaped}"'
    elif isinstance(value, (int, float, bool)):
        return str(value).lower() if isinstance(value, bool) else str(value)
    
    return f'"{str(value)}"'


def jsonld_to_turtle(jsonld_data, output_path=None):
    """Convert JSON-LD data to RDF/Turtle format."""
    context = jsonld_data.get('@context', {})
    graph = jsonld_data.get('@graph', [jsonld_data])
    
    lines = []
    
    # Header
    lines.append('# RDF/Turtle export')
    lines.append(f'# Generated: {datetime.utcnow().isoformat()}Z')
    lines.append(f'# Source: SKOS JSON-LD')
    lines.append('')
    
    # Prefixes
    lines.append('@prefix skos: <http://www.w3.org/2004/02/skos/core#> .')
    lines.append('@prefix dct: <http://purl.org/dc/terms/> .')
    lines.append('@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .')
    lines.append('@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .')
    lines.append('@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .')
    lines.append('')
    
    # Add custom prefixes from context
    for prefix, uri in context.items():
        if prefix not in ['skos', 'dct', 'rdfs', 'rdf', 'xsd'] and isinstance(uri, str):
            lines.append(f'@prefix {prefix}: <{uri}> .')
    lines.append('')
    
    # Process each resource in the graph
    for item in graph:
        if '@id' not in item:
            continue
        
        subject = resolve_curie(item['@id'], context)
        lines.append(f'')
        
        # Determine type
        item_type = item.get('@type', '')
        if item_type:
            type_uri = resolve_curie(item_type, context)
            lines.append(f'<{subject}>')
            lines.append(f'    rdf:type <{type_uri}> ;')
        
        # Process properties
        props = []
        for key, value in item.items():
            if key.startswith('@'):
                continue
            
            prop_uri = resolve_curie(key, context)
            serialized = serialize_value(value, context)
            
            if isinstance(value, list):
                # Multiple values
                for v in value:
                    v_serialized = serialize_value(v, context)
                    props.append(f'    <{prop_uri}> {v_serialized} ;')
            else:
                props.append(f'    <{prop_uri}> {serialized} ;')
        
        # Remove trailing semicolon
        if props:
            props[-1] = props[-1].rstrip(' ;') + ' .'
            lines.extend(props)
    
    turtle_content = '\n'.join(lines) + '\n'
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(turtle_content)
        print(f"Written: {output_path}")
    else:
        print(turtle_content)
    
    return turtle_content


def main():
    """Main entry point."""
    # Determine input files
    if len(sys.argv) >= 2:
        input_files = [sys.argv[1]]
        output_file = sys.argv[2] if len(sys.argv) >= 3 else None
    else:
        # Process all taxonomy files
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
        
        if output_file:
            jsonld_to_turtle(jsonld_data, output_file)
        else:
            # Generate output filename
            input_path = Path(input_file)
            output_path = input_path.parent / (input_path.stem.replace('.jsonld', '') + '.ttl')
            jsonld_to_turtle(jsonld_data, str(output_path))


if __name__ == '__main__':
    main()
