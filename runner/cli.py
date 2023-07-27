from typer import Typer, echo

from n2t.infra import HackProgram

cli = Typer(
    name="Nand 2 Tetris Software",
    no_args_is_help=True,
    add_completion=False,
)


@cli.command("execute", no_args_is_help=True)
def run_disassembler(hack_file: str, cycles: int = 0) -> None:
    echo(f"Disassembling {hack_file}")
    HackProgram.load_from(hack_file, cycles).disassemble()
    echo("Done!")


@cli.command("compile", no_args_is_help=True)
def handle_compile(jack: str) -> None:
    echo(jack)
