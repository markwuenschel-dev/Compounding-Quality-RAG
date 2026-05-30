from app.extract_intake_understanding import extract_intake_understanding
from app.schemas import (
    DosageForm,
    IntakeSource,
    RefusalReason,
    Species,
    SubmitterRole,
    SubmissionPurpose,
)


class FakeJSONClient:
    def __init__(self, response):
        self.response = response

    def complete_json(self, *args):
        assert args
        assert all(isinstance(arg, str) for arg in args)
        return self.response


def test_extract_intake_understanding_parses_supported_vomiting_concern() -> None:
    concern_text = (
        "My dog received chicken-flavored compounded oral liquid. "
        "About 10 minutes later he ran around frantically and vomited once."
    )

    client = FakeJSONClient(
        {
            "raw_intake": {
                "intake_source": "qre_general_question_form",
                "submitter_role": "customer",
                "submission_purpose": "customer_reported_concern",
                "concern_narrative": concern_text,
                "star_rating": None,
                "review_text_present": None,
                "submitter_selected_classification": None,
            },
            "product_context": {
                "species": "dog",
                "dosage_form": "oral_liquid",
                "product_placeholder": None,
                "flavor_or_attribute": "chicken-flavored",
                "bud_present": None,
                "batch_lot_present": None,
            },
            "possible_boundary_issue": None,
            "boundary_supporting_phrase": None,
            "extracted_customer_context": (
                "Dog received chicken-flavored compounded oral liquid, ran around "
                "frantically, and vomited once about 10 minutes after administration."
            ),
            "facts_present": [
                "Species is dog",
                "Dosage form is oral liquid",
                "Flavor is chicken-flavored",
                "Vomiting occurred about 10 minutes after administration",
                "Dog vomited once",
            ],
            "facts_missing": [
                "Medication or product name",
                "Dose administered",
                "Whether veterinarian was contacted",
            ],
        }
    )

    result = extract_intake_understanding(concern_text, client)

    assert result.raw_intake.intake_source == IntakeSource.QRE_GENERAL_QUESTION_FORM
    assert result.raw_intake.submitter_role == SubmitterRole.CUSTOMER
    assert result.raw_intake.submission_purpose == SubmissionPurpose.CUSTOMER_REPORTED_CONCERN
    assert result.raw_intake.concern_narrative == concern_text

    assert result.product_context.species == Species.DOG
    assert result.product_context.dosage_form == DosageForm.ORAL_LIQUID
    assert result.product_context.flavor_or_attribute == "chicken-flavored"

    assert result.possible_boundary_issue is None
    assert result.boundary_supporting_phrase is None
    assert result.extracted_customer_context is not None

    joined_present = " ".join(result.facts_present).lower()
    joined_missing = " ".join(result.facts_missing).lower()

    assert "dog" in joined_present
    assert "oral liquid" in joined_present
    assert "chicken" in joined_present
    assert "10 minutes" in joined_present
    assert "vomited once" in joined_present

    assert "dose" in joined_missing
    assert "veterinarian" in joined_missing


def test_extract_intake_understanding_detects_inventory_boundary() -> None:
    concern_text = (
        "A customer wants to know when this medication will be back in stock "
        "so they can order it again."
    )

    client = FakeJSONClient(
        {
            "raw_intake": {
                "intake_source": "qre_general_question_form",
                "submitter_role": "customer",
                "submission_purpose": "customer_reported_concern",
                "concern_narrative": concern_text,
                "star_rating": None,
                "review_text_present": None,
                "submitter_selected_classification": None,
            },
            "product_context": {
                "species": "unknown",
                "dosage_form": "unknown",
                "product_placeholder": None,
                "flavor_or_attribute": None,
                "bud_present": None,
                "batch_lot_present": None,
            },
            "possible_boundary_issue": "internal_record_access",
            "boundary_supporting_phrase": (
                "when this medication will be back in stock so they can order it again"
            ),
            "extracted_customer_context": (
                "Customer asks when the medication will be back in stock and available to order again."
            ),
            "facts_present": [
                "Customer asks about back-in-stock timing",
                "Customer asks about ordering the medication again",
            ],
            "facts_missing": [],
        }
    )

    result = extract_intake_understanding(concern_text, client)

    assert result.raw_intake.concern_narrative == concern_text
    assert result.product_context.species == Species.UNKNOWN
    assert result.product_context.dosage_form == DosageForm.UNKNOWN

    assert result.possible_boundary_issue == RefusalReason.INTERNAL_RECORD_ACCESS
    assert result.boundary_supporting_phrase is not None
    assert "back in stock" in result.boundary_supporting_phrase
    assert "order it again" in result.boundary_supporting_phrase

    joined_present = " ".join(result.facts_present).lower()
    assert "stock" in joined_present or "order" in joined_present


def test_extract_intake_understanding_detects_external_reference_boundary() -> None:
    concern_text = (
        "Can you check Plumb's or the package insert and tell me whether "
        "this dose range is safe for cats?"
    )

    client = FakeJSONClient(
        {
            "raw_intake": {
                "intake_source": "qre_general_question_form",
                "submitter_role": "customer",
                "submission_purpose": "customer_reported_concern",
                "concern_narrative": concern_text,
                "star_rating": None,
                "review_text_present": None,
                "submitter_selected_classification": None,
            },
            "product_context": {
                "species": "cat",
                "dosage_form": "unknown",
                "product_placeholder": None,
                "flavor_or_attribute": None,
                "bud_present": None,
                "batch_lot_present": None,
            },
            "possible_boundary_issue": "external_drug_reference",
            "boundary_supporting_phrase": "Plumb's or the package insert",
            "extracted_customer_context": (
                "Customer asks whether a dose range is safe for cats using Plumb's or the package insert."
            ),
            "facts_present": [
                "Species is cat",
                "Customer references Plumb's",
                "Customer references package insert",
                "Customer asks about dose range safety",
            ],
            "facts_missing": [],
        }
    )

    result = extract_intake_understanding(concern_text, client)

    assert result.product_context.species == Species.CAT
    assert result.possible_boundary_issue == RefusalReason.EXTERNAL_DRUG_REFERENCE
    assert result.boundary_supporting_phrase is not None

    supporting_phrase = result.boundary_supporting_phrase.lower()
    assert "plumb" in supporting_phrase
    assert "package insert" in supporting_phrase


def test_extract_intake_understanding_detects_clinical_or_legal_boundary() -> None:
    concern_text = "Did this medication cause my dog to die, and is Chewy liable?"

    client = FakeJSONClient(
        {
            "raw_intake": {
                "intake_source": "qre_general_question_form",
                "submitter_role": "customer",
                "submission_purpose": "customer_reported_concern",
                "concern_narrative": concern_text,
                "star_rating": None,
                "review_text_present": None,
                "submitter_selected_classification": None,
            },
            "product_context": {
                "species": "dog",
                "dosage_form": "unknown",
                "product_placeholder": None,
                "flavor_or_attribute": None,
                "bud_present": None,
                "batch_lot_present": None,
            },
            "possible_boundary_issue": "clinical_or_legal_conclusion",
            "boundary_supporting_phrase": "Did this medication cause my dog to die",
            "extracted_customer_context": (
                "Customer asks whether the medication caused the dog to die and whether Chewy is liable."
            ),
            "facts_present": [
                "Species is dog",
                "Customer asks whether medication caused death",
                "Customer asks whether Chewy is liable",
            ],
            "facts_missing": [],
        }
    )

    result = extract_intake_understanding(concern_text, client)

    assert result.product_context.species == Species.DOG
    assert result.possible_boundary_issue == RefusalReason.CLINICAL_OR_LEGAL_CONCLUSION
    assert result.boundary_supporting_phrase is not None

    joined_present = " ".join(result.facts_present).lower()
    assert "death" in joined_present or "die" in joined_present
    assert "liable" in joined_present