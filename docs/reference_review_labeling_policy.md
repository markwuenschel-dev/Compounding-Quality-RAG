# Reference Review Labeling Policy

Status: confirmed  
Updated: 2026-06-25

This policy defines `api_reference_review_result` values for the public synthetic project.

The public project does not include real licensed drug-reference content, internal clinical guidance, manufacturer files, package inserts, proprietary formula details, or internal SOP text. A label may state that an outside reference was reviewed in the synthetic reviewer note, but the public project must not reproduce protected or licensed content.

## Controlled values

### `not_needed`

Use when reference review is irrelevant, not mentioned, or explicitly not needed.

### `synthetic_reference_consulted`

Use only when a reference included in the public project corpus was consulted.

### `external_reference_consulted`

Use when the reviewer note states that an outside source was already consulted and incorporated.

Examples:

- USP guidance;
- manufacturer information;
- internal clinical guidance;
- veterinary drug reference;
- commercial package insert.

Do not reproduce outside source content in the public project.

### `external_reference_needed`

Use when an outside source still needs to be reviewed before the investigation can be completed.

### `not_supported_by_public_corpus`

Use when the requested conclusion, answer, or disclosure cannot be supported through the public synthetic corpus.

Includes:

- supplier non-disclosure;
- manufacturer non-disclosure;
- proprietary-formula disclosure boundary;
- product-specific conclusion absent from public sources;
- request for real record, inventory, order, or customer-history access.

When outside information was reviewed but the requested supplier/manufacturer/proprietary information cannot be disclosed, this value overrides `external_reference_consulted`.

## Precedence

1. explicit unsupported or non-disclosure boundary;
2. completed external review;
3. completed synthetic reference review;
4. external review still required;
5. reference review not needed.

## Routing rule

An explicit supplier, manufacturer, or proprietary-formula disclosure boundary returns to the frontline pharmacist through:

```yaml
handling_path: respond_to_frontline_pharmacist
api_reference_review_result: not_supported_by_public_corpus
```

## Examples

| Reviewer note language | Label |
|---|---|
| `No reference review was needed.` | `not_needed` |
| `The public synthetic reference was reviewed.` | `synthetic_reference_consulted` |
| `USP guidance was reviewed and incorporated.` | `external_reference_consulted` |
| `Manufacturer stability information still needs to be checked.` | `external_reference_needed` |
| `Supplier details were not disclosed.` | `not_supported_by_public_corpus` |
| `USP was reviewed, but proprietary formula details cannot be disclosed.` | `not_supported_by_public_corpus` |

## Testing expectations

Keep regression tests for all five labels and for non-disclosure overriding completed external review.
