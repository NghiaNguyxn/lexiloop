from enum import Enum


class PartOfSpeech(str, Enum):
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PRONOUN = "pronoun"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    DETERMINER = "determiner"
    INTERJECTION = "interjection"
    NUMERAL = "numeral"
    AUXILIARY = "auxiliary"
    MODAL = "modal"
    PARTICLE = "particle"
    PHRASE = "phrase"
    IDIOM = "idiom"
    OTHER = "other"


class CEFRLevel(str, Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"
