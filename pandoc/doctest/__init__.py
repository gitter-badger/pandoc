
# Python 2.7 Directives
from __future__ import absolute_import

# Python 2.7 Standard Library
import doctest
import json
from subprocess import Popen, PIPE
import sys

# Local Library
import pandoc

# This doctest extension require pandoc 1.16
from subprocess import Popen, PIPE
p = Popen(["pandoc", "-v"], stdout=PIPE)
if "pandoc 1.16" not in p.communicate()[0]:
    raise RuntimeError("pandoc 1.16 not found")

# ------------------------------------------------------------------------------

# Declare a new doctest directive: PANDOC 
PANDOC = doctest.register_optionflag("PANDOC")
doctest.PANDOC = PANDOC
doctest.__all__.append("PANDOC")
doctest.COMPARISON_FLAGS = doctest.COMPARISON_FLAGS | PANDOC

# Helpers
from subprocess import Popen, PIPE
import json
def to_json(txt):
    p = Popen(["pandoc", "-tjson"], 
              stdout=PIPE, stdin=PIPE, stderr=PIPE)
    json_string = p.communicate(input=txt.encode("utf-8"))[0]
    json_doc = json.loads(json_string)
    return json_doc

def linebreak(text, length=80):
    text = text.replace(u"\n", "")
    chunks = [text[i:i+length] for i in range(0, len(text), length)]
    return "\n".join(chunks) + "\n"

# Implement the pandoc output checker and monkey-patch doctest:
_doctest_OutputChecker = doctest.OutputChecker
class PandocOutputChecker(_doctest_OutputChecker):

    def round_trip_check(self, json_doc):
        json_doc_2 = None
        try:
            doc = pandoc.read(json_doc)
            json_doc_2 = pandoc.write(doc)
        except:
            pass
        return json_doc == json_doc_2   

    # TODO: manage the pandoc reads that may go wrong.

    def check_output(self, want, got, optionflags):
        if optionflags & PANDOC:
            want = want.replace("\n", "")
            json_got = to_json(eval(got)) # brittle. got may not be 
                                          # the representation of a string ...
            doc_got = pandoc.read(json_got) # may go wrong.
            got = repr(doc_got)
        super_check_output = _doctest_OutputChecker.check_output
        check = super_check_output(self, want, got, optionflags)
        if optionflags & PANDOC:
            check = check and self.round_trip_check(json_got)
        return check

    def output_difference(self, example, got, optionflags):
        if optionflags & PANDOC:
            json_got = to_json(eval(got)) # brittle (see above)
            if not self.round_trip_check(json_got):
                error = "Pandoc JSON Read+Write Error:"
                output_1 = json.dumps(json_got)
                output_2 = None
                try:
                    json_got_2 = pandoc.write(pandoc.read(json_got))
                    output_2 = json.dumps(json_got_2)
                except Exception as e:
                    return error + " " + e.message
                error += "\n\n{0}\ndiffers from:\n\n{1}\n"
                return error.format(linebreak(output_1), linebreak(output_2))
            else:
                example.want = linebreak(example.want, 76)
                got = linebreak(repr(pandoc.read(json_got)), 76)
        super_output_difference = _doctest_OutputChecker.output_difference
        return super_output_difference(self, example, got, optionflags)

doctest.OutputChecker = PandocOutputChecker

