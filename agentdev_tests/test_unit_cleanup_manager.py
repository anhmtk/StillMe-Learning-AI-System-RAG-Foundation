#!/usr/bin/env python3
"""
Unit tests for Cleanup Manager Module
Tests cleanup detection and optimization capabilities
"""

import os
import shutil
import tempfile

import pytest

# Import AgentDev modules
from agent_dev.core.cleanup_manager import (
    CleanupManager,
    CleanupOpportunity,
    CleanupType,
)


class TestCleanupManager:
    """Test cases for Cleanup Manager Module"""

    def setup_method(self):
        """Set up test fixtures"""
        self.cleanup_manager = CleanupManager()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_cleanup_manager_initialization(self):
        """Test CleanupManager initialization"""
        assert self.cleanup_manager is not None
        assert hasattr(self.cleanup_manager, "analyze_cleanup_opportunities")
        assert hasattr(self.cleanup_manager, "detect_temp_files")
        assert hasattr(self.cleanup_manager, "detect_dead_code")
        assert hasattr(self.cleanup_manager, "detect_duplicates")

    @pytest.mark.unit
    def test_temp_file_detection(self):
        """Test temporary file detection"""
        # Create test files
        test_files = [
            "temp_file.tmp",
            "backup_file.bak",
            "cache_file.cache",
            "log_file.log",
            "normal_file.py",
        ]

        for filename in test_files:
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, "w") as f:
                f.write("test content")

        # Analyze cleanup opportunities
        cleanup_result = self.cleanup_manager.analyze_cleanup_opportunities(
            self.temp_dir
        )

        assert isinstance(cleanup_result, list)
        assert len(cleanup_result) > 0

        # Should detect temp files
        temp_files = [
            item
            for item in cleanup_result
            if item.cleanup_type == CleanupType.TEMP_FILES
        ]
        assert len(temp_files) > 0

        # Should not detect normal files
        normal_files = [
            item
            for item in cleanup_result
            if item.cleanup_type == CleanupType.TEMP_FILES
            and "normal_file.py" in item.file_path
        ]
        assert len(normal_files) == 0

    @pytest.mark.unit
    def test_dead_code_detection(self):
        """Test dead code detection"""
        # Create Python file with dead code
        dead_code_file = os.path.join(self.temp_dir, "dead_code.py")
        with open(dead_code_file, "w") as f:
            f.write("""
def used_function():
    return "used"

def unused_function():
    return "unused"

def another_unused_function():
    return "also unused"

class UsedClass:
    def method(self):
        return "used method"

class UnusedClass:
    def method(self):
        return "unused method"

# This function is never called
def never_called_function():
    return "never called"

if __name__ == "__main__":
    used_function()
    obj = UsedClass()
    obj.method()
""")

        # Analyze for dead code
        cleanup_result = self.cleanup_manager.analyze_cleanup_opportunities(
            self.temp_dir
        )

        # Should detect dead code
        dead_code_items = [
            item
            for item in cleanup_result
            if item.cleanup_type == CleanupType.DEAD_CODE
        ]
        assert len(dead_code_items) > 0

        # Should identify unused functions
        dead_code_text = " ".join([item.description for item in dead_code_items])
        assert "unused" in dead_code_text.lower()

    @pytest.mark.unit
    def test_duplicate_detection(self):
        """Test duplicate code detection"""
        # Create files with duplicate code
        file1_path = os.path.join(self.temp_dir, "file1.py")
        file2_path = os.path.join(self.temp_dir, "file2.py")

        duplicate_code = """
def calculate_sum(a, b):
    return a + b

def calculate_product(a, b):
    return a * b
"""

        with open(file1_path, "w") as f:
            f.write(duplicate_code)

        with open(file2_path, "w") as f:
            f.write(duplicate_code)

        # Analyze for duplicates
        cleanup_result = self.cleanup_manager.analyze_cleanup_opportunities(
            self.temp_dir
        )

        # Should detect duplicates
        duplicate_items = [
            item
            for item in cleanup_result
            if item.cleanup_type == CleanupType.DUPLICATES
        ]
        assert len(duplicate_items) > 0

        # Should identify duplicate files
        duplicate_text = " ".join([item.description for item in duplicate_items])
        assert "duplicate" in duplicate_text.lower()

    @pytest.mark.unit
    def test_cache_cleanup_detection(self):
        """Test cache cleanup detection"""
        # Create cache files
        cache_files = [
            "__pycache__/module.cpython-39.pyc",
            "cache/data.cache",
            ".cache/session.cache",
            "node_modules/.cache/build.cache",
        ]

        for cache_file in cache_files:
            cache_path = os.path.join(self.temp_dir, cache_file)
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, "w") as f:
                f.write("cache content")

        # Analyze for cache cleanup
        cleanup_result = self.cleanup_manager.analyze_cleanup_opportunities(
            self.temp_dir
        )

        # Should detect cache files
        cache_items = [
            item
            for item in cleanup_result
            if item.cleanup_type == CleanupType.CACHE_CLEANUP
        ]
        assert len(cache_items) > 0

        # Should identify cache files
        cache_text = " ".join([item.description for item in cache_items])
        assert "cache" in cache_text.lower()

    @pytest.mark.unit
    def test_resource_optimization_detection(self):
        """Test resource optimization detection"""
        # Create large files that could be optimized
        large_file = os.path.join(self.temp_dir, "large_file.txt")
        with open(large_file, "w") as f:
            f.write("x" * 1000000)  # 1MB file

        # Create inefficient code
        inefficient_code = os.path.join(self.temp_dir, "inefficient.py")
        with open(inefficient_code, "w") as f:
            f.write("""
# Inefficient code with O(n²) complexity
def inefficient_sort(data):
    for i in range(len(data)):
        for j in range(len(data)):
            if data[i] > data[j]:
                data[i], data[j] = data[j], data[i]
    return data

# Unused imports
import os
import sys
import json
import xml
import csv
import sqlite3
import requests
import numpy
import pandas
import matplotlib
import seaborn
import sklearn
import tensorflow
import torch
import opencv
import pillow
import flask
import django
import fastapi
import sqlalchemy
import alembic
import pytest
import black
import flake8
import mypy
import isort
import bandit
import safety
import pipenv
import poetry
import conda
import docker
import kubernetes
import terraform
import ansible
import jenkins
import gitlab
import github
import bitbucket
import jira
import confluence
import slack
import discord
import telegram
import whatsapp
import zoom
import teams
import meet
import webex
import skype
import hangouts
import messenger
import instagram
import facebook
import twitter
import linkedin
import youtube
import tiktok
import snapchat
import pinterest
import reddit
import quora
import stackoverflow
import medium
import deviantart
import behance
import dribbble
import figma
import sketch
import adobe
import canva
import notion
import trello
import asana
import monday
import wrike
import smartsheet
import airtable
import zapier
import ifttt
import integromat
import n8n
import bubble
import webflow
import squarespace
import wix
import shopify
import woocommerce
import magento
import prestashop
import opencart
import bigcommerce
import squarespace
import wix
import shopify
import woocommerce
import magento
import prestashop
import opencart
import bigcommerce
""")

        # Analyze for resource optimization
        cleanup_result = self.cleanup_manager.analyze_cleanup_opportunities(
            self.temp_dir
        )

        # Should detect resource optimization opportunities
        optimization_items = [
            item
            for item in cleanup_result
            if item.cleanup_type == CleanupType.RESOURCE_OPTIMIZATION
        ]
        assert len(optimization_items) > 0

        # Should identify large files and inefficient code
        optimization_text = " ".join([item.description for item in optimization_items])
        assert (
            "large" in optimization_text.lower()
            or "inefficient" in optimization_text.lower()
        )

    @pytest.mark.unit
    def test_cleanup_opportunity_creation(self):
        """Test CleanupOpportunity creation"""
        opportunity = CleanupOpportunity(
            file_path="/path/to/file.py",
            cleanup_type=CleanupType.DEAD_CODE,
            description="Unused function detected",
            potential_savings=1024,
            confidence=0.8,
        )

        assert opportunity.file_path == "/path/to/file.py"
        assert opportunity.cleanup_type == CleanupType.DEAD_CODE
        assert opportunity.description == "Unused function detected"
        assert opportunity.potential_savings == 1024
        assert opportunity.confidence == 0.8

    @pytest.mark.unit
    def test_cleanup_manager_performance(self):
        """Test cleanup manager performance"""
        import time

        # Create large directory structure
        for i in range(1000):
            file_path = os.path.join(self.temp_dir, f"file_{i}.py")
            with open(file_path, "w") as f:
                f.write(f"# File {i}\ndef function_{i}():\n    return {i}")

        start_time = time.time()
        cleanup_result = self.cleanup_manager.analyze_cleanup_opportunities(
            self.temp_dir
        )
        end_time = time.time()

        # Should complete within reasonable time
        assert (end_time - start_time) < 5.0  # Less than 5 seconds
        assert len(cleanup_result) > 0

    @pytest.mark.unit
    def test_empty_directory_handling(self):
        """Test handling of empty directory"""
        empty_dir = os.path.join(self.temp_dir, "empty")
        os.makedirs(empty_dir)

        cleanup_result = self.cleanup_manager.analyze_cleanup_opportunities(empty_dir)

        # Should handle empty directory gracefully
        assert isinstance(cleanup_result, list)
        assert len(cleanup_result) == 0

    @pytest.mark.unit
    def test_cleanup_manager_deterministic(self):
        """Test that cleanup manager is deterministic"""
        # Create test files
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, "w") as f:
            f.write("def unused_function():\n    return 'unused'")

        # Run analysis multiple times
        result1 = self.cleanup_manager.analyze_cleanup_opportunities(self.temp_dir)
        result2 = self.cleanup_manager.analyze_cleanup_opportunities(self.temp_dir)

        # Results should be identical
        assert len(result1) == len(result2)
        for item1, item2 in zip(result1, result2, strict=False):
            assert item1.file_path == item2.file_path
            assert item1.cleanup_type == item2.cleanup_type
            assert item1.description == item2.description

    @pytest.mark.unit
    def test_cleanup_manager_edge_cases(self):
        """Test edge cases for cleanup manager"""
        # Test with non-existent directory
        with pytest.raises((FileNotFoundError, OSError)):
            self.cleanup_manager.analyze_cleanup_opportunities("/non/existent/path")

        # Test with file instead of directory
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")

        with pytest.raises((NotADirectoryError, OSError)):
            self.cleanup_manager.analyze_cleanup_opportunities(test_file)


# ko dùng # type: ignore và ko dùng comment out để che giấu lỗi
