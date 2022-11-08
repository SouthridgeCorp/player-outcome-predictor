import logging

from cricsheet_helper import parse_data

logging.basicConfig(level=logging.INFO)


def main():
    """
    The main function - Tournament list below must be updated before running the script.
    :return: None
    """
    parse_data("t20s", "International T20s")
    parse_data("apl", "Afghanistan Premier League")
    parse_data("bbl", "Big Bash League")
    parse_data("bpl", "Bangladesh Premier League")
    parse_data("cpl", "Caribbean Premier League")
    parse_data("ctc", "CSA T20 Challenge")
    parse_data("ipl", "Indian Premier League")
    parse_data("lpl", "Lanka Premier League")
    parse_data("psl", "Pakistan Super League")
    parse_data("ssm", "Super Smash")
    parse_data("ntb", "T20 Blast")
    parse_data("msl", "Mzansi Super League")


main()
