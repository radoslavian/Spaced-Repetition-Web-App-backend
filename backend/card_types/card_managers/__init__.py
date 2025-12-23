from .front_back_back_front import FrontBackBackFront
from .double_sided_formatted import DoubleSidedFormatted
from .vocabulary import FormattedVocabulary


__all__ = ["type_managers", FrontBackBackFront, DoubleSidedFormatted,
           FormattedVocabulary]

type_managers = {
    "front-back-back-front": FrontBackBackFront,
    "double-sided-formatted": DoubleSidedFormatted,
    "formatted-vocabulary": FormattedVocabulary
}