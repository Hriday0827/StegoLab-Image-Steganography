"""
shared/report_utils.py
-----------------------
Formatting helpers for terminal and file reports.
Used by all phases to produce consistent output.
"""

SEP  = "=" * 80
SEP2 = "-" * 80


def section(title: str) -> str:
    return f"\n{SEP2}\n  {title}\n{SEP2}"


def header(title: str, subtitle: str = "") -> str:
    lines = [SEP, f"  {title}"]
    if subtitle:
        lines.append(f"  {subtitle}")
    lines.append(SEP)
    return "\n".join(lines)


def format_pixel_table_header() -> str:
    return (
        f"  {'#':>6}  {'Row':>5}  {'Col':>5}  "
        f"{'R':>3}  {'G':>3}  {'B':>3}  "
        f"{'R-bin':>8}  {'G-bin':>8}  {'B-bin':>8}"
    )


def format_pixel_row(idx, row, col, r, g, b) -> str:
    return (
        f"  {idx:>6}  {row:>5}  {col:>5}  "
        f"{r:>3}  {g:>3}  {b:>3}  "
        f"{format(r,'08b'):>8}  {format(g,'08b'):>8}  {format(b,'08b'):>8}"
    )


def format_change_table_header() -> str:
    return (
        f"  {'Pixel#':>7}  {'Row':>5}  {'Col':>5}  {'Ch':>4}  "
        f"{'OldVal':>6}  {'NewVal':>6}  {'Diff':>5}  "
        f"{'Old-bin':>8}  {'New-bin':>8}  {'BitEmbed':>8}"
    )


def format_change_row(pixel_idx, row, col, ch_name,
                       old_val, new_val, bit_embedded) -> str:
    diff = new_val - old_val
    diff_str = f"{diff:+d}"
    return (
        f"  {pixel_idx:>7}  {row:>5}  {col:>5}  {ch_name:>4}  "
        f"{old_val:>6}  {new_val:>6}  {diff_str:>5}  "
        f"{format(old_val,'08b'):>8}  {format(new_val,'08b'):>8}  {bit_embedded:>8}"
    )
