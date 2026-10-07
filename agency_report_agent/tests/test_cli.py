"""The command line."""

from agency_report_agent.__main__ import main
from agency_report_agent.demo import agency as demo


def test_cli_demo_draft_status_check(tmp_path, capsys):
    home = str(tmp_path / "ws")
    assert main(["--home", home, "demo"]) == 0
    assert main(["--home", home, "demo"]) == 1                     # refuses to load twice
    assert main(["--home", home, "draft", demo.PERIOD]) == 0
    out = capsys.readouterr().out
    assert out.count("Ready for review") == 12
    assert main(["--home", home, "status", demo.PERIOD]) == 0
    draft = tmp_path / "d.md"
    draft.write_text("Paid search delivered 110 enquiries in September.\n")
    assert main(["--home", home, "check", "brightwave-dental", demo.PERIOD, str(draft)]) == 0
    draft.write_text("Paid search delivered 111 enquiries in September.\n")
    assert main(["--home", home, "check", "brightwave-dental", demo.PERIOD, str(draft)]) == 2
    assert "doesn't match" in capsys.readouterr().out


def test_cli_import(tmp_path, capsys):
    from agency_report_agent.desk import Desk
    home = tmp_path / "ws"
    d = Desk(home)
    d.store.create_client("Seaview Physio")
    d.close()
    f = tmp_path / "ga4.csv"
    c = demo.client_def("kestrel-accounting")
    f.write_bytes(demo.build_exports(c, demo.PERIOD)["ga4"])
    assert main(["--home", str(home), "import", "seaview-physio", demo.PERIOD, "ga4", str(f)]) == 0
    f.write_bytes(b"not,a,ga4\n1,2,3\n")
    assert main(["--home", str(home), "import", "seaview-physio", demo.PERIOD, "ga4", str(f)]) == 1
