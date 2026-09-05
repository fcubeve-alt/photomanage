#!/usr/bin/env python3
"""
Verify that the committed test-library manifest still reproduces from its seed.

    python check_manifest_reproducible.py <regenerated manifest.json>

Two participants in different sessions must be looking at the same library, or
every between-arm comparison in T0-B and T0-D is comparing two different things.
`generated_at` is a wall-clock stamp and is expected to differ; everything that
describes the library itself must be identical.
"""
import io, json, os, sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
COMMITTED = os.path.join(HERE, "library", "manifest.json")

VOLATILE = ("generated_at",)


def load(path):
    d = json.load(io.open(path, encoding="utf-8"))
    for k in VOLATILE:
        d.pop(k, None)
    return d


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    committed, regenerated = load(COMMITTED), load(sys.argv[1])
    if committed == regenerated:
        print(f"manifest reproduces from seed {committed.get('seed')} "
              f"({committed.get('total_assets')} assets)")
        return
    differing = sorted(k for k in set(committed) | set(regenerated)
                       if committed.get(k) != regenerated.get(k))
    sys.exit("manifest does not reproduce from its seed. Fields differing beyond the "
             f"timestamp: {differing}. The committed library and a freshly generated "
             "one are not the same library.")


if __name__ == "__main__":
    main()
