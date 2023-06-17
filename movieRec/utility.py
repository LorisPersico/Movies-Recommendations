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

    # J(A, B) = |A ∩ B| / |A ∪ B|
    @staticmethod
    def jaccardSim(list1, list2):
        set1 = set(list1)
        set2 = set(list2)
        union = set1 | set2
        intersection = set1 & set2
        return len(intersection) / len(union)

    # K(A ,B) = (|A ∩ B| / |A|) + (|A ∩ B| / |B|) / 2
    @staticmethod
    def kulczynskiSim(list1, list2):
        set1 = set(list1)
        set2 = set(list2)
        intersection = set1 & set2
        len1 = len(set1)
        len2 = len(set2)

        if len1 == 0 or len2 == 0:
            return 0

        similarity = (len(intersection) / len1 + len(intersection) / len2) * 0.5
        return similarity

    posterNotFoundUrl = 'https://www.prokerala.com/movies/assets/img/no-poster-available.jpg'
