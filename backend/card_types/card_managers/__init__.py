from .front_back_back_front import FrontBackBackFront, DoubleSidedFormatted

__all__ = ["type_managers"]


type_managers = {
    "front-back-back-front": FrontBackBackFront,
    "double-sided-formatted": DoubleSidedFormatted
}