# Reference Review Labeling Policy

Status: confirmed

## Controlled values

### `not_needed`

Use when reference review is irrelevant or the investigation explicitly states
that no reference review was needed.

### `synthetic_reference_consulted`

Use only when a reference included in the public project corpus was consulted.

### `external_reference_consulted`

Use when the pharmacist already consulted an outside source and incorporated it
into the investigation. Examples include USP guidance, manufacturer
information, internal clinical guidance, a veterinary drug reference, or a
commercial package insert.

### `external_reference_needed`

Use when an outside source still needs to be reviewed before the investigation
can be completed.

### `not_supported_by_public_corpus`

Use when the requested conclusion or information cannot be provided through the
public corpus. This includes explicit supplier or manufacturer non-disclosure
and a full proprietary-formula disclosure boundary.

When outside information was reviewed but the requested supplier or proprietary
information cannot be disclosed, this value overrides
`external_reference_consulted`.

## Precedence

1. Explicit unsupported or non-disclosure boundary
2. Completed external review
3. Completed synthetic reference review
4. External review still required
5. Reference review not needed

## Routing rule

An explicit supplier, manufacturer, or proprietary-formula disclosure boundary
returns to the frontline pharmacist through `respond_to_frontline_pharmacist`.
