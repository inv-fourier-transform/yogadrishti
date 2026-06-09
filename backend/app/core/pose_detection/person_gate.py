"""Person count gating — ensure exactly one person is in the frame."""
from app.models.domain_schemas import LandmarkSet
from app.utils.exceptions import NoPersonDetectedError, MultiplePersonsError


def validate_single_person(landmark_sets: list[LandmarkSet], person_count: int) -> LandmarkSet:
    """
    Gate: exactly one person must be detected.
    Returns the single LandmarkSet.
    Raises NoPersonDetectedError or MultiplePersonsError.
    """
    if person_count == 0 or not landmark_sets:
        raise NoPersonDetectedError(
            "No person detected in the image. Please upload an image showing "
            "a person performing a yoga pose, with the full body visible."
        )
    if person_count > 1:
        raise MultiplePersonsError(
            f"Multiple people ({person_count}) detected in the image. "
            "Please upload an image with only one person performing a yoga pose."
        )
    return landmark_sets[0]
