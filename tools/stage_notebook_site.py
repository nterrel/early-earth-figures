#!/usr/bin/env python3
"""Stage a complete validated site on main; commit/push remains a human action.

Preparation needs sibling sources. CI consumes only the staged physical copies.
An existing managed snapshot is archived under ignored build/ before replacement.
"""
from pathlib import Path
import json
import uuid

import prepare_pages
import sync_catalog

FIGURES = Path(__file__).resolve().parents[1]


def stage():
    sync_catalog.check()
    destination = FIGURES / 'site'
    token = uuid.uuid4().hex
    build = FIGURES / 'build'
    build.mkdir(exist_ok=True)
    temporary = build / f'notebook-site-{token}'
    previous = None
    if destination.exists():
        # Refuse to replace hand-edited, unmanifested or symlink-containing sites.
        prepare_pages.check(destination, verify_sources=False)
    result = prepare_pages.prepare(temporary, FIGURES / 'metadata/supplement_selection.json')
    if destination.exists():
        previous = build / f'previous-notebook-site-{token}'
        destination.rename(previous)
    try:
        temporary.rename(destination)
    except OSError:
        if previous is not None:
            previous.rename(destination)
        raise
    # Rename preserves the already-verified tree; avoid hashing every file twice.
    result['directory'] = str(destination)
    print(json.dumps({'site': str(destination), 'validation': result,
                      'previous_snapshot': str(previous) if previous else None,
                      'publication': 'Local only. Inspect, commit and push main after enabling GitHub Actions as the Pages source.'}, indent=2))
    return result


if __name__ == '__main__':
    stage()
