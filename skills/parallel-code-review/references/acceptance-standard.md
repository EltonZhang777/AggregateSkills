# Pinned money standard

Fixture revision: decimal-preview-v1

- Represent currency with `Decimal` throughout each calculation, including
  previews.
- Never convert monetary values to binary floating point. Precision loss can
  make a displayed amount incorrect.
