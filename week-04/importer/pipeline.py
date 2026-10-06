"""Pipeline runner (provided). A pipe is simply the list handed from one filter to the next.

A filter is any callable  records: list[dict] -> list[dict].
"""


def run(pipeline_name, filters, records, log=print):
    """Push records through the filters in order; log how many records each stage kept."""
    log(f"[{pipeline_name}] input: {len(records)} records")
    for step in filters:
        before = len(records)
        records = step(records)
        name = getattr(step, "__name__", type(step).__name__)
        log(f"[{pipeline_name}] {name:<22} {before:>3} → {len(records):<3} (dropped {before - len(records)})")
    return records
