# Pinned requirements

Fixture revision: pricing-review-v3

Fixture impact context:
- Valid purchases and the SAVE10 coupon are unaffected.
- The checkout caller displays the returned total without a separate invalid-code message, so users cannot learn why their coupon was ignored. This creates moderate checkout confusion, retries, or support friction, but it does not change the amount charged or grant a discount.
- The tax preview is the tax-inclusive estimate shown before purchase confirmation and informs the customer's affordability decision. It is display-only, never passed to invoice creation or persisted, and cannot change the charge; its moderate impact is limited to a misleading estimate or price dispute.

Acceptance criteria:
- SAVE10 is the only valid coupon. Reject an unknown code with an explicit invalid-coupon error. Returning the total unchanged for an unknown code still counts as accepting it.
- The tax preview must use Decimal end-to-end so its displayed amount preserves exact decimal values.
