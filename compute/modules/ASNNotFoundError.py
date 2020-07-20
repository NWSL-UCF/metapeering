class ASNNotFoundError(Exception):
    """Exception raised for ASN not found in the peering DB.

    Attributes:
        ASN -- The ASN that was given as input
        message -- explanation of the error
    """

    def __init__(self, ASN, message="ASN Not found in the Peering DB"):
        self.ASN = ASN
        self.message = message
        super().__init__(self.message)