from agent_lab import main


def test_main_runs(capsys):
    main()
    captured = capsys.readouterr()
    assert "agent-lab" in captured.out
