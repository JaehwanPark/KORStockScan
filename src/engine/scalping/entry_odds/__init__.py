"""Offline entry-odds observation package.

This package deliberately has no import edge into the live scalping runtime.
It consumes immutable AI traces, mature outcome labels, and separately
produced raw odds to create counterfactual-only calibration evidence.
"""
