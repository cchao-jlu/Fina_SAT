from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FONT_REGULAR = "/home/sunshixin/.local/share/fonts/static/NotoSansSC-Regular.ttf"
FONT_BOLD = "/home/sunshixin/.local/share/fonts/static/NotoSansSC-Bold.ttf"


def add_font(path: str) -> str:
    font_manager.fontManager.addfont(path)
    return font_manager.FontProperties(fname=path).get_name()


def draw_three_line_table() -> None:
    font_name = add_font(FONT_REGULAR)
    font_bold = font_manager.FontProperties(fname=FONT_BOLD)
    plt.rcParams["font.family"] = font_name
    plt.rcParams["axes.unicode_minus"] = False

    columns = ["规模", "RLAF 基线", "Balanced Improver", "本文方法"]
    rows = [
        ["300", "200/200, 7.506s", "200/200, 4.684s", "200/200, 7.272s"],
        ["350", "108/200, 34.593s", "132/200, 30.961s", "109/200, 33.815s"],
        ["400", "50/200, 47.730s", "52/200, 45.975s", "56/200, 45.498s"],
    ]

    fig, ax = plt.subplots(figsize=(10.8, 3.8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    title = "RLAF、Balanced Improver 与本文方法在 3SAT 测试集上的 60 秒口径结果"
    ax.text(
        0.5,
        0.93,
        title,
        ha="center",
        va="center",
        fontsize=15,
        fontproperties=font_bold,
    )

    left, right = 0.06, 0.94
    top = 0.78
    header_y = 0.69
    mid = 0.61
    row_ys = [0.51, 0.41, 0.31]
    bottom = 0.23
    col_x = [0.12, 0.34, 0.58, 0.82]

    ax.hlines(top, left, right, linewidth=1.4, color="black")
    ax.hlines(mid, left, right, linewidth=0.9, color="black")
    ax.hlines(bottom, left, right, linewidth=1.4, color="black")

    for x, col in zip(col_x, columns):
        ax.text(
            x,
            header_y,
            col,
            ha="center",
            va="center",
            fontsize=12.5,
            fontproperties=font_bold,
        )

    for y, row in zip(row_ys, rows):
        for x, text in zip(col_x, row):
            ax.text(x, y, text, ha="center", va="center", fontsize=12)

    note = (
        "注：结果格式为“解出实例数/总实例数，平均求解时间”。"
        "Balanced Improver 的 60 秒结果来自历史长跑记录的事后截断诊断；"
        "本文方法在 300/350 使用 Online-Consistent Selector，在 400 使用带候选保护的 Local Boundary Correction。"
    )
    ax.text(
        left,
        0.12,
        note,
        ha="left",
        va="top",
        fontsize=9.2,
        wrap=True,
    )

    pdf_path = OUT_DIR / "rlaf_balanced_ours_three_line_table.pdf"
    png_path = OUT_DIR / "rlaf_balanced_ours_three_line_table.png"
    fig.savefig(pdf_path, bbox_inches="tight", pad_inches=0.2)
    fig.savefig(png_path, dpi=240, bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)
    print(pdf_path)
    print(png_path)


if __name__ == "__main__":
    draw_three_line_table()
