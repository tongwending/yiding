# ------------------------------------------------------------------------------
# __main__
# ------------------------------------------------------------------------------

from __future__ import annotations

import getpass
import argparse
import sys
from typing import Sequence

from . import commands


# ------------------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------------------


def _add_settings_arg(
    p: argparse.ArgumentParser,
) -> None:

    p.add_argument(
        "-s",
        "--settings",
        default=None,
        help=(
            "Path to a TOML settings file. "
            "If omitted, uses settings.toml in the "
            "current folder when available, otherwise "
            "the normal Yiding settings."
        ),
    )


def _add_output_arg(
    p: argparse.ArgumentParser,
    default: str = "docx",
) -> None:

    p.add_argument(
        "-o",
        "--output-file",
        default=default,
        help=(
            "Output format: docx or txt "
            "(default: %(default)s)."
        ),
    )


def _add_bool_flag(
    p: argparse.ArgumentParser,
    *,
    name: str,
    default: bool,
    help_enable: str,
) -> None:

    g = p.add_mutually_exclusive_group()

    g.add_argument(
        f"--{name}",
        dest=name.replace("-", "_"),
        action="store_true",
        help=help_enable,
    )

    g.add_argument(
        f"--no-{name}",
        dest=name.replace("-", "_"),
        action="store_false",
        help=f"Disable {help_enable.lower()}",
    )

    p.set_defaults(
        **{
            name.replace("-", "_"): default
        }
    )


def _decode_delimiter(
    value: str | None,
) -> str | None:

    if value is None:
        return None

    return (
        value
        .replace("\\r", "\r")
        .replace("\\n", "\n")
        .replace("\\t", "\t")
    )


# ------------------------------------------------------------------------------
# PARSER
# ------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        prog="yiding",
        description=(
            "Yiding CLI (python -m yiding ...)"
        ),
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # ------------------------------------------------------------------
    # create-yiding
    # ------------------------------------------------------------------

    p = sub.add_parser(
        "create-yiding",
        help=(
            "Create a Yiding project from supplied text."
        ),
    )

    p.add_argument(
        "projectfile",
        help="Yiding project file to create (*.yiding).",
    )

    p.add_argument(
        "--unpunctuated-text",
        default=None,
        help="Unpunctuated source text.",
    )

    p.add_argument(
        "--unpunctuated-divider",
        default=None,
        help=(
            "Segment delimiter for unpunctuated text. "
            "Use \\n for newline."
        ),
    )

    p.add_argument(
        "--unpunctuated-keep-divider",
        action="store_true",
        help=(
            "Keep the unpunctuated delimiter "
            "inside the resulting segments."
        ),
    )

    p.add_argument(
        "--unpunctuated-divider-is-whole-line",
        action="store_true",
        help=(
            "Treat the unpunctuated delimiter "
            "as a whole-line delimiter."
        ),
    )

    p.add_argument(
        "--punctuated-text",
        default=None,
        help="Existing punctuated text.",
    )

    p.add_argument(
        "--punctuated-divider",
        default=None,
        help=(
            "Segment delimiter for punctuated text. "
            "Use \\n for newline."
        ),
    )

    p.add_argument(
        "--punctuated-keep-divider",
        action="store_true",
        help=(
            "Keep the punctuated delimiter "
            "inside the resulting segments."
        ),
    )

    p.add_argument(
        "--punctuated-divider-is-whole-line",
        action="store_true",
        help=(
            "Treat the punctuated delimiter "
            "as a whole-line delimiter."
        ),
    )

    p.add_argument(
        "--translated-text",
        default=None,
        help="Existing translated text.",
    )

    p.add_argument(
        "--translation-divider",
        default=None,
        help=(
            "Segment delimiter for translated text. "
            "Use \\n for newline."
        ),
    )

    p.add_argument(
        "--translation-keep-divider",
        action="store_true",
        help=(
            "Keep the translation delimiter "
            "inside the resulting segments."
        ),
    )

    p.add_argument(
        "--translation-divider-is-whole-line",
        action="store_true",
        help=(
            "Treat the translation delimiter "
            "as a whole-line delimiter."
        ),
    )

    p.add_argument(
        "--original-title",
        default=None,
        help="Original title.",
    )

    p.add_argument(
        "--translated-title",
        default=None,
        help="Translated title.",
    )

    p.add_argument(
        "--translation-language",
        default=None,
        help=(
            "Language of an existing supplied translation."
        ),
    )

    p.add_argument(
        "--property",
        dest="properties",
        action="append",
        default=None,
        help=(
            "Project property. "
            "May be supplied more than once."
        ),
    )

    p.add_argument(
        "--structured",
        action="store_true",
        help=(
            "Mark supplied unpunctuated segments "
            "as meaningful aligned sections."
        ),
    )

    _add_settings_arg(p)

    p.set_defaults(
        _handler="create-yiding"
    )

    # ------------------------------------------------------------------
    # translate
    # ------------------------------------------------------------------

    p = sub.add_parser(
        "translate",
        help=(
            "Translate or resume translation "
            "of a Yiding project."
        ),
    )

    p.add_argument(
        "projectfile",
        help="Yiding project file (*.yiding).",
    )

    _add_settings_arg(p)
    _add_output_arg(
        p,
        default="docx",
    )

    _add_bool_flag(
        p,
        name="table",
        default=True,
        help_enable=(
            "Include table output where supported"
        ),
    )

    _add_bool_flag(
        p,
        name="punctuation",
        default=True,
        help_enable=(
            "Include punctuation in exported output"
        ),
    )

    p.set_defaults(
        _handler="translate"
    )

    # ------------------------------------------------------------------
    # translate-bulk
    # ------------------------------------------------------------------

    p = sub.add_parser(
        "translate-bulk",
        help=(
            "Translate or resume multiple "
            "Yiding projects."
        ),
    )

    p.add_argument(
        "projectfiles",
        nargs="+",
        help=(
            "One or more Yiding project files (*.yiding)."
        ),
    )

    _add_settings_arg(p)
    _add_output_arg(
        p,
        default="docx",
    )

    _add_bool_flag(
        p,
        name="table",
        default=True,
        help_enable=(
            "Include table output where supported"
        ),
    )

    _add_bool_flag(
        p,
        name="punctuation",
        default=True,
        help_enable=(
            "Include punctuation in exported output"
        ),
    )

    p.set_defaults(
        _handler="translate-bulk"
    )

    # ------------------------------------------------------------------
    # translate-anew
    # ------------------------------------------------------------------

    p = sub.add_parser(
        "translate-anew",
        help=(
            "Discard the existing translation "
            "and translate a Yiding project again."
        ),
    )

    p.add_argument(
        "projectfile",
        help="Yiding project file (*.yiding).",
    )

    _add_settings_arg(p)

    p.add_argument(
        "--translated-title",
        default=None,
        help="Override translated title.",
    )

    _add_output_arg(
        p,
        default="docx",
    )

    _add_bool_flag(
        p,
        name="table",
        default=True,
        help_enable=(
            "Include table output where supported"
        ),
    )

    _add_bool_flag(
        p,
        name="punctuation",
        default=True,
        help_enable=(
            "Include punctuation in exported output"
        ),
    )

    p.set_defaults(
        _handler="translate-anew"
    )

    # ------------------------------------------------------------------
    # translate-from-kanripo
    # ------------------------------------------------------------------

    p = sub.add_parser(
        "translate-from-kanripo",
        help=(
            "Create a Yiding project from Kanripo "
            "and translate it."
        ),
    )

    p.add_argument(
        "kanripo_code",
        help=(
            "Kanripo code "
            "(for example: KR5h0008)."
        ),
    )

    _add_settings_arg(p)

    p.add_argument(
        "--translated-title",
        default=None,
        help="Override translated title.",
    )

    p.add_argument(
        "--project-file",
        default=None,
        help=(
            "Optional path for the new Yiding project."
        ),
    )

    _add_output_arg(
        p,
        default="docx",
    )

    _add_bool_flag(
        p,
        name="table",
        default=True,
        help_enable=(
            "Include table output where supported"
        ),
    )

    _add_bool_flag(
        p,
        name="punctuation",
        default=True,
        help_enable=(
            "Include punctuation in exported output"
        ),
    )

    p.set_defaults(
        _handler="translate-from-kanripo"
    )

    # ------------------------------------------------------------------
    # translate-bulk-from-kanripo
    # ------------------------------------------------------------------

    p = sub.add_parser(
        "translate-bulk-from-kanripo",
        help=(
            "Create and translate multiple "
            "Yiding projects from Kanripo."
        ),
    )

    p.add_argument(
        "kanripo_codes",
        nargs="+",
        help="One or more Kanripo codes.",
    )

    _add_settings_arg(p)

    p.add_argument(
        "--translated-titles",
        nargs="*",
        default=None,
        help=(
            "Optional translated titles. "
            "The count must match the Kanripo codes."
        ),
    )

    _add_output_arg(
        p,
        default="docx",
    )

    _add_bool_flag(
        p,
        name="table",
        default=True,
        help_enable=(
            "Include table output where supported"
        ),
    )

    _add_bool_flag(
        p,
        name="punctuation",
        default=True,
        help_enable=(
            "Include punctuation in exported output"
        ),
    )

    p.set_defaults(
        _handler="translate-bulk-from-kanripo"
    )

    # ------------------------------------------------------------------
    # punctuate
    # ------------------------------------------------------------------

    p = sub.add_parser(
        "punctuate",
        help=(
            "Punctuate or resume punctuation "
            "of a Yiding project."
        ),
    )

    p.add_argument(
        "projectfile",
        help="Yiding project file (*.yiding).",
    )

    _add_settings_arg(p)
    _add_output_arg(
        p,
        default="docx",
    )

    p.set_defaults(
        _handler="punctuate"
    )

    # ------------------------------------------------------------------
    # punctuate-bulk
    # ------------------------------------------------------------------

    p = sub.add_parser(
        "punctuate-bulk",
        help=(
            "Punctuate or resume multiple "
            "Yiding projects."
        ),
    )

    p.add_argument(
        "projectfiles",
        nargs="+",
        help=(
            "One or more Yiding project files (*.yiding)."
        ),
    )

    _add_settings_arg(p)
    _add_output_arg(
        p,
        default="docx",
    )

    p.set_defaults(
        _handler="punctuate-bulk"
    )

    # ------------------------------------------------------------------
    # punctuate-from-kanripo
    # ------------------------------------------------------------------

    p = sub.add_parser(
        "punctuate-from-kanripo",
        help=(
            "Create a Yiding project from Kanripo "
            "and punctuate it."
        ),
    )

    p.add_argument(
        "kanripo_code",
        help=(
            "Kanripo code "
            "(for example: KR5h0008)."
        ),
    )

    _add_settings_arg(p)

    p.add_argument(
        "--project-file",
        default=None,
        help=(
            "Optional path for the new Yiding project."
        ),
    )

    _add_output_arg(
        p,
        default="docx",
    )

    p.set_defaults(
        _handler="punctuate-from-kanripo"
    )

    # ------------------------------------------------------------------
    # punctuate-bulk-from-kanripo
    # ------------------------------------------------------------------

    p = sub.add_parser(
        "punctuate-bulk-from-kanripo",
        help=(
            "Create and punctuate multiple "
            "Yiding projects from Kanripo."
        ),
    )

    p.add_argument(
        "kanripo_codes",
        nargs="+",
        help="One or more Kanripo codes.",
    )

    _add_settings_arg(p)
    _add_output_arg(
        p,
        default="docx",
    )

    p.set_defaults(
        _handler="punctuate-bulk-from-kanripo"
    )

    # ------------------------------------------------------------------
    # set-key
    # ------------------------------------------------------------------

    p = sub.add_parser(
        "set-key",
        help="Save an API key securely.",
    )

    p.add_argument(
        "provider",
        choices=("openai", "google"),
        help="API provider.",
    )

    p.set_defaults(
        _handler="set-key"
    )
    
    # ------------------------------------------------------------------
    # get-settings
    # ------------------------------------------------------------------

    p = sub.add_parser(
        "get-settings",
        help=(
            "Copy the package settings.toml "
            "into the current working directory."
        ),
    )

    p.set_defaults(
        _handler="get-settings"
    )

    # ------------------------------------------------------------------
    # export
    # ------------------------------------------------------------------

    p = sub.add_parser(
        "export",
        help=(
            "Export from a Yiding project "
            "without running models."
        ),
    )

    p.add_argument(
        "projectfile",
        help="Yiding project file (*.yiding).",
    )

    _add_output_arg(
        p,
        default="docx",
    )

    _add_bool_flag(
        p,
        name="table",
        default=False,
        help_enable=(
            "Include table output where supported"
        ),
    )

    _add_bool_flag(
        p,
        name="punctuation",
        default=False,
        help_enable="Export punctuation",
    )

    _add_bool_flag(
        p,
        name="translation",
        default=False,
        help_enable="Export translation",
    )

    p.set_defaults(
        _handler="export"
    )

    # ------------------------------------------------------------------
    # export-log
    # ------------------------------------------------------------------

    p = sub.add_parser(
        "export-log",
        help=(
            "Export the Yiding project log to TXT."
        ),
    )

    p.add_argument(
        "projectfile",
        help="Yiding project file (*.yiding).",
    )

    p.set_defaults(
        _handler="export-log"
    )

    # ------------------------------------------------------------------
    # update-glossary
    # ------------------------------------------------------------------

    p = sub.add_parser(
        "update-glossary",
        help=(
            "Merge the translation glossary from "
            "a Yiding project into a base glossary CSV."
        ),
    )

    p.add_argument(
        "glossaryfile",
        help="Base glossary CSV file.",
    )

    p.add_argument(
        "projectfile",
        help="Yiding project file (*.yiding).",
    )

    p.add_argument(
        "-o",
        "--output-file",
        default=None,
        help=(
            "Optional output CSV path. "
            "If omitted, overwrites glossaryfile."
        ),
    )

    p.set_defaults(
        _handler="update-glossary"
    )

    return parser


# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------


def main(
    argv: Sequence[str] | None = None,
) -> int:

    parser = build_parser()

    args = parser.parse_args(
        list(argv)
        if argv is not None
        else None
    )

    try:

        h = getattr(
            args,
            "_handler",
        )

        # --------------------------------------------------------------
        # create-yiding
        # --------------------------------------------------------------

        if h == "create-yiding":

            commands.create_yiding(
                args.projectfile,

                unpunctuated_text=(
                    args.unpunctuated_text
                ),
                unpunctuated_divider=(
                    _decode_delimiter(
                        args.unpunctuated_divider
                    )
                ),
                unpunctuated_keep_divider=(
                    args.unpunctuated_keep_divider
                ),
                unpunctuated_divider_is_whole_line=(
                    args.unpunctuated_divider_is_whole_line
                ),

                punctuated_text=(
                    args.punctuated_text
                ),
                punctuated_divider=(
                    _decode_delimiter(
                        args.punctuated_divider
                    )
                ),
                punctuated_keep_divider=(
                    args.punctuated_keep_divider
                ),
                punctuated_divider_is_whole_line=(
                    args.punctuated_divider_is_whole_line
                ),

                translated_text=(
                    args.translated_text
                ),
                translation_divider=(
                    _decode_delimiter(
                        args.translation_divider
                    )
                ),
                translation_keep_divider=(
                    args.translation_keep_divider
                ),
                translation_divider_is_whole_line=(
                    args.translation_divider_is_whole_line
                ),

                original_title=(
                    args.original_title
                ),
                translated_title=(
                    args.translated_title
                ),
                translation_language=(
                    args.translation_language
                ),

                properties=(
                    args.properties
                ),
                structured=(
                    args.structured
                ),

                settings=(
                    args.settings
                ),
            )

            return 0

        # --------------------------------------------------------------
        # translate
        # --------------------------------------------------------------

        if h == "translate":

            commands.translate(
                args.projectfile,
                settings=args.settings,
                output_file=args.output_file,
                table=args.table,
                punctuation=args.punctuation,
            )

            return 0

        # --------------------------------------------------------------
        # translate-bulk
        # --------------------------------------------------------------

        if h == "translate-bulk":

            commands.translate_bulk(
                args.projectfiles,
                settings=args.settings,
                output_file=args.output_file,
                table=args.table,
                punctuation=args.punctuation,
            )

            return 0

        # --------------------------------------------------------------
        # translate-anew
        # --------------------------------------------------------------

        if h == "translate-anew":

            commands.translate_anew(
                args.projectfile,
                settings=args.settings,
                translated_title=(
                    args.translated_title
                ),
                output_file=args.output_file,
                table=args.table,
                punctuation=args.punctuation,
            )

            return 0

        # --------------------------------------------------------------
        # translate-from-kanripo
        # --------------------------------------------------------------

        if h == "translate-from-kanripo":

            commands.translate_from_kanripo(
                args.kanripo_code,
                settings=args.settings,
                translated_title=(
                    args.translated_title
                ),
                output_file=args.output_file,
                table=args.table,
                punctuation=args.punctuation,
                projectfile=args.project_file,
            )

            return 0

        # --------------------------------------------------------------
        # translate-bulk-from-kanripo
        # --------------------------------------------------------------

        if h == "translate-bulk-from-kanripo":

            if (
                args.translated_titles
                is not None
                and len(
                    args.translated_titles
                ) == 0
            ):

                args.translated_titles = None

            if (
                args.translated_titles
                is not None
                and len(
                    args.translated_titles
                )
                != len(
                    args.kanripo_codes
                )
            ):

                raise ValueError(
                    "Error: --translated-titles "
                    "count must match the number "
                    "of Kanripo codes."
                )

            commands.translate_bulk_from_kanripo(
                args.kanripo_codes,
                settings=args.settings,
                translated_titles=(
                    args.translated_titles
                ),
                output_file=args.output_file,
                table=args.table,
                punctuation=args.punctuation,
            )

            return 0

        # --------------------------------------------------------------
        # punctuate
        # --------------------------------------------------------------

        if h == "punctuate":

            commands.punctuate(
                args.projectfile,
                settings=args.settings,
                output_file=args.output_file,
            )

            return 0

        # --------------------------------------------------------------
        # punctuate-bulk
        # --------------------------------------------------------------

        if h == "punctuate-bulk":

            commands.punctuate_bulk(
                args.projectfiles,
                settings=args.settings,
                output_file=args.output_file,
            )

            return 0

        # --------------------------------------------------------------
        # punctuate-from-kanripo
        # --------------------------------------------------------------

        if h == "punctuate-from-kanripo":

            commands.punctuate_from_kanripo(
                args.kanripo_code,
                settings=args.settings,
                output_file=args.output_file,
                projectfile=args.project_file,
            )

            return 0

        # --------------------------------------------------------------
        # punctuate-bulk-from-kanripo
        # --------------------------------------------------------------

        if h == "punctuate-bulk-from-kanripo":

            commands.punctuate_bulk_from_kanripo(
                args.kanripo_codes,
                settings=args.settings,
                output_file=args.output_file,
            )

            return 0

        # --------------------------------------------------------------
        # get-settings
        # --------------------------------------------------------------

        if h == "set-key":

            api_key = getpass.getpass(
                f"{args.provider.capitalize()} API key: "
            )

            commands.set_key(
                args.provider,
                api_key,
            )

            print(
                f"{args.provider.capitalize()} API key saved."
            )

            return 0

        # --------------------------------------------------------------
        # get-settings
        # --------------------------------------------------------------

        if h == "get-settings":

            commands.get_settings()

            return 0

        # --------------------------------------------------------------
        # export
        # --------------------------------------------------------------

        if h == "export":

            commands.export(
                args.projectfile,
                punctuation=args.punctuation,
                translation=args.translation,
                output_file=args.output_file,
                table=args.table,
            )

            return 0

        # --------------------------------------------------------------
        # export-log
        # --------------------------------------------------------------

        if h == "export-log":

            commands.export_log(
                args.projectfile
            )

            return 0

        # --------------------------------------------------------------
        # update-glossary
        # --------------------------------------------------------------

        if h == "update-glossary":

            commands.update_glossary(
                args.glossaryfile,
                args.projectfile,
                output_file=args.output_file,
            )

            return 0

        parser.error(
            f"Unknown command handler: {h}"
        )

        return 2

    except KeyboardInterrupt:

        return 130

    except Exception as e:

        print(
            str(e),
            file=sys.stderr,
        )

        return 1


# ------------------------------------------------------------------------------


if __name__ == "__main__":

    raise SystemExit(
        main()
    )
