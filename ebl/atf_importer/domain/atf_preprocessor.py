import codecs
import traceback
import re

from ebl.atf_importer.domain.atf_conversions import (
    Convert_Line_Dividers,
    Convert_Line_Joiner,
    Convert_Legacy_Grammar_Signs,
    Strip_Signs,
    Get_Lemma_Values_and_Guidewords,
    Get_Words,
    Line_Serializer,
)

from ebl.atf_importer.domain.atf_preprocessor_util import Util
from lark import Lark  # pyre-ignore[21]
import logging


class ATFPreprocessor:
    def __init__(self, logdir):
        self.EBL_PARSER = Lark.open(
            "../../transliteration/domain/ebl_atf.lark",
            maybe_placeholders=True,
            rel_to=__file__,
        )
        self.ORACC_PARSER = Lark.open(
            "lark-oracc/oracc_atf.lark", maybe_placeholders=True, rel_to=__file__
        )
        self.logger = logging.getLogger("Atf-Preprocessor")
        self.logger.setLevel(10)
        self.skip_next_lem_line = False
        self.unparseable_lines = []
        self.unused_lines = [
            "oracc_atf_at_line__object_with_status",
            "oracc_atf_at_line__surface_with_status",
            "oracc_atf_at_line__discourse",
            "oracc_atf_at_line__column",
            "dollar_line",
            "note_line",
            "control_line",
            "empty_line",
        ]
        self.stop_preprocessing = False
        self.logdir = logdir

    def do_atf_replacements(self,atf):
        atf = re.sub(
            "([\[<])([\*:])(.*)", r"\1 \2\3", atf
        )  # convert [* => [  <* => < *
        atf = re.sub("(\*)([\]>])(.*)", r"\1 \2\3", atf)  # convert *] => * ]  ?

        atf = atf.replace("\t", " ")  # convert tabs to spaces
        atf = " ".join(atf.split())  # remove multiple spaces

        return atf

    def line_not_converted(self,original_atf,atf):
        error = "Could not convert line"
        self.logger.error(error + ": " + atf)
        self.logger.error(traceback.format_exc())

        if "translation" in atf:
            self.stop_preprocessing = True

        self.unparseable_lines.append(original_atf)
        return (None, None, None, None)

    def check_original_line(self,atf):
        self.EBL_PARSER.parse(atf)

        # words serializer oracc parser
        tree = self.ORACC_PARSER.parse(atf)
        #self.logger.debug((tree.pretty()))

        words_serializer = Get_Words()
        words_serializer.result = []
        words_serializer.visit_topdown(tree)
        converted_line_array = words_serializer.result

        self.logger.info("Line successfully parsed, no conversion needed")
        self.logger.debug(
            "Parsed line as "
            + tree.data
        )
        self.logger.info(
            "----------------------------------------------------------------------"
        )
        return (atf, converted_line_array, tree.data, [])

    def unused_line(self,tree):
        for line in self.unused_lines:
            if tree.data == line:
                return self.get_empty_conversion(tree)

    def get_empty_conversion(self, tree):
        line_serializer = Line_Serializer()
        line_serializer.visit_topdown(tree)
        converted_line = line_serializer.line.strip(" ")
        return (converted_line, None, tree.data, None)

    def convert_line(self,original_atf,atf):

        tree = self.ORACC_PARSER.parse(atf)
        self.logger.debug("Converting " + tree.data)


        self.logger.debug((tree.pretty()))

        if tree.data == "lem_line":
            return self.convert_lemline(atf, tree)

        elif tree.data == "text_line":
            conversion_result = self.convert_textline(tree)
            return self.check_converted_line(original_atf, tree, conversion_result)

        else:
            return self.unused_line(tree)

    def convert_textline(self, tree):
        Convert_Line_Dividers().visit(tree)
        Convert_Line_Joiner().visit(tree)

        Convert_Legacy_Grammar_Signs().visit(tree)

        Strip_Signs().visit(tree)

        line_serializer = Line_Serializer()
        line_serializer.visit_topdown(tree)
        converted_line = line_serializer.line.strip(" ")

        words_serializer = Get_Words()
        words_serializer.result = []
        words_serializer.alter_lemline_at = []

        words_serializer.visit_topdown(tree)
        converted_line_array = words_serializer.result
        return (converted_line, converted_line_array, words_serializer.alter_lemline_at)

    def check_converted_line(self,original_atf,tree,conversion):
        try:
            self.EBL_PARSER.parse(conversion[0])
            self.logger.debug("Successfully parsed converted line")
            self.logger.debug(conversion[0])
            self.logger.debug(
                "Converted line as "
                + tree.data
                + " --> '"
                + conversion[0]
                + "'"
            )
            self.logger.debug(
                "----------------------------------------------------------------------"
            )

            return (
                conversion[0],
                conversion[1],
                tree.data,
                conversion[2]
            )

        except Exception as e:
            self.logger.error(traceback.format_exc())
            self.logger.error("Could not parse converted line")
            self.unparseable_lines.append(original_atf)
            return (None, None, None, None)

    def convert_lemline(self,atf,tree):

        if self.skip_next_lem_line:

            self.logger.warning("Skipping lem line")
            self.skip_next_lem_line = False
            return (None, None, "lem_line", None)

        lemmas_and_guidewords_serializer = Get_Lemma_Values_and_Guidewords()
        lemmas_and_guidewords_serializer.result = []
        lemmas_and_guidewords_serializer.visit(tree)
        lemmas_and_guidewords_array = (
            lemmas_and_guidewords_serializer.result
        )
        self.logger.debug(
            "Converted line as "
            + tree.data
            + " --> '"
            + str(lemmas_and_guidewords_array)
            + "'"
        )
        self.logger.debug(
            "----------------------------------------------------------------------"
        )

        return atf, lemmas_and_guidewords_array, tree.data, []

    def process_line(self, atf):
        self.logger.debug("Original line: '" + atf + "'")
        original_atf = atf

        try:
            if atf.startswith("#lem"):
                raise Exception

            # try to parse line with ebl-parser
            return self.check_original_line(atf)

        except Exception:

            atf = self.do_atf_replacements(atf)

            try:
                return self.convert_line(original_atf,atf)

            except Exception as e:
               return self.line_not_converted(original_atf,atf)

    def write_unparsable_lines(self,filename):
        with open(
                self.logdir + "unparseable_lines_" + filename + ".txt", "w", encoding="utf8"
        ) as outputfile:
            for key in self.unparseable_lines:
                outputfile.write(key + "\n")

    def read_lines(self,file):
        with codecs.open(file, "r", encoding="utf8") as f:
            atf_ = f.read()

        return atf_.split("\n")

    def convert_lines(self, file, filename):
        self.logger.info(Util.print_frame('Converting: "' + filename + '.atf"'))

        lines = self.read_lines(file)
        processed_lines = []
        for line in lines:
            (c_line, c_array, c_type, c_alter_lemline_at) = self.process_line(line)

            if self.stop_preprocessing:
                break

            if c_line is not None:
                processed_lines.append(
                    {
                        "c_line": c_line,
                        "c_array": c_array,
                        "c_type": c_type,
                        "c_alter_lemline_at": c_alter_lemline_at,
                    }
                )
            elif c_type is None and c_line is None:
                self.skip_next_lem_line = True

        self.logger.info(Util.print_frame("Preprocessing finished"))
        self.write_unparsable_lines(filename)

        return processed_lines
