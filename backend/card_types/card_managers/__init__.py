from .front_back_back_front import FrontBackBackFront
from .double_sided_formatted import DoubleSidedFormatted
from .occluded_cloze_deletion import OccludedClozeDeletion, \
    FormattedOccludedClozeDeletion
from .single_sided_formatted import SingleSidedFormatted
from .vocabulary import FormattedVocabulary


__all__ = ["type_managers", FrontBackBackFront, DoubleSidedFormatted,
           FormattedVocabulary, OccludedClozeDeletion]

type_managers = {
    "front-back-back-front": FrontBackBackFront,
    "double-sided-formatted": DoubleSidedFormatted,
    "formatted-vocabulary": FormattedVocabulary,
    "single-sided-formatted": SingleSidedFormatted,
    "occluded-cloze-deletion": OccludedClozeDeletion,
    "formatted-occluded-cloze-deletion": FormattedOccludedClozeDeletion
}