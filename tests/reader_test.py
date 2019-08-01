from ir.reader import read_ir
from ir.writer import write_ir


def test_tokenize_comments():
    script_source = "(equal 7 (+ 5 ;foo bar\n   2))"
    expected_output = "(equal 7 (+ 5 2))"
    t = read_ir(script_source)
    s = write_ir(t)
    assert s == expected_output
