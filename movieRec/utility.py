from difflib import SequenceMatcher
import jellyfish


class Module:
    @staticmethod
    # returns the similarity % between two strings using Levenshtein Distance
    # distance == 0 => a equals b
    # distance == max(len(a),len(b)) => a completely different from b
    def levenshteinDistance(a, b):
        maxLength = 0
        if len(a) > len(b):
            maxLength = len(a)
        else:
            maxLength = len(b)
        # return the distance in percentage
        perc = jellyfish.levenshtein_distance(a, b) / maxLength
        return perc
