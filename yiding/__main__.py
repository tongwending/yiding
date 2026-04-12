# ------------------------------------------------------------------------------
# __main__
# ------------------------------------------------------------------------------

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from . import commands


def _add_settings_arg(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "-s",
        "--settings",
        default=None,
        help="Path to a TOML settings file. If omitted, uses the package's settings.toml.",
    )


def _add_output_arg(p: argparse.ArgumentParser, default: str = "docx") -> None:
    p.add_argument(
        "-o",
        "--output-file",
        default=default,
        help="Output file format/extension passed to print_to_file (default: %(default)s).",
    )


def _add_bool_flag(
    p: argparse.ArgumentParser,
    *,
    name: str,
    default: bool,
    help_enable: str,
) -> None:
    """
    Adds --<name> / --no-<name> as a mutually exclusive pair, with a default.
    """
    g = p.add_mutually_exclusive_group()
    g.add_argument(f"--{name}", dest=name.replace("-", "_"), action="store_true", help=help_enable)
    g.add_argument(
        f"--no-{name}",
        dest=name.replace("-", "_"),
        action="store_false",
        help=f"Disable {help_enable.lower()}",
    )
    p.set_defaults(**{name.replace("-", "_"): default})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yiding",
        description="YiDing CLI (python -m yiding ...)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # ------------------------------------------------------------------
    # translate
    # ------------------------------------------------------------------
    p = sub.add_parser("translate", help="Translate a single Kanripo text.")
    p.add_argument("kanripo_code", help="Kanripo code (e.g., KR5h0008).")
    _add_settings_arg(p)
    p.add_argument("--translated-title", default=None, help="Override translated title.")
    _add_output_arg(p, default="docx")
    _add_bool_flag(p, name="table", default=True, help_enable="Include table output (where supported)")
    _add_bool_flag(p, name="punctuation", default=True, help_enable="Include punctuation in exported output")
    p.set_defaults(_handler="translate")

    # ------------------------------------------------------------------
    # translate-bulk
    # ------------------------------------------------------------------
    p = sub.add_parser("translate-bulk", help="Translate multiple Kanripo texts.")
    p.add_argument("kanripo_codes", nargs="+", help="One or more Kanripo codes.")
    _add_settings_arg(p)
    p.add_argument(
        "--translated-titles",
        nargs="*",
        default=None,
        help="Optional list of translated titles (must match number of codes).",
    )
    _add_output_arg(p, default="docx")
    _add_bool_flag(p, name="table", default=True, help_enable="Include table output (where supported)")
    _add_bool_flag(p, name="punctuation", default=True, help_enable="Include punctuation in exported output")
    p.set_defaults(_handler="translate-bulk")

    # ------------------------------------------------------------------
    # continue-translating
    # ------------------------------------------------------------------
    p = sub.add_parser("continue-translating", help="Resume translating from a saved pickle.")
    p.add_argument("picklefile", help="Pickle file containing a saved WorkflowOrchestrator.")
    _add_output_arg(p, default="docx")
    _add_bool_flag(p, name="table", default=True, help_enable="Include table output (where supported)")
    _add_bool_flag(p, name="punctuation", default=True, help_enable="Include punctuation in exported output")
    p.set_defaults(_handler="continue-translating")

    # ------------------------------------------------------------------
    # translate-anew
    # ------------------------------------------------------------------
    p = sub.add_parser(
        "translate-anew",
        help="Reload a saved pickle but re-run translation from scratch (punctuation disabled in settings).",
    )
    p.add_argument("picklefile", help="Pickle file containing a saved WorkflowOrchestrator.")
    _add_settings_arg(p)
    p.add_argument("--translated-title", default=None, help="Override translated title.")
    _add_output_arg(p, default="docx")
    _add_bool_flag(p, name="table", default=True, help_enable="Include table output (where supported)")
    _add_bool_flag(p, name="punctuation", default=True, help_enable="Include punctuation in exported output")
    p.set_defaults(_handler="translate-anew")

    # ------------------------------------------------------------------
    # punctuate
    # ------------------------------------------------------------------
    p = sub.add_parser("punctuate", help="Punctuate a single Kanripo text (no translation).")
    p.add_argument("kanripo_code", help="Kanripo code (e.g., KR5h0008).")
    _add_settings_arg(p)
    _add_output_arg(p, default="docx")
    p.set_defaults(_handler="punctuate")

    # ------------------------------------------------------------------
    # punctuate-bulk
    # ------------------------------------------------------------------
    p = sub.add_parser("punctuate-bulk", help="Punctuate multiple Kanripo texts (no translation).")
    p.add_argument("kanripo_codes", nargs="+", help="One or more Kanripo codes.")
    _add_settings_arg(p)
    _add_output_arg(p, default="docx")
    p.set_defaults(_handler="punctuate-bulk")

    # ------------------------------------------------------------------
    # continue-punctuating
    # ------------------------------------------------------------------
    p = sub.add_parser("continue-punctuating", help="Resume punctuating from a saved pickle.")
    p.add_argument("picklefile", help="Pickle file containing a saved WorkflowOrchestrator.")
    _add_output_arg(p, default="docx")
    p.set_defaults(_handler="continue-punctuating")

    # ------------------------------------------------------------------
    # get-settings
    # ------------------------------------------------------------------
    p = sub.add_parser(
        "get-settings",
        help="Copy the package settings.toml into the current working directory.",
    )
    p.set_defaults(_handler="get-settings")

    # ------------------------------------------------------------------
    # export
    # ------------------------------------------------------------------
    p = sub.add_parser("export", help="Export from a saved pickle without running models.")
    p.add_argument("picklefile", help="Pickle file containing a saved WorkflowOrchestrator.")
    _add_output_arg(p, default="docx")
    _add_bool_flag(p, name="table", default=False, help_enable="Include table output (where supported)")
    _add_bool_flag(p, name="punctuation", default=False, help_enable="Export punctuation")
    _add_bool_flag(p, name="translation", default=False, help_enable="Export translation")
    p.set_defaults(_handler="export")

    # ------------------------------------------------------------------
    # export-log
    # ------------------------------------------------------------------
    p = sub.add_parser("export-log", help="Export orchestrator log to a _LOG.txt file.")
    p.add_argument("picklefile", help="Pickle file containing a saved WorkflowOrchestrator.")
    p.set_defaults(_handler="export-log")

    # ------------------------------------------------------------------
    # update-glossary
    # ------------------------------------------------------------------
    p = sub.add_parser(
        "update-glossary",
        help="Merge translation glossary from a pickle into a base glossary CSV.",
    )
    p.add_argument("glossaryfile", help="Base glossary CSV file.")
    p.add_argument("picklefile", help="Pickle file containing a saved WorkflowOrchestrator.")
    p.add_argument(
        "-o",
        "--output-file",
        default=None,
        help="Optional output CSV path. If omitted, overwrites glossaryfile.",
    )
    p.set_defaults(_handler="update-glossary")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        h = getattr(args, "_handler")

        if h == "translate":
            commands.translate(
                args.kanripo_code,
                settings=args.settings,
                translated_title=args.translated_title,
                output_file=args.output_file,
                table=args.table,
                punctuation=args.punctuation,
            )
            return 0

        if h == "translate-bulk":
            if args.translated_titles is not None and len(args.translated_titles) == 0:
                # argparse gives [] if flag used with no values; treat as None
                args.translated_titles = None
            if args.translated_titles is not None and len(args.translated_titles) != len(args.kanripo_codes):
                raise ValueError(
                    "Error: --translated-titles count must match number of kanripo_codes "
                    f"({len(args.translated_titles)} != {len(args.kanripo_codes)})."
                )
            commands.translate_bulk(
                args.kanripo_codes,
                settings=args.settings,
                translated_titles=args.translated_titles,
                output_file=args.output_file,
                table=args.table,
                punctuation=args.punctuation,
            )
            return 0

        if h == "continue-translating":
            commands.continue_translating(
                args.picklefile,
                output_file=args.output_file,
                table=args.table,
                punctuation=args.punctuation,
            )
            return 0

        if h == "translate-anew":
            commands.translate_anew(
                args.picklefile,
                settings=args.settings,
                translated_title=args.translated_title,
                output_file=args.output_file,
                table=args.table,
                punctuation=args.punctuation,
            )
            return 0

        if h == "punctuate":
            commands.punctuate(
                args.kanripo_code,
                settings=args.settings,
                output_file=args.output_file,
            )
            return 0

        if h == "punctuate-bulk":
            commands.punctuate_bulk(
                args.kanripo_codes,
                settings=args.settings,
                output_file=args.output_file,
            )
            return 0

        if h == "continue-punctuating":
            commands.continue_punctuating(
                args.picklefile,
                output_file=args.output_file,
            )
            return 0
        
        if h == "get-settings":
            commands.get_settings()
            return 0

        if h == "export":
            commands.export(
                args.picklefile,
                punctuation=args.punctuation,
                translation=args.translation,
                output_file=args.output_file,
                table=args.table,
            )
            return 0

        if h == "export-log":
            commands.export_log(args.picklefile)
            return 0

        if h == "update-glossary":
            commands.update_glossary(
                args.glossaryfile,
                args.picklefile,
                output_file=args.output_file,
            )
            return 0

        parser.error(f"Unknown command handler: {h}")
        return 2

    except KeyboardInterrupt:
        return 130
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
