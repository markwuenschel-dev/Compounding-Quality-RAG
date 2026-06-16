from __future__ import annotations

import re
from enum import StrEnum

from app.schemas import (
    ApiReferenceReviewResult,
    InventoryInspectionResult,
    LotBatchPatternSummary,
    RecordReviewResult,
    ReviewSummary,
)


class ReviewSummaryScope(StrEnum):
    GUIDANCE_ONLY = "guidance_only"
    FULL_INVESTIGATION = "full_investigation"


_RECORD_RESULT_RE = re.compile(
    r"\b(?:compounding[- ]record review|record review|worksheet review|record and label review|"
    r"documentation (?:was |is )?(?:complete|incomplete)|"
    r"documented process or documentation discrepancy|"
    r"record(?:s)? (?:were |was )?(?:within specification|in spec|reviewed)|"
    r"formula and worksheet)\b",
    re.IGNORECASE,
)

_LOT_RESULT_RE = re.compile(
    r"\b(?:additional quality complaints|similar (?:lot|batch) complaints|"
    r"same[- ](?:lot|batch)|lot[- /]batch trend|lot trend|batch trend|"
    r"lot review|batch review|lot[- /]batch review|trend threshold|"
    r"source stock|lot or source stock|lot or batch)\b",
    re.IGNORECASE,
)

_NO_SIMILAR_LOT_PATTERN_RE = re.compile(
    r"\b(?:no additional quality complaints? (?:was|were) identified "
    r"for the lot(?: or source stock)?|"
    r"no similar (?:lot|batch) (?:concerns?|complaints?)|"
    r"no other (?:quality )?(?:concerns?|complaints?) (?:for|from) "
    r"the (?:lot|batch))\b",
    re.IGNORECASE,
)

_SAME_BATCH_PATTERN_RE = re.compile(
    r"\b(?:(?:one|two|three|four|five|\d+) additional quality complaints? "
    r"(?:was|were) identified for the lot|"
    r"similar (?:concern|complaint)s? (?:was|were )?(?:identified|found) "
    r"(?:for|in) the same (?:lot|batch)|"
    r"same[- ](?:lot|batch)[^.;\n]{0,80}"
    r"(?:similar|matching|additional) (?:concern|complaint))\b",
    re.IGNORECASE,
)

_INVENTORY_RESULT_RE = re.compile(
    r"\b(?:retained inventory|inventory (?:was |is )?(?:available|unavailable|"
    r"inspected|not inspected|not checked)|physically inspected|"
    r"direct inspection|inventory inspection|no inventory left|"
    r"inventory left|visual concern|fill concern|odor concern|"
    r"consistency concern)\b",
    re.IGNORECASE,
)

_REFERENCE_RESULT_RE = re.compile(
    r"\b(?:assessment incorporated|reference (?:was )?(?:consulted|reviewed|"
    r"needed|not needed)|external reference (?:consulted|needed|not needed)|"
    r"synthetic reference consulted|usp guidance|manufacturer information|"
    r"internal clinical guidance|veterinary drug reference|"
    r"commercial package insert|not supported by (?:the )?public corpus|"
    r"not disclosed|proprietary formula)\b",
    re.IGNORECASE,
)

_CLINICAL_EVENT_RE = re.compile(
    r"\b(?:vomit(?:ed|ing)?|diarrhea|blood(?:y)? (?:in )?(?:the )?stool|"
    r"hospitali[sz](?:ed|ation)|difficulty walking|trouble walking|weakness|"
    r"gagging|short of breath|difficulty breathing|respiratory distress|"
    r"sores?|skin irritation|ear irritation|hair loss|drool(?:ed|ing)?|"
    r"foaming|fell over|collapse(?:d)?|seizures?|ataxia|neurologic|"
    r"lethargy|appetite (?:decreased|loss)|got sick|adverse (?:event|effect)|"
    r"reaction)\b",
    re.IGNORECASE,
)

_PRODUCT_QUALITY_RE = re.compile(
    r"\b(?:smells? (?:weird|different|wrong|bad)|odor concern|pudding[- ]like|"
    r"too thick|thickened|watery|runny|cloudy|milky|clearer|separat(?:ed|ion)|"
    r"phase separation|caking|sediment|will not (?:mix|suspend|resuspend)|"
    r"won't (?:mix|suspend|resuspend)|color change|appearance change|"
    r"foreign material|contaminat(?:ed|ion)|mold|particulate|"
    r"broken|damaged|leak(?:ing|age)?|short fill|underfilled|"
    r"not enough medication|running out early|run out early|"
    r"below the \d+[- ]?ml line|only \d+(?:\.\d+)?\s*ml(?:s)? (?:was|were|left)|"
    r"wrong patient|wrong medication|dispensing error)\b",
    re.IGNORECASE,
)

_DEVICE_FAILURE_RE = re.compile(
    r"\b(?:pen|device|clicks?)\b[^.\n;]{0,100}"
    r"\b(?:not|no|nothing|less|fewer|reduced|inconsistent|broken|damaged|"
    r"leak(?:ing|age)?|air bubbles?|stuck|failed?|stopped|won't|wouldn't|"
    r"doesn't|didn't|wasn't|weren't|unable|unclear)\b"
    r"|\b(?:not|no|nothing|less|fewer|reduced|inconsistent|broken|damaged|"
    r"leak(?:ing|age)?|air bubbles?|stuck|failed?|stopped|won't|wouldn't|"
    r"doesn't|didn't|wasn't|weren't|unable|unclear)\b[^.\n;]{0,100}"
    r"\b(?:pen|device|clicks?|dispens(?:e|ed|ing)?|came out|pushing out)\b",
    re.IGNORECASE,
)

_EFFECTIVENESS_FAILURE_RE = re.compile(
    r"\b(?:therapeutic levels?|bloodwork|condition|response|efficacy)\b"
    r"[^.\n;]{0,100}\b(?:worsen(?:ed|ing)?|not (?:adjust|improve|respond)|"
    r"declin(?:e|ed|ing)|ineffective|not working|loss of effect)\b"
    r"|\b(?:worsen(?:ed|ing)?|not (?:adjust|improve|respond)|declin(?:e|ed|ing)|"
    r"ineffective|not working|loss of effect)\b[^.\n;]{0,100}"
    r"\b(?:therapeutic levels?|bloodwork|condition|response|efficacy)\b",
    re.IGNORECASE,
)

_FORMULATION_REACTION_RE = re.compile(
    r"\b(?:formulation|ingredient|manufacturer)\b[^.\n;]{0,120}"
    r"\b(?:changed?|different|reaction|sores?|irritation|sensitive)\b"
    r"|\b(?:reaction|sores?|irritation|sensitive)\b[^.\n;]{0,120}"
    r"\b(?:formulation|ingredient|manufacturer)\b",
    re.IGNORECASE,
)


def infer_review_summary_scope(
    *,
    concern_text: str,
    reviewer_note: str,
) -> ReviewSummaryScope:
    note = reviewer_note.strip()
    concern = concern_text.strip()

    if any(
        pattern.search(note)
        for pattern in (
            _RECORD_RESULT_RE,
            _LOT_RESULT_RE,
            _INVENTORY_RESULT_RE,
        )
    ):
        return ReviewSummaryScope.FULL_INVESTIGATION

    if any(
        pattern.search(concern)
        for pattern in (
            _CLINICAL_EVENT_RE,
            _PRODUCT_QUALITY_RE,
            _DEVICE_FAILURE_RE,
            _EFFECTIVENESS_FAILURE_RE,
            _FORMULATION_REACTION_RE,
        )
    ):
        return ReviewSummaryScope.FULL_INVESTIGATION

    return ReviewSummaryScope.GUIDANCE_ONLY


def apply_review_summary_defaults(
    summary: ReviewSummary,
    *,
    concern_text: str,
    reviewer_note: str,
) -> ReviewSummary:
    data = summary.model_dump(mode="json")
    scope = infer_review_summary_scope(
        concern_text=concern_text,
        reviewer_note=reviewer_note,
    )

    if not _RECORD_RESULT_RE.search(reviewer_note):
        data["record_review_result"] = (
            RecordReviewResult.DOCUMENTATION_INCOMPLETE.value
            if scope is ReviewSummaryScope.FULL_INVESTIGATION
            else RecordReviewResult.NOT_APPLICABLE.value
        )

    if _SAME_BATCH_PATTERN_RE.search(reviewer_note):
        data["lot_batch_pattern_summary"] = (
            LotBatchPatternSummary.SIMILAR_CONCERN_SAME_BATCH_FOUND.value
        )
    elif _NO_SIMILAR_LOT_PATTERN_RE.search(reviewer_note):
        data["lot_batch_pattern_summary"] = (
            LotBatchPatternSummary.NO_SIMILAR_BATCH_CONCERNS_FOUND.value
        )
    elif not _LOT_RESULT_RE.search(reviewer_note):
        data["lot_batch_pattern_summary"] = (
            LotBatchPatternSummary.UNAVAILABLE.value
            if scope is ReviewSummaryScope.FULL_INVESTIGATION
            else LotBatchPatternSummary.NOT_APPLICABLE.value
        )

    if not _INVENTORY_RESULT_RE.search(reviewer_note):
        data["inventory_inspection_result"] = (
            InventoryInspectionResult.NOT_CHECKED.value
            if scope is ReviewSummaryScope.FULL_INVESTIGATION
            else InventoryInspectionResult.NOT_APPLICABLE.value
        )

    if not _REFERENCE_RESULT_RE.search(reviewer_note):
        data["api_reference_review_result"] = (
            ApiReferenceReviewResult.NOT_NEEDED.value
        )

    return ReviewSummary.model_validate(data)
