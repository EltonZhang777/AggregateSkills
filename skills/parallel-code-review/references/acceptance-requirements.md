# Pinned requirements

Fixture revision: discounts-review-v1

Acceptance criteria:

- `SAVE10` is the only valid coupon. Reject every other code with an explicit
  invalid-coupon error. Returning the unchanged amount is not a rejection.
- The tax preview must use Decimal end-to-end and never convert money to binary
  floating point.

Impact context:

- The coupon path cannot grant an unintended discount or change the amount
  charged, but the caller cannot explain why an unknown code was ignored.
- The tax preview is display-only and is not persisted or charged. A float
  conversion can still show a misleading estimate.
