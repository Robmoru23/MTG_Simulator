# utils/helpers.py
from typing import List

def wrap_text(text: str, font, max_width: int) -> List[str]:
    """Envuelve texto para que quepa en un ancho máximo"""
    words = text.split()
    lines, current = [], []
    for word in words:
        test = ' '.join(current + [word])
        if font.size(test)[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(' '.join(current))
            current = [word]
    if current:
        lines.append(' '.join(current))
    return lines