# Pinned Decimal money standard

Fixture revision: decimal-money-v2

- Represent currency with Decimal throughout each calculation, including previews.
- Never convert monetary values to binary floating point. This is a high-severity standards violation because precision loss can make displayed or charged amounts incorrect.
