"""
NLP Parser Module
=================

LangGraph-based orchestration framework for parsing PM inputs into structured task decompositions.

Main Components:
- langgraph-setup: Core orchestration framework
- test_langgraph: Comprehensive test suite

Usage:
    from phase1_nlp.parser.langgraph_setup import execute_parser_workflow

    result = execute_parser_workflow("Create a login system")
    print(f"Status: {result['status']}")
"""

__version__ = "0.1.0"
__author__ = "Backend Engineer - Phase 1 Week 1"

# Make key functions available at package level
try:
    from .langgraph_setup import (
        execute_parser_workflow,
        create_parser_graph,
        ParserState
    )

    __all__ = [
        'execute_parser_workflow',
        'create_parser_graph',
        'ParserState'
    ]
except ImportError:
    # Allow module to load even if dependencies aren't installed yet
    __all__ = []
