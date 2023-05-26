from difflib import SequenceMatcher


class Module:
    @staticmethod
    # returns the similarity % between two strings
    def similar(a, b):
        return SequenceMatcher(None, a, b).ratio()
