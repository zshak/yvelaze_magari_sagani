from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

from n2t.core.disassembler.chain import (
    AddressingDisassembler,
    AlphabetValidator,
    CommandDisassembler,
    DisassemblerChain,
    LengthValidator,
)
from n2t.core.disassembler.entities import Word

dest_table = {
    "null": "000",
    "A": "100",
    "D": "010",
    "M": "001",
    "AD": "110",
    "AM": "101",
    "MD": "011",
    "AMD": "111",
}

comp_table = {
    "0": "0101010",
    "1": "0111111",
    "-1": "0111010",
    "D": "0001100",
    "A": "0110000",
    "M": "1110000",
    "!D": "0001101",
    "!A": "0110001",
    "!M": "1110001",
    "-D": "0001111",
    "-A": "0110011",
    "-M": "1110011",
    "D+1": "0011111",
    "1+D": "0011111",
    "A+1": "0110111",
    "1+A": "0110111",
    "M+1": "1110111",
    "1+M": "1110111",
    "D-1": "0001110",
    "A-1": "0110010",
    "M-1": "1110010",
    "D+A": "0000010",
    "A+D": "0000010",
    "D+M": "1000010",
    "M+D": "1000010",
    "D-A": "0010011",
    "D-M": "1010011",
    "A-D": "0000111",
    "M-D": "1000111",
    "D&A": "0000000",
    "D&M": "1000000",
    "D|A": "0010101",
    "D|M": "1010101",
}

jump_table = {
    "null": "000",
    "JGT": "001",
    "JEQ": "010",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111",
}


# -----------------------------------
# -----------------------------------
# -----------------------------------


class SymbolTable:
    def __init__(self) -> None:
        self.symbol_dic: Dict[str, int] = {}
        self.running_memory_address: int = 16
        self.initialize_symbol_table()

    def initialize_symbol_table(self) -> None:
        for i in range(16):
            self.add("R" + str(i), i)
        self.add("SCREEN", 16384)
        self.add("KBD", 24576)
        self.add("SP", 0)
        self.add("LCL", 1)
        self.add("ARG", 2)
        self.add("THIS", 3)
        self.add("THAT", 4)

    def add(self, key: str, value: int) -> None:
        self.symbol_dic[key] = value

    def get_value(self, key: str) -> int:
        return self.symbol_dic.get(key, -1)


# ---------------------------------------------------
# ---------------------------------------------------


@dataclass
class Assembler:
    def assemble(self, assembly: List[str]) -> List[str]:
        symbol_table = SymbolTable()
        filtered_code: List[str] = self.parse_input(assembly, symbol_table)
        res = self.translate(filtered_code, symbol_table)
        return res

    def should_skip(self, word: str) -> bool:
        return word == "\n" or word == "" or word[0] == "/"

    def parse_input(
        self, assembly: Iterable[str], symbol_table: SymbolTable
    ) -> List[str]:
        res: List[str] = []
        index = 0
        for word in assembly:
            word = word.replace(" ", "")
            if self.should_skip(word):
                continue
            word = word.replace("\n", "")
            separator = "/"
            word = word.partition(separator)[0]
            # word is a valid input
            if word[0] == "(":
                word = word.strip("(,)")
                symbol_table.add(word, index)
                continue
            index += 1
            res.append(word)
        return res

    def translate(
        self, filtered_code: List[str], symbol_table: SymbolTable
    ) -> List[str]:
        res: List[str] = []
        for word in filtered_code:
            self.process_word(word, res, symbol_table)
        return res

    def process_word(
        self, word: str, res: List[str], symbol_table: SymbolTable
    ) -> None:
        res_str = ""
        if word[0] != "@":
            split_arr = re.split("[=;]", word)
            if len(split_arr) == 2:
                if split_arr[1][0] != "J":
                    res_str = (
                        "111"
                        + comp_table[split_arr[1]]
                        + dest_table[split_arr[0]]
                        + "000"
                    )
                else:
                    if not split_arr[0].isnumeric():
                        res_str = (
                            "111"
                            + comp_table[split_arr[0]]
                            + dest_table["null"]
                            + jump_table[split_arr[1]]
                        )
                    else:
                        res_str = (
                            "111"
                            + comp_table["0"]
                            + dest_table["null"]
                            + jump_table[split_arr[1]]
                        )

            else:
                res_str = (
                    "111"
                    + comp_table[split_arr[1]]
                    + dest_table[split_arr[0]]
                    + jump_table[split_arr[2]]
                )
            res.append(res_str)
            return

        # not instruction

        word = word[1:]
        if word.isnumeric():
            binary_string = str(format(int(word), "b"))
            binary_string = binary_string.zfill(16)
            res.append(binary_string)
            return
        if symbol_table.get_value(word) != -1:
            res_word = str(format(symbol_table.get_value(word), "b"))
            res_word = res_word.zfill(16)
            res.append(res_word)
        else:
            binary_string = str(format(symbol_table.running_memory_address, "b"))
            binary_string = binary_string.zfill(16)
            res.append(binary_string)
            symbol_table.add(word, symbol_table.running_memory_address)
            symbol_table.running_memory_address += 1
        return


class Simulator:
    assembler = Assembler()
    A: int = 0
    D: int = 0
    PC: int = 0

    Ram: List[int] = [0 for _ in range(65536)]
    Res: Dict[int, int] = {}
    instructions: List[str] = []

    def _read_file_to_list(self, file_path: str) -> List[str]:
        try:
            with open(file_path, "r") as file:
                content_list = file.readlines()
            return content_list
        except FileNotFoundError:
            print("File not found.")
            return []

    def beautify_hack(self) -> List[str]:
        res = []
        for inst in self.instructions:
            if self.assembler.should_skip(inst):
                continue
            inst = inst.strip()
            inst = inst.replace("\n", "")
            res.append(inst)
        return res

    def replace_negative(self) -> None:
        for k, v in self.Res.items():
            if v < 0:
                self.Res[k] = v + (1 << 16)

    def simulate(self, file_path: str, cycles: float | int) -> None:
        assembly = self._read_file_to_list(file_path)
        self.instructions = assembly
        if file_path.endswith(".hack"):
            self.instructions = self.beautify_hack()
        else:
            self.instructions = self.assembler.assemble(assembly)
        i = 0
        while i <= cycles:
            if self.PC == len(self.instructions):
                break
            self.process_instruction(self.instructions[self.PC])
            i += 1
        self.replace_negative()
        self.generate_json(file_path)

    def generate_json(self, output_file_path: str) -> None:
        directory_path = os.path.dirname(output_file_path)
        new_path = os.path.join(directory_path, "RamJson.json")
        with open(new_path, "w") as json_file:
            json.dump(self.Res, json_file, indent=4)

    def process_instruction(self, instruction: str) -> None:
        # c instruction
        if instruction[0] == "1":
            value = self.compute_value(instruction[3:10])
            self.store(value, instruction[10:13])
            self.jump(value, instruction[13:])
            return
        # A instruction
        else:
            self.A = int(instruction[1:], 2)
            self.PC += 1

            return

    def jump(self, value: int, inst: str) -> None:
        should_jump = False
        if inst == "001" and value > 0:
            should_jump = True
        elif inst == "010" and value == 0:
            should_jump = True
        elif inst == "011" and value >= 0:
            should_jump = True
        elif inst == "100" and value < 0:
            should_jump = True
        elif inst == "101" and not value == 0:
            should_jump = True
        elif inst == "110" and value <= 0:
            should_jump = True
        elif inst == "111":
            should_jump = True
        if should_jump:
            self.PC = self.A
        else:
            self.PC += 1

    def store(self, value: int, dest: str) -> None:
        if dest == "001":
            self.Ram[self.A] = value
            self.Res[self.A] = value

            return
        if dest == "010":
            self.D = value
            return
        if dest == "011":
            self.Ram[self.A] = value
            self.Res[self.A] = value
            self.D = value
            return
        if dest == "100":
            self.A = value
            return
        if dest == "101":
            self.A = value
            self.Ram[self.A] = value
            self.Res[self.A] = value
            return
        if dest == "110":
            self.A = value
            self.D = value
            return
        if dest == "111":
            self.A = value
            self.D = value
            self.Ram[self.A] = value
            self.Res[self.A] = value
            return

    def compute_value(self, comp: str) -> int:
        if comp == "0101010":
            return 0
        if comp == "0111111":
            return 1
        if comp == "0111010":
            return -1
        if comp == "0001100":
            return self.D
        if comp == "0110000":
            return self.A
        if comp == "0001101":
            st = str(self.A)
            return self.twos_comp(int(st, 2), len(st))
        if comp == "0011111":
            return self.D + 1
        if comp == "0110111":
            return self.A + 1
        if comp == "0001110":
            return self.D - 1
        if comp == "0110010":
            return self.A - 1
        if comp == "0000010":
            return self.D + self.A
        if comp == "0010011":
            return self.D - self.A
        if comp == "0000111":
            return self.A - self.D
        if comp == "0000000":
            return self.D & self.A
        if comp == "0010101":
            return self.D | self.A
        if comp == "1110000":
            return self.Ram[self.A]
        if comp == "1110001":
            st = str(self.Ram[self.A])
            return self.twos_comp(int(st, 2), len(st))
        if comp == "1110011":
            return -self.Ram[self.A]
        if comp == "1110111":
            return self.Ram[self.A] + 1
        if comp == "1110010":
            return self.Ram[self.A] - 1
        if comp == "1000010":
            return self.D + self.Ram[self.A]
        if comp == "1010011":
            return self.D - self.Ram[self.A]
        if comp == "1000111":
            return self.Ram[self.A] - self.D
        if comp == "1000000":
            return self.D & self.Ram[self.A]
        if comp == "1010101":
            return self.D | self.Ram[self.A]
        return 0

    def twos_comp(self, val: int, bits: int) -> int:
        if (val & (1 << (bits - 1))) != 0:
            val = val - (1 << bits)
        return val


@dataclass
class Disassembler:
    chain: DisassemblerChain

    @classmethod
    def create(cls) -> Disassembler:
        return cls(
            LengthValidator()
            | AlphabetValidator()
            | AddressingDisassembler()
            | CommandDisassembler()
        )

    def disassemble(self, words: Iterable[str], cycles: int, path: Path) -> None:
        sim = Simulator()
        if cycles == 0:
            sim.simulate(str(path), float("inf"))
        else:
            sim.simulate(str(path), cycles)

    def disassemble_one(self, word: str) -> str:
        return self.chain.disassemble(Word(word))
