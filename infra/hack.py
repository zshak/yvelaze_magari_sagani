from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Protocol

from n2t.core import Disassembler as DefaultDisassembler
from n2t.infra.io import File, FileFormat


@dataclass
class HackProgram:
    path: Path
    cycles: int
    disassembler: Disassembler = field(default_factory=DefaultDisassembler.create)

    def __post_init__(self) -> None:
        FileFormat.hack.validate(self.path)

    @classmethod
    def load_from(cls, file_name: str, cycles: int) -> HackProgram:
        return cls(Path(file_name), cycles)

    def disassemble(self) -> None:
        File(FileFormat.asm.convert(self.path))
        self.disassembler.disassemble(self, self.cycles, self.path)

    def __iter__(self) -> Iterator[str]:
        yield from File(self.path).load()


class Disassembler(Protocol):  # pragma: no cover
    def disassemble(self, words: Iterable[str], cycles: int, f_path: Path) -> None:
        pass
