[object Object]

## Underlying spot comparison exception

If the derived validation source exposes a spot field but the selected rows contain no usable values, the reconciliation report must mark the comparison as `source_values_unavailable` and must not fabricate or forward-fill spot prices. The source is then corroborative for option-price fields only. A source that does provide a usable spot series must pass the explicit index-point tolerance. This exception does not affect canonical underlying data quality.
