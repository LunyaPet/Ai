from math import log10
from os import environ
from random import randint, choices, choice
from sys import argv


def block(a, b, exc=tuple()):
    res = list(range(a, b + 1))
    l = len(res)
    i = 0
    while i < l:
        if res[i] in exc:
            res.pop(i)
            l -= 1
            i -= 1
        i += 1
    return list(map(chr, res))


BASIC_LATIN = block(0x0020, 0x007E)
LATIN_1_SUPPLEMENT = block(0x00A0, 0x00FF)
LATIN_EXTENDED_A = block(0x1000, 0x017F)
LATIN_EXTENDED_B = block(0x0180, 0x24F)
LATIN_EXTENDED_ADDITIONAL = block(0x1E00, 0x1EFF)
LATIN_EXTENDED_C = block(0x2C60, 0x2C7F)
LATIN_EXTENDED_D = block(0xA720, 0xA7B1)
CUNEIFORM = block(0x12000, 0x1236E)  # limited to those supported by Roboto

MATH_OPERATORS = block(0x2200, 0x22FF)
SUPPLEMENTAL_MATH_OPERATORS = block(0x2A00, 0x2AFF)
MATH_ALPHANUMERIC_SYMBOLS = block(
    0x1D400,
    0x1D7FF,
    (
        0x1D455,
        0x1D49D,
        0x1D4A0,
        0x1D4A1,
        0x1D4A3,
        0x1D4A4,
        0x1D4A7,
        0x1D4A8,
        0x1D4AD,
        0x1D4BA,
        0x1D4BC,
        0x1D4C4,
        0x1D506,
        0x1D50B,
        0x1D50C,
        0x1D515,
        0x1D51D,
        0x1D53A,
        0x1D53F,
        0x1D545,
        0x1D547,
        0x1D548,
        0x1D549,
        0x1D551,
        0x1D6A6,
        0x1D6A7,
        0x1D7CC,
        0x1D7CD,
    ),
)

KATAKANA = block(0x30A0, 0x30FF)
HIRAGANA = block(0x3041, 0x309F, (0x3097, 0x3098))

MYANMAR = block(0x1000, 0x109F)

CANADIAN_SYLLABARY = block(0x1400, 0x167F)

# not all greek characters, because im lazy
GREEK = block(0x0390, 0x03FF, (0x03A2,))
COPTIC = block(0x2C80, 0x2CFF, (0x2CF4, 0x2CF5, 0x2CF6, 0x2CF7, 0x2CF8))

DESERET = block(0x10400, 0x1044F)

GLAGOLITHIC = block(0x2C00, 0x2C5E)  # U+2C5F isn't displayed by Roboto

LATINS = (
    BASIC_LATIN
    + LATIN_1_SUPPLEMENT
    + LATIN_EXTENDED_A
    + LATIN_EXTENDED_B
    + LATIN_EXTENDED_ADDITIONAL
    + LATIN_EXTENDED_C
)  # + LATIN_EXTENDED_D

MATHS = MATH_OPERATORS + MATH_ALPHANUMERIC_SYMBOLS + SUPPLEMENTAL_MATH_OPERATORS

KANA = HIRAGANA + KATAKANA

PLEADING_EMOJIS = (
    "🥺",
    ":neofox_pleading: ",
    ":neofox_pleading_reach: ",
)

FLUSTERED_EMOJIS = (
    ">///<",
    ":33333",
    "😳😳",
    "😍😍",
    "nyaaa~~",
)  # not exhaustive

USER = environ.get('USER', environ.get('USERNAME'))

#### END OF CONSTANTS ####

"""
print_block = lambda x: print(*x, sep="", end="\n\n")
print_block(GLAGOLITHIC)
"""

def keysmash_ai():
    keysmash = "".join(
        choices(
            LATINS
            + CUNEIFORM
            + MATHS
            + KANA
            + CANADIAN_SYLLABARY
            + MYANMAR
            + GREEK
            + COPTIC
            + DESERET
            + GLAGOLITHIC,
            k=randint(10, 100),
        )
    )

    pleading = choice(PLEADING_EMOJIS) * int(log10(randint(0, 10000)))

    return f"{choice(FLUSTERED_EMOJIS)} {keysmash} {pleading}"
