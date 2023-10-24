from attrs import frozen
from twisted.logger import Logger


@frozen(kw_only=True)
class Indexer:
    """
    Radio Transmission Indexer
    """

    #
    # Class attributes
    #

    log = Logger()
