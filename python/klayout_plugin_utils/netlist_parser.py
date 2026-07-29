# MIT License
# 
# Copyright (c) 2025–2026 Rohan Chadhury
# Copyright (c) 2026 Martin Jan Köhler (implicit top cell modifications)
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


"""Core parser implementation for netlist_parser."""

from __future__ import annotations

import os
import re
from typing import Dict, List, Optional, Set, Union

# from .utils import warning
warning = print

__all__ = [
    "NetlistError",
    "Netlist",
    "NetlistCell",
    "DeviceInstance",
    "NetlistParser",
]

ALLOWED_EXTENSIONS = {".cir", ".scs", ".spi", ".cdl", ".spf", ".sp", ".hsp"}


class NetlistError(Exception):
    """Raised when a netlist file cannot be found, opened, or parsed."""


class Netlist:
    """Container for data parsed from a complete netlist file."""

    def __init__(self) -> None:
        self.cells: List[NetlistCell] = []
        self.version: Optional[str] = None
        self.resistance: Dict = {}
        self.capacitance: Dict = {}
        self.layer_map: Dict = {}
        self.implicit_top_cell: Optional[NetlistCell] = None

    @property
    def all_cells(self) -> List[NetlistCell]:
        """Include the implicit_top_cell"""
        if self.implicit_top_cell:
            return self.cells + [self.implicit_top_cell]
        return self.cells


class NetlistCell:
    """Corresponds to one subckt block in a netlist file."""

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.ports: List[str] = []
        self.instances: List[DeviceInstance] = []
        self.substitute: Dict[str, str] = {}

    def __str__(self) -> str:
        return self.name


class DeviceInstance:
    """Holds data parsed from one instance line inside a subckt."""

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.code: str = name[0].lower()
        self.nodes: List[str] = []
        self.device_name: Optional[str] = None
        self.number: Optional[str] = None
        self.parameters: Dict[str, str] = {}

    def __str__(self) -> str:
        return self.name


class NetlistParser:
    """Parser for SPICE-family netlist files (.spi, .cir, .cdl, .scs, .spf, .sp, .hsp).

    Parameters
    ----------
    internal:
        When *False* (default) cells that appear both as a subckt definition
        and as a device reference (i.e. internal/hierarchical cells) are
        excluded from the output of :meth:`read`.
    """

    def __init__(self, internal: bool = False) -> None:
        self.internal = internal

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, 
              filename: str, 
              data=None,
              implicit_top_cell_name: Optional[str] = None) -> Netlist:
        """Parse *filename* and return a :class:`Netlist` object.

        Parameters
        ----------
        filename:
            Path to a netlist file.
        data:
            Optional hint used when called from :meth:`read`; affects error
            handling for lines outside of subckt blocks.

        Raises
        ------
        NetlistError
            If the file cannot be found or opened.
        """
        if not os.path.isfile(filename):
            raise NetlistError(
                f"Could not find file, please check file name: {filename}"
            )
        try:
            netlist_file = open(filename, "r")
        except OSError as exc:
            raise NetlistError(f"Could not read file: {filename}") from exc

        netlist = Netlist()
        netlist.version = filename.rsplit(".", 1)[-1].lower()
        in_subckt = False
        tag_main_port: Optional[str] = None

        line = netlist_file.readline()
        while line:
            next_line = netlist_file.readline()
            line = line.lstrip().rstrip()

            if not line:
                line = next_line
                continue

            # ---- Line continuation: ends with '\' ----
            if line.endswith("\\"):
                continuation = next_line[1:] if next_line.startswith("+") else next_line
                line = line[:-1] + " " + continuation.lstrip().rstrip()
                continue

            # ---- Line continuation: next line starts with '+' ----
            if next_line and next_line.startswith("+"):
                line = line + " " + next_line[1:].lstrip().rstrip()
                continue

            # ---- Spectre: remove parentheses ----
            if netlist.version == "scs":
                line = line.replace("(", "").replace(")", "")

            # ---- Layer map (*N name) ----
            if re.search(r"^\*\d+\s+", line):
                m = re.search(r"^\*(\d+)\s+(\S+)", line)
                if m:
                    layer_number = m.group(1)
                    layer_name = re.sub(r":.*", "", m.group(2))
                    netlist.layer_map[layer_number] = layer_name

            # ---- Start of subckt ----
            elif line.startswith(("subckt", ".subckt", ".SUBCKT")):
                in_subckt = True
                tokens = line.split()
                cell = NetlistCell(tokens[1])
                existing_names = {c.name for c in netlist.cells}
                if cell.name in existing_names:
                    line = next_line
                    continue
                for token in tokens[2:]:
                    if "=" in token:
                        variable, subst = token.split("=", 1)
                        cell.substitute[variable] = subst
                    else:
                        cell.ports.append(token)
                netlist.cells.append(cell)

            # ---- Device instance lines ----
            elif line and line[0].lower() in {"d", "x", "m", "c", "r"}:
                in_spf = False
                # SPF capacitance data lines (e.g. "C10_5 n1 n2 1.23e-18")
                if re.search(r"^C.*_", line):
                    m = re.search(r"^C.*_.*\s(\S+)\s(\S+)\s(\S+)", line)
                    if m:
                        con1 = m.group(1)
                        con2 = m.group(2)
                        capacitance_val = m.group(3)
                        if con1 == "0":
                            con1 = "ground"
                        if con2 == "0":
                            con2 = "ground"
                        self._process_spf_capacitance(
                            netlist, con1, con2, capacitance_val
                        )
                    in_spf = True
                # SPF resistance data lines (e.g. "R1_5 n1 n2 50.0")
                elif re.search(r"^R\d+_", line):
                    m = re.search(r"^R.*?\s(\S+)\s(\S+)\s(\S+)", line)
                    if m:
                        con1 = m.group(1)
                        con2 = m.group(2)
                        resistance_val = m.group(3)
                        self._process_spf_resistance(
                            netlist, con1, con2, resistance_val
                        )
                    in_spf = True
                
                if not in_spf:
                    if in_subckt:
                        self._instance_parse(line, netlist.version, netlist.cells[-1])
                    elif implicit_top_cell_name:
                        if netlist.implicit_top_cell is None:
                            netlist.implicit_top_cell = NetlistCell(implicit_top_cell_name)
                        self._instance_parse(line, netlist.version, netlist.implicit_top_cell)

            # ---- SPF *|NET annotation ----
            elif line.startswith("*|NET"):
                m = re.search(r".*NET\s(\S+)\s+(\S+)", line)
                if m:
                    main_port = m.group(1)
                    main_cap = m.group(2)
                    tag_main_port = main_port
                    netlist.resistance.setdefault(main_port, {})
                    netlist.capacitance.setdefault(main_port, {})
                    netlist.capacitance[main_port]["net_cap"] = main_cap
                    netlist.resistance[main_port].setdefault("main_interface", "")
                    netlist.capacitance[main_port].setdefault("main_interface", "")
                    netlist.resistance[main_port].setdefault("sub_interfaces", [])
                    netlist.capacitance[main_port].setdefault("sub_interfaces", [])
                    netlist.resistance[main_port].setdefault("ports", {})
                    netlist.capacitance[main_port].setdefault("ports", {})

            # ---- SPF *|P port layer annotation ----
            elif line.startswith("*|P "):
                m = re.search(r".*P\s\((\S+)\s.*\$lvl=(\S+)", line)
                if m:
                    main_port = m.group(1)
                    layer_number = m.group(2)
                    if main_port in netlist.resistance and layer_number in netlist.layer_map:
                        new_interface = netlist.layer_map[layer_number]
                        netlist.resistance[main_port]["main_interface"] = new_interface
                        netlist.resistance[main_port].setdefault(new_interface, [])
                    if main_port in netlist.capacitance and layer_number in netlist.layer_map:
                        new_interface = netlist.layer_map[layer_number]
                        netlist.capacitance[main_port]["main_interface"] = new_interface

            # ---- SPF *|S sub-port layer annotation ----
            elif line.startswith("*|S "):
                m = re.search(r".*S\s\((\S+)\s.*\$lvl=(\S+)", line)
                if m:
                    sub_port = m.group(1)
                    main_port = re.sub(r":\d+", "", sub_port)
                    layer_number = m.group(2)
                    if layer_number in netlist.layer_map:
                        new_interface = netlist.layer_map[layer_number]
                        if ":" not in sub_port and sub_port in netlist.resistance:
                            if netlist.resistance[sub_port].get("main_interface") == "":
                                netlist.resistance[sub_port]["main_interface"] = new_interface
                        if ":" not in sub_port and sub_port in netlist.capacitance:
                            if netlist.capacitance[sub_port].get("main_interface") == "":
                                netlist.capacitance[sub_port]["main_interface"] = new_interface
                        if main_port in netlist.resistance:
                            netlist.resistance[main_port].setdefault(new_interface, [])
                            if sub_port not in netlist.resistance[main_port]["ports"]:
                                netlist.resistance[main_port]["ports"][sub_port] = new_interface
                                if new_interface not in netlist.resistance[main_port]["sub_interfaces"]:
                                    netlist.resistance[main_port]["sub_interfaces"].append(new_interface)
                        if main_port in netlist.capacitance:
                            if sub_port not in netlist.capacitance[main_port]["ports"]:
                                netlist.capacitance[main_port]["ports"][sub_port] = new_interface
                                if new_interface not in netlist.capacitance[main_port]["sub_interfaces"]:
                                    netlist.capacitance[main_port]["sub_interfaces"].append(new_interface)

            # ---- SPF *|I internal port annotation ----
            elif line.startswith("*|I "):
                m = re.search(r".*I\s\((\S+)\s.*\$lvl=(\S+)", line)
                if m and tag_main_port is not None:
                    sub_port = m.group(1)
                    layer_number = m.group(2)
                    if layer_number in netlist.layer_map:
                        new_interface = netlist.layer_map[layer_number]
                        if tag_main_port in netlist.resistance:
                            if sub_port not in netlist.resistance[tag_main_port]["ports"]:
                                netlist.resistance[tag_main_port]["ports"][sub_port] = new_interface
                        if tag_main_port in netlist.capacitance:
                            if sub_port not in netlist.capacitance[tag_main_port]["ports"]:
                                netlist.capacitance[tag_main_port]["ports"][sub_port] = new_interface

            # ---- End of subckt ----
            elif line.startswith(("end", ".end", ".END", "ends", ".ENDS")):
                in_subckt = False

            line = next_line

        netlist_file.close()
        return netlist

    def read(
        self,
        path: str,
        data=None,
        key=None,
        implicit_top_cell_name: Optional[str] = None,
    ):
        """Parse one file or a directory of netlist files.

        Parameters
        ----------
        path:
            Path to a netlist file or a directory.
        data:
            Controls what is returned:

            * ``None`` — return a :class:`Netlist` object (single file only)
            * ``'cells'`` — return ``Set[str]`` of cell names
            * ``'ports'`` — return ``Dict[str, List[str]]``
            * ``'devices'`` — return ``Dict[str, Set[str]]``
            * ``'device-params'`` — return ``Dict[str, Dict]``
            * ``'resistors'`` — return ``Dict[str, List]``
            * ``'capacitors'`` — return ``Dict[str, List]``
        key:
            Reserved for future use.

        Raises
        ------
        NetlistError
            If a file cannot be found or opened.
        """
        output: Union[Set, Dict] = set() if data == "cells" else {}

        cell_names: Set[str] = set()
        device_names: Set[str] = set()

        # Collect files
        netlist_files: List[str] = []
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path, topdown=False):
                for file_name in files:
                    ext = os.path.splitext(file_name)[1].lower()
                    if ext in ALLOWED_EXTENSIONS:
                        netlist_files.append(os.path.join(root, file_name))
        else:
            netlist_files = [path]

        last_filename = path
        for filename in netlist_files:
            last_filename = filename
            netlist = self.parse(filename, data, implicit_top_cell_name)

            all_cells = list(netlist.cells)
            if implicit_top_cell_name and netlist.implicit_top_cell:
                all_cells.append(netlist.implicit_top_cell)

            if not self.internal:
                cell_names.update(c.name for c in all_cells)
                for cell in all_cells:
                    for inst in cell.instances:
                        if inst.device_name:
                            device_names.add(inst.device_name)

            if data == "cells":
                assert isinstance(output, set)
                output.update(c.name for c in all_cells)

            elif data == "ports":
                assert isinstance(output, dict)
                for cell in all_cells:
                    output.setdefault(cell.name, []).extend(cell.ports)

            elif data == "devices":
                assert isinstance(output, dict)
                for cell in all_cells:
                    output[cell.name] = set()
                    for inst in cell.instances:
                        if inst.device_name:
                            output[cell.name].add(inst.device_name)

            elif data == "device-params":
                assert isinstance(output, dict)
                for cell in all_cells:
                    output[cell.name] = {}
                    for inst in cell.instances:
                        if inst.device_name:
                            output[cell.name].setdefault(inst.device_name, {})
                            output[cell.name][inst.device_name][inst.name] = dict(
                                inst.parameters
                            )
                            output[cell.name][inst.device_name][inst.name][
                                "nodes"
                            ] = inst.nodes

            elif data == "resistors":
                assert isinstance(output, dict)
                for cell in all_cells:
                    output[cell.name] = []
                    for inst in cell.instances:
                        if inst.code == "r":
                            output[cell.name].append(
                                [inst.name, inst.nodes, inst.number, inst.parameters]
                            )

            elif data == "capacitors":
                assert isinstance(output, dict)
                for cell in all_cells:
                    output[cell.name] = []
                    for inst in cell.instances:
                        if inst.code == "c":
                            output[cell.name].append([inst.name, inst.number])

            elif data == "resistance":
                assert isinstance(output, dict)
                for cell in all_cells:
                    output[cell.name] = netlist.resistance

            elif data == "capacitance":
                assert isinstance(output, dict)
                for cell in all_cells:
                    output[cell.name] = netlist.capacitance

            elif data is None:
                return netlist

        # Filter internal cells when self.internal is False
        if not self.internal:
            internal_cells = cell_names.intersection(device_names)
            if implicit_top_cell_name:
                internal_cells.discard(implicit_top_cell_name)
            if internal_cells:
                warning(
                    f"Warning: Device(s) {', '.join(sorted(internal_cells))} "
                    f"defined in an internal subckt in {last_filename}."
                )
                if data == "cells":
                    assert isinstance(output, set)
                    output = output.difference(internal_cells)
                elif data == "devices":
                    assert isinstance(output, dict)
                    for cell_name in list(output.keys()):
                        if cell_name in internal_cells:
                            del output[cell_name]
                        else:
                            output[cell_name] = {
                                d for d in output[cell_name]
                                if d not in internal_cells
                            }
                else:
                    assert isinstance(output, dict)
                    for cell_name in internal_cells:
                        output.pop(cell_name, None)

        return output

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _instance_parse(self, line: str, netlist_version: str, cell: NetlistCell):
        """Parse one device-instance line and append to the given cell."""
        tokens = line.split()
        instance = DeviceInstance(tokens[0])

        # CDL capacitors, diodes, resistors: device token is at position 3 (or 4)
        if netlist_version == "cdl" and instance.code in {"c", "r", "d"}:
            i = 3
            if len(tokens) > 3 and tokens[i].startswith("$SUB="):
                i += 1

        # All other cases: scan backwards to find device/number token
        else:
            i = 2  # safe fallback
            for idx in range(len(tokens) - 1, 1, -1):
                # Spectre: strip "capacitor _="/"resistor _=" prefix
                if netlist_version == "scs" and instance.code in {"c", "r"}:
                    if tokens[idx - 1] in {"capacitor", "resistor"}:
                        tokens[idx] = tokens[idx].split("=", 1)[-1]
                        del tokens[idx - 1]
                        i = idx - 1
                        break
                if "=" not in tokens[idx] and "=" not in tokens[idx - 1]:
                    i = idx
                    break

        # Nodes are everything between instance name and device/number token
        instance.nodes = tokens[1:i]

        # Parameters follow the device/number token
        for token in tokens[i + 1:]:
            if "=" in token:
                param, value = token.split("=", 1)
                instance.parameters[param] = value

        # Decide whether token[i] is a number or a device name
        if i < len(tokens):
            tok = tokens[i]
            if instance.code in {"c", "r"} and re.match(r"^\d+(\.\S*)?", tok):
                instance.number = tok
            elif tok != "vsource" and "=" not in tok and tok not in cell.substitute:
                if netlist_version == "cdl" and "$" in tok and "[" in tok:
                    instance.device_name = tok.split("[", 1)[1].rstrip("]").lower()
                else:
                    instance.device_name = tok.lower()

        cell.instances.append(instance)

    # ------------------------------------------------------------------
    # SPF parasitic data helpers (ported from original)
    # ------------------------------------------------------------------

    def _process_spf_capacitance(
        self, netlist: Netlist, con1: str, con2: str, capacitance_val: str
    ) -> None:
        """Store SPF capacitance annotation into netlist.capacitance."""
        if ":" not in con1 and con2 == "ground":
            if con1 in netlist.capacitance:
                con1_interface = netlist.capacitance[con1].get("main_interface", "")
                netlist.capacitance[con1].setdefault(con2, {})
                netlist.capacitance[con1][con2].setdefault("total", []).append(capacitance_val)
                if con1_interface:
                    netlist.capacitance[con1][con2].setdefault(con1_interface, []).append(
                        capacitance_val
                    )
        elif ":" in con1 and con2 == "ground":
            base_con1 = re.sub(r":\d+", "", con1)
            if base_con1 in netlist.capacitance:
                con1_interface = netlist.capacitance[base_con1].get("main_interface", "")
                netlist.capacitance[base_con1].setdefault(con2, {})
                netlist.capacitance[base_con1][con2].setdefault("total", []).append(
                    capacitance_val
                )
                if con1_interface:
                    netlist.capacitance[base_con1][con2].setdefault(
                        con1_interface, []
                    ).append(capacitance_val)
        elif con1 in netlist.capacitance and ":" not in con2:
            if con2 in netlist.capacitance:
                con1_interface = netlist.capacitance[con1].get("main_interface", "")
                con2_interface = netlist.capacitance[con2].get("main_interface", "")
                netlist.capacitance[con1].setdefault(con2, {})
                netlist.capacitance[con2].setdefault(con1, {})
                netlist.capacitance[con1][con2].setdefault("total", []).append(capacitance_val)
                net_net = (
                    f"{con1_interface}-{con2_interface}"
                    if con1_interface != con2_interface
                    else con1_interface
                )
                if net_net:
                    netlist.capacitance[con1][con2].setdefault(net_net, []).append(
                        capacitance_val
                    )

    def _process_spf_resistance(
        self, netlist: Netlist, con1: str, con2: str, resistance_val: str
    ) -> None:
        """Store SPF resistance annotation into netlist.resistance."""
        main_port = re.sub(r":\d+", "", con1)
        if con1 in netlist.resistance:
            main_interface = netlist.resistance[con1].get("main_interface", "")
            if main_interface:
                netlist.resistance[con1].setdefault(main_interface, []).append(resistance_val)
        elif con2 in netlist.resistance:
            main_interface = netlist.resistance[con2].get("main_interface", "")
            if main_interface:
                netlist.resistance[con2].setdefault(main_interface, []).append(resistance_val)
        elif re.search(r":\d+", con1) and main_port in netlist.resistance:
            res = netlist.resistance[main_port]
            con1_interface = res.get("ports", {}).get(con1, "")
            con2_interface = res.get("ports", {}).get(con2, "")
            if con1_interface and con1_interface == con2_interface:
                res.setdefault(con1_interface, []).append(resistance_val)
            elif con1_interface and con2_interface:
                net_net = f"{con1_interface}-{con2_interface}"
                res.setdefault(net_net, []).append(resistance_val)
                if net_net not in res.get("sub_interfaces", []):
                    res.setdefault("sub_interfaces", []).append(net_net)
